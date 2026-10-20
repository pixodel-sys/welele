"""
Welele Media™ — Pillar 4: Cloud Storage & Ingestion Router
Direct Presigned Upload URL generation for S3 / Cloudflare R2 / Supabase Storage
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from services.storage_service import storage_service
from services.rbac_service import require_role

router = APIRouter(prefix="/storage", tags=["Cloud Storage & Video Delivery (Pillar 4)"])

class BinaryUploadResponse(BaseModel):
    success: bool
    storage_key: str
    public_cdn_url: str
    file_size_bytes: int
    content_type: str
    provider: str
    media_asset_id: Optional[str] = None
    is_durable: Optional[bool] = None

@router.post("/upload-binary", response_model=BinaryUploadResponse, dependencies=[Depends(require_role(["creator", "admin"]))])
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
        
        # Attach media asset in authoritative database if episode_id provided
        media_asset_id = None
        if episode_id:
            from repositories.series_repository import series_repository
            media_asset = series_repository.attach_media_asset(
                episode_id=episode_id,
                storage_key=result["storage_key"],
                master_url=result["public_cdn_url"],
                duration_seconds=None
            )
            media_asset_id = media_asset.get("id")

        return {
            "success": True,
            "storage_key": result["storage_key"],
            "public_cdn_url": result["public_cdn_url"],
            "file_size_bytes": result["file_size_bytes"],
            "content_type": result["content_type"],
            "provider": result["provider"],
            "media_asset_id": media_asset_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-artwork", response_model=BinaryUploadResponse, dependencies=[Depends(require_role(["creator", "admin"]))])
async def upload_artwork_asset(
    file: UploadFile = File(...),
    series_id: Optional[str] = Form(None),
    artwork_type: str = Form("poster")
):
    """
    Phase 6J-2R-B: Direct artwork ingestion endpoint.
    Uploads static poster or banner image to durable Cloudflare R2 storage.
    Guarantees that public_cdn_url is a permanent, non-expiring public CDN URL.
    """
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty artwork file payload")

        content_type = file.content_type or "image/jpeg"
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Invalid content type '{content_type}': Artwork must be an image.")

        result = storage_service.save_artwork(
            file_bytes=contents,
            series_id=series_id,
            artwork_type=artwork_type,
            filename=file.filename or "artwork.jpg",
            content_type=content_type
        )

        return {
            "success": True,
            "storage_key": result["storage_key"],
            "public_cdn_url": result["public_cdn_url"],
            "file_size_bytes": result["file_size_bytes"],
            "content_type": result["content_type"],
            "provider": result["provider"],
            "media_asset_id": None,
            "is_durable": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify-asset/{storage_key:path}")
def verify_storage_asset(storage_key: str):
    """Verifies that an object exists durably in Cloudflare R2."""
    exists = storage_service.object_exists(storage_key)
    return {
        "storage_key": storage_key,
        "exists": exists,
        "bucket": storage_service.storage_bucket,
        "provider": f"Cloudflare R2 Storage ({storage_service.storage_bucket})" if storage_service.s3_client else "Local"
    }


PUBLIC_STREAM_ALLOWLIST = {
    "videos/welele_ident_v2.mp4",
    "videos/welele_placeholder.mp4",
    "videos/ocean_waves.mp4",
    "videos/sample_drama.mp4",
    "videos/flower_bloom.mp4",
    "videos/jellyfish.mp4",
    "videos/sintel.mp4",
    "videos/big_buck.mp4",
    "videos/Isibusiso_Ep01_The_Midnight_Sovereign_v1.mp4",
}

@router.get("/stream/{storage_key:path}")
def stream_storage_object(storage_key: str):
    """
    Direct streaming redirect endpoint: Resolves public object storage keys to a secure presigned R2 download URL.
    Protected episode masters (masters/*) and private media assets CANNOT be streamed via this endpoint.
    Direct calls for protected media return HTTP 403 Forbidden.
    Clients MUST request an authorized media session via POST /media/sessions/create.
    Public static artwork (artwork/*) is allowed.
    """
    clean_key = storage_service._clean_key(storage_key)
    
    # Phase 6O-5: Direct streaming of protected episode masters or non-allowlisted objects is strictly forbidden
    if clean_key.startswith("masters/") or clean_key.startswith("private/") or (clean_key not in PUBLIC_STREAM_ALLOWLIST and not clean_key.startswith("artwork/")):
        raise HTTPException(
            status_code=403,
            detail="Direct streaming of protected media assets is prohibited. Please request an authorized playback session via POST /media/sessions/create."
        )

    if not storage_service.object_exists(clean_key):
        if not storage_service.s3_client and clean_key in PUBLIC_STREAM_ALLOWLIST:
            presigned = storage_service.generate_presigned_download_url(clean_key, expires_in_seconds=3600)
            return RedirectResponse(url=presigned["download_url"], status_code=307)
        raise HTTPException(status_code=404, detail=f"Media asset '{clean_key}' not found in object storage")
    presigned = storage_service.generate_presigned_download_url(clean_key, expires_in_seconds=3600)
    return RedirectResponse(url=presigned["download_url"], status_code=307)


@router.get("/artwork/{storage_key:path}")
def get_artwork_asset(storage_key: str):
    """
    Phase 6J-2R-B: Durable artwork retrieval endpoint.
    Serves stored artwork binary with immutable caching headers.
    """
    from fastapi.responses import Response
    clean_key = storage_service._clean_key(storage_key)
    if not clean_key.startswith("artwork/"):
        clean_key = f"artwork/{clean_key}"

    binary = storage_service.get_stored_binary(clean_key)
    if not binary:
        raise HTTPException(status_code=404, detail=f"Artwork asset '{clean_key}' not found in storage")

    ext = clean_key.rsplit(".", 1)[-1].lower() if "." in clean_key else "jpg"
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "svg": "image/svg+xml"
    }
    media_type = media_types.get(ext, "image/jpeg")

    return Response(
        content=binary,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff"
        }
    )



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

@router.post("/presigned-upload-url", response_model=PresignedUploadResponse, dependencies=[Depends(require_role(["creator", "admin"]))])
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

@router.post("/presigned-upload", dependencies=[Depends(require_role(["creator", "admin"]))])
def get_presigned_upload_alias(req: PresignedUploadRequest):
    """
    Backward-compatibility alias matching Pillar 4 architecture specs.
    Protected by Creator/Admin RBAC.
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

@router.post("/jobs/transcode", dependencies=[Depends(require_role(["creator", "admin"]))])
def dispatch_media_job(req: DispatchJobRequest):
    """Dispatches an asynchronous media transcoding job outside the request thread. Protected by Creator/Admin RBAC."""
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

