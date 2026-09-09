"""
Welele Media™ — Pillar 4: Cloud Storage & Ingestion Router
Direct Presigned Upload URL generation for S3 / Cloudflare R2 / Supabase Storage
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.storage_service import storage_service

router = APIRouter(prefix="/storage", tags=["Cloud Storage & Video Delivery (Pillar 4)"])

class PresignedUploadRequest(BaseModel):
    story_id: str
    episode_number: int
    filename: str
    content_type: Optional[str] = "video/mp4"

class PresignedUploadResponse(BaseModel):
    upload_url: str
    storage_key: str
    public_cdn_url: str
    provider: str
    bucket: str
    expires_in_seconds: int
    max_file_size_bytes: int
    required_headers: Dict[str, str]

class HlsRendition(BaseModel):
    name: str
    resolution: str
    bitrate_kbps: int
    fps: int
    url: str

class RenditionsResponse(BaseModel):
    master_playlist_url: str
    aspect_ratio: str
    renditions: List[HlsRendition]

@router.post("/presigned-upload-url", response_model=PresignedUploadResponse)
def get_presigned_upload_url(req: PresignedUploadRequest):
    """
    Generates an authorized pre-signed upload URL for direct S3/R2 video asset ingestion.
    """
    try:
        result = storage_service.generate_presigned_upload_url(
            story_id=req.story_id,
            episode_number=req.episode_number,
            filename=req.filename,
            content_type=req.content_type or "video/mp4"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/presigned-upload")
def get_presigned_upload_alias(req: PresignedUploadRequest):
    """
    Backward-compatibility alias matching Pillar 4 architecture specs.
    """
    try:
        res = storage_service.generate_presigned_upload_url(
            story_id=req.story_id,
            episode_number=req.episode_number,
            filename=req.filename,
            content_type=req.content_type or "video/mp4"
        )
        return {"upload": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/renditions", response_model=RenditionsResponse)
def get_hls_renditions(storage_key: str):
    """
    Returns the HLS multi-bitrate adaptive streaming manifest and rendition URLs.
    """
    return storage_service.get_hls_renditions(storage_key)
