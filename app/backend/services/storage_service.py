"""
Welele Media™ — Pillar 4: Object Storage & CDN Video Delivery Service
Architecture Rule: The database never stores video binaries.
This service handles CDN URL resolution, HLS adaptive streaming packaging,
and pre-signed upload URLs for Cloudflare R2 / AWS S3 / Supabase Storage.
"""

import os
import sys
import uuid
import json
from typing import Dict, Any, List, Optional

# Ensure parent directory is in sys.path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import settings
except ImportError:
    class MockSettings:
        PROJECT_NAME = "Welele™ Media Backend"
    settings = MockSettings()

try:
    import boto3
    from botocore.config import Config
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class StorageService:
    def __init__(self):
        self.account_id = os.getenv("R2_ACCOUNT_ID") or ""
        self.access_key = os.getenv("R2_ACCESS_KEY_ID") or ""
        self.secret_key = os.getenv("R2_SECRET_ACCESS_KEY") or ""
        self.storage_bucket = os.getenv("R2_BUCKET_NAME") or os.getenv("STORAGE_BUCKET", "welele-vod-masters")
        self.cdn_base_url = os.getenv("CDN_BASE_URL", "https://cdn.welele.media").rstrip("/")
        self.supported_formats = ["video/mp4", "video/quicktime", "application/x-mpegURL"]

        # Initialize boto3 S3/R2 client if credentials exist
        self.s3_client = None
        if HAS_BOTO3 and self.account_id and self.access_key and self.secret_key:
            try:
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    config=Config(signature_version='s3v4'),
                    region_name='auto'
                )
                print(f"[StorageService] Connected to Cloudflare R2 bucket '{self.storage_bucket}' successfully.")
            except Exception as e:
                print(f"[StorageService] Failed to initialize live R2 client: {e}")

    def get_stream_url(self, video_path_or_url: str, adaptive_hls: bool = True) -> str:
        """
        Resolves asset path to edge CDN URL with optional HLS adaptive bitrate manifest (.m3u8).
        """
        if video_path_or_url.startswith("http://") or video_path_or_url.startswith("https://"):
            return video_path_or_url

        clean_path = video_path_or_url.lstrip("/")
        if adaptive_hls and not clean_path.endswith(".m3u8"):
            base_name = clean_path.rsplit(".", 1)[0]
            clean_path = f"{base_name}/master.m3u8"

        return f"{self.cdn_base_url}/{clean_path}"

    def generate_presigned_upload_url(
        self,
        story_id: str,
        episode_number: int,
        filename: str,
        content_type: str = "video/mp4",
        expires_in_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Generates a direct pre-signed upload URL for Cloudflare R2 / S3.
        """
        extension = filename.rsplit(".", 1)[-1] if "." in filename else "mp4"
        clean_ext = f".{extension}"
        storage_key = f"masters/{story_id}/ep_{episode_number:03d}_{uuid.uuid4().hex[:8]}{clean_ext}"

        # 1. Live Cloudflare R2 Presigned URL
        if self.s3_client:
            try:
                presigned_url = self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': self.storage_bucket,
                        'Key': storage_key,
                        'ContentType': content_type
                    },
                    ExpiresIn=expires_in_seconds
                )
                public_cdn_url = f"{self.cdn_base_url}/{storage_key}"
                return {
                    "upload_url": presigned_url,
                    "storage_key": storage_key,
                    "public_cdn_url": public_cdn_url,
                    "provider": "Cloudflare R2 Storage (Direct Ingestion)",
                    "bucket": self.storage_bucket,
                    "expires_in_seconds": expires_in_seconds,
                    "max_file_size_bytes": 500 * 1024 * 1024,
                    "required_headers": {
                        "Content-Type": content_type
                    }
                }
            except Exception as e:
                print(f"[StorageService] Failed generating live R2 presigned URL: {e}")

        # 2. Simulation / Fallback Presigned Ticket
        public_cdn_url = f"{self.cdn_base_url}/{storage_key}"
        return {
            "upload_url": f"{self.cdn_base_url}/upload/{storage_key}?ticket={uuid.uuid4().hex}",
            "storage_key": storage_key,
            "public_cdn_url": public_cdn_url,
            "provider": "Cloudflare R2 Local Dispatcher",
            "bucket": self.storage_bucket,
            "expires_in_seconds": expires_in_seconds,
            "max_file_size_bytes": 500 * 1024 * 1024,
            "required_headers": {
                "Content-Type": content_type
            }
        }

    def generate_adaptive_renditions(self, video_path_or_url: str) -> List[Dict[str, Any]]:
        """
        Generates multi-bitrate rendition specifications for vertical microdramas.
        """
        base_clean = video_path_or_url.replace(".mp4", "").replace(".m3u8", "")
        return [
            {
                "resolution": "1080x1920",
                "label": "1080p (Full HD Vertical)",
                "bitrate": "4.5 Mbps",
                "stream_url": f"{base_clean}_1080p.m3u8"
            },
            {
                "resolution": "720x1280",
                "label": "720p (HD Mobile)",
                "bitrate": "2.2 Mbps",
                "stream_url": f"{base_clean}_720p.m3u8"
            },
            {
                "resolution": "480x854",
                "label": "480p (Data Saver 3G/4G)",
                "bitrate": "800 kbps",
                "stream_url": f"{base_clean}_480p.m3u8"
            }
        ]

    def get_hls_renditions(self, storage_key: str) -> Dict[str, Any]:
        """
        Returns the HLS multi-bitrate adaptive streaming manifest and rendition URLs.
        """
        base_url = f"{self.cdn_base_url}/{storage_key.rsplit('.', 1)[0]}"
        return {
            "master_playlist_url": f"{base_url}/master.m3u8",
            "aspect_ratio": "9:16",
            "renditions": [
                {
                    "name": "1080p_high",
                    "resolution": "1080x1920",
                    "bitrate_kbps": 4500,
                    "fps": 30,
                    "url": f"{base_url}/1080p/index.m3u8"
                },
                {
                    "name": "720p_medium",
                    "resolution": "720x1280",
                    "bitrate_kbps": 2200,
                    "fps": 30,
                    "url": f"{base_url}/720p/index.m3u8"
                },
                {
                    "name": "480p_data_saver",
                    "resolution": "480x854",
                    "bitrate_kbps": 800,
                    "fps": 30,
                    "url": f"{base_url}/480p/index.m3u8"
                }
            ]
        }


storage_service = StorageService()
