"""
Welele Media™ — Pillar 4: Cloud Storage & Ingestion Router
Direct Presigned Upload URL generation for S3 / Cloudflare R2 / Supabase Storage
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from services.storage_service import storage_service

router = APIRouter(prefix="/storage", tags=["Cloud Storage & Video Delivery (Pillar 4)"])

class BinaryUploadResponse(BaseModel):
    success: bool
    storage_key: str
    public_cdn_url: str
    file_size_bytes: int
    content_type: str
    provider: str

@router.post("/upload-binary", response_model=BinaryUploadResponse)
async def upload_binary_master(
    file: UploadFile = File(...),
    series_id: str = Form(...),
    episode_id: Optional[str] = Form(None),
    episode_number: Optional[int] = Form(None)
):
    """
    Direct binary ingestion endpoint: Uploads video file bytes to object storage.
    Returns authoritative storage_key and public_cdn_url.
    """
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty video file payload")
        
        result = storage_service.save_binary_master(
            file_bytes=contents,
            story_id=series_id,
            episode_id=episode_id,
            episode_number=episode_number,
            filename=file.filename or "master.mp4",
            content_type=file.content_type or "video/mp4"
        )
        return {
            "success": True,
            "storage_key": result["storage_key"],
            "public_cdn_url": result["public_cdn_url"],
            "file_size_bytes": result["file_size_bytes"],
            "content_type": result["content_type"],
            "provider": result["provider"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

class DispatchJobRequest(BaseModel):
    media_asset_id: str
    provider: Optional[str] = "CloudflareStream"
    idempotency_key: Optional[str] = None

@router.post("/jobs/transcode")
def dispatch_media_job(req: DispatchJobRequest):
    """Dispatches an asynchronous media transcoding job outside the request thread."""
    from services.transcoding_service import transcoding_service
    job = transcoding_service.dispatch_transcoding_job(
        media_asset_id=req.media_asset_id,
        provider=req.provider or "CloudflareStream",
        idempotency_key=req.idempotency_key
    )
    return {"status": "accepted", "job": job}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Returns the operational execution status of a media job."""
    from services.transcoding_service import transcoding_service
    job = transcoding_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Media job not found")
    return {"job": job}

@router.get("/assets/{asset_id}/renditions")
def get_asset_renditions(asset_id: str):
    """Returns all generated HLS renditions for a media asset."""
    from services.transcoding_service import transcoding_service
    renditions = transcoding_service.get_asset_renditions(asset_id)
    return {"asset_id": asset_id, "renditions": renditions}

