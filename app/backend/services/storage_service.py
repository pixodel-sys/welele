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
        self.account_id = os.getenv("R2_ACCOUNT_ID") or getattr(settings, "R2_ACCOUNT_ID", None) or ""
        self.access_key = os.getenv("R2_ACCESS_KEY_ID") or getattr(settings, "R2_ACCESS_KEY_ID", None) or ""
        self.secret_key = os.getenv("R2_SECRET_ACCESS_KEY") or getattr(settings, "R2_SECRET_ACCESS_KEY", None) or ""
        self.storage_bucket = os.getenv("R2_BUCKET_NAME") or os.getenv("STORAGE_BUCKET") or getattr(settings, "R2_BUCKET_NAME", None) or getattr(settings, "STORAGE_BUCKET", None) or ("welele-vod-staging" if getattr(settings, "ENVIRONMENT", "") == "staging" else "welele-vod-masters")
        self.cdn_base_url = (os.getenv("CDN_BASE_URL") or getattr(settings, "CDN_BASE_URL", None) or "https://cdn.welele.media").rstrip("/")
        self.supported_formats = ["video/mp4", "video/quicktime", "application/x-mpegURL"]

        # Local physical disk backing for local dev & object verification
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.local_storage_dir = os.path.join(backend_dir, "media_storage")
        os.makedirs(self.local_storage_dir, exist_ok=True)

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

    def save_binary_master(
        self,
        file_bytes: bytes,
        story_id: str,
        episode_id: Optional[str] = None,
        episode_number: Optional[int] = None,
        filename: str = "master.mp4",
        content_type: str = "video/mp4"
    ) -> Dict[str, Any]:
        """
        Ingests real binary video payload into object storage (Cloudflare R2).
        Fails closed in staging/production if durable R2 storage is unavailable.
        Returns the authoritative storage_key and signed stream delivery URL.
        """
        if not file_bytes:
            raise ValueError("Cannot ingest empty binary payload into object storage.")

        ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp4"
        clean_ext = f".{ext}"
        
        if episode_id:
            storage_key = f"masters/{story_id}/{episode_id}{clean_ext}"
        elif episode_number is not None:
            storage_key = f"masters/{story_id}/ep_{episode_number:03d}_{uuid.uuid4().hex[:6]}{clean_ext}"
        else:
            storage_key = f"masters/{story_id}/master_{uuid.uuid4().hex[:8]}{clean_ext}"

        # 1. Authoritative Cloudflare R2 Durable Storage
        provider = "Local Object Storage"
        if getattr(settings, "IS_PRODUCTION_OR_STAGING", False):
            if not self.s3_client:
                raise RuntimeError(
                    f"CRITICAL STORAGE HALT: Cloudflare R2 client is uninitialized in {getattr(settings, 'ENVIRONMENT', 'unknown')}. "
                    "Ephemeral Railway disk storage is strictly prohibited for durable media in staging/production."
                )
            try:
                self.s3_client.put_object(
                    Bucket=self.storage_bucket,
                    Key=storage_key,
                    Body=file_bytes,
                    ContentType=content_type
                )
                provider = f"Cloudflare R2 Storage ({self.storage_bucket})"
            except Exception as e:
                raise RuntimeError(
                    f"CRITICAL STORAGE HALT: Failed writing durable object to R2 bucket '{self.storage_bucket}' (key: '{storage_key}'): {e}"
                )
        elif self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=self.storage_bucket,
                    Key=storage_key,
                    Body=file_bytes,
                    ContentType=content_type
                )
                provider = f"Cloudflare R2 Storage ({self.storage_bucket})"
            except Exception as e:
                print(f"[StorageService:Dev] Failed writing to R2 bucket: {e}")

        # 2. Local disk backing (dev verification only)
        local_target_path = os.path.join(self.local_storage_dir, *storage_key.split("/"))
        try:
            os.makedirs(os.path.dirname(local_target_path), exist_ok=True)
            with open(local_target_path, "wb") as f:
                f.write(file_bytes)
        except Exception:
            pass

        # 3. Generate delivery URL (signed presigned URL if R2 available)
        if self.s3_client:
            try:
                presigned = self.generate_presigned_download_url(storage_key, expires_in_seconds=3600)
                stream_url = presigned["download_url"]
            except Exception:
                stream_url = self.get_stream_url(storage_key, adaptive_hls=False)
        else:
            stream_url = self.get_stream_url(storage_key, adaptive_hls=False)

        return {
            "storage_key": storage_key,
            "public_cdn_url": stream_url,
            "file_size_bytes": len(file_bytes),
            "content_type": content_type,
            "provider": provider,
            "local_path": local_target_path
        }

    @staticmethod
    def _clean_key(storage_key: str) -> str:
        k = (storage_key or "").strip().lstrip("/")
        if k.startswith("media/"):
            k = k[6:]
        return k

    def object_exists(self, storage_key: str) -> bool:
        """
        Verifies whether an object exists durably in Cloudflare R2.
        """
        if not storage_key or storage_key.startswith("blob:"):
            return False
        clean_key = self._clean_key(storage_key)
        if self.s3_client:
            try:
                self.s3_client.head_object(Bucket=self.storage_bucket, Key=clean_key)
                return True
            except Exception:
                return False
        if not getattr(settings, "IS_PRODUCTION_OR_STAGING", False):
            local_target_path = os.path.join(self.local_storage_dir, *clean_key.split("/"))
            return os.path.exists(local_target_path) and os.path.isfile(local_target_path)
        return False

    def get_stored_binary(self, storage_key: str) -> Optional[bytes]:
        """
        Retrieves actual binary bytes from storage for integrity & playback verification.
        In staging/production, retrieval is strictly from Cloudflare R2.
        """
        if not storage_key or storage_key.startswith("blob:"):
            raise ValueError(f"Cannot retrieve binary from ephemeral browser blob reference: {storage_key}")

        clean_key = self._clean_key(storage_key)

        # 1. Authoritative check: Cloudflare R2
        if self.s3_client:
            try:
                response = self.s3_client.get_object(Bucket=self.storage_bucket, Key=clean_key)
                return response['Body'].read()
            except Exception as e:
                if getattr(settings, "IS_PRODUCTION_OR_STAGING", False):
                    return None

        # 2. Local disk fallback permitted ONLY in local development
        if not getattr(settings, "IS_PRODUCTION_OR_STAGING", False):
            local_target_path = os.path.join(self.local_storage_dir, *clean_key.split("/"))
            if os.path.exists(local_target_path) and os.path.isfile(local_target_path):
                with open(local_target_path, "rb") as f:
                    return f.read()

        return None

    def get_stream_url(self, video_path_or_url: str, adaptive_hls: bool = True) -> str:
        """
        Resolves asset path or storage_key to edge CDN URL or streamable route.
        Strict invariant: Rejects browser blob: references.
        """
        if not video_path_or_url:
            return "/videos/welele_placeholder.mp4"

        if video_path_or_url.startswith("blob:"):
            raise ValueError(
                f"Invalid media reference: Cannot resolve ephemeral browser blob URL '{video_path_or_url}'. "
                f"A valid storage_key or completed binary upload is required."
            )

        if video_path_or_url.startswith("http://") or video_path_or_url.startswith("https://"):
            return video_path_or_url

        if video_path_or_url.startswith("/videos/"):
            return video_path_or_url

        clean_path = video_path_or_url.lstrip("/")
        if clean_path.startswith("media/"):
            clean_path = clean_path[len("media/"):]

        if adaptive_hls and not clean_path.endswith(".m3u8"):
            base_name = clean_path.rsplit(".", 1)[0]
            clean_path = f"{base_name}/master.m3u8"

        # In local development mode without live R2 credentials, stream from mounted /media endpoint
        if not self.s3_client:
            return f"/media/{clean_path}"

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
        public_cdn_url = self.get_stream_url(storage_key, adaptive_hls=False)
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

    def generate_presigned_download_url(
        self,
        storage_key: str,
        expires_in_seconds: int = 900
    ) -> Dict[str, Any]:
        """
        Generates a secure, time-bounded presigned URL for video playback.
        Strict invariant: Rejects browser blob: references.
        """
        if not storage_key or storage_key.startswith("blob:"):
            raise ValueError(f"Invalid storage key for download signing: '{storage_key}'")

        clean_key = self._clean_key(storage_key)

        # 1. Live Cloudflare R2 Presigned Download URL
        if self.s3_client:
            try:
                presigned_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.storage_bucket,
                        'Key': clean_key
                    },
                    ExpiresIn=expires_in_seconds
                )
                return {
                    "download_url": presigned_url,
                    "storage_key": clean_key,
                    "provider": f"Cloudflare R2 Storage ({self.storage_bucket})",
                    "bucket": self.storage_bucket,
                    "expires_in_seconds": expires_in_seconds
                }
            except Exception as e:
                if getattr(settings, "IS_PRODUCTION_OR_STAGING", False):
                    raise RuntimeError(f"CRITICAL STORAGE HALT: Failed generating R2 presigned download URL for '{clean_key}': {e}")
                print(f"[StorageService:Dev] Failed generating live R2 presigned download URL: {e}")

        if getattr(settings, "IS_PRODUCTION_OR_STAGING", False):
            raise RuntimeError(
                f"CRITICAL STORAGE HALT: Cannot generate secure download URL: Cloudflare R2 client is uninitialized in {getattr(settings, 'ENVIRONMENT', 'unknown')}."
            )

        # 2. Local / Standard Streaming Fallback URL (Local development only)
        stream_url = self.get_stream_url(clean_key, adaptive_hls=False)
        return {
            "download_url": stream_url,
            "storage_key": clean_key,
            "provider": "Welele Local VOD Dispatcher",
            "bucket": self.storage_bucket,
            "expires_in_seconds": expires_in_seconds
        }

    def generate_adaptive_renditions(self, video_path_or_url: str) -> List[Dict[str, Any]]:
        """
        Generates multi-bitrate rendition specifications for vertical microdramas.
        """
        if not video_path_or_url or video_path_or_url.startswith("blob:"):
            return []

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
        if storage_key.startswith("blob:"):
            raise ValueError(f"Invalid storage key: Ephemeral blob URL cannot have HLS renditions.")

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
