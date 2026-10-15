"""
Welele Media™ — Milestone 5B: Migrate Frontend Video Assets to Staging Cloudflare R2
Target: R2 bucket 'welele-vod-staging' ONLY (Production is 100% Frozen)
"""

import os
import sys
import boto3
import hashlib
from dotenv import load_dotenv

CANDIDATE_STAGING_PATHS = [
    r"G:\App_Development\App_Dev\Welele Media\.env\.env.staging",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env.staging"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.staging"),
]

staging_env_path = None
for p in CANDIDATE_STAGING_PATHS:
    if os.path.exists(p):
        staging_env_path = p
        break

if not staging_env_path:
    raise RuntimeError("Could not find staging .env file.")

load_dotenv(staging_env_path, override=True)

# Strict production freeze guardrail
TARGET_BUCKET = "welele-vod-staging"
if os.getenv("ENVIRONMENT") == "production" or TARGET_BUCKET != "welele-vod-staging":
    raise RuntimeError(f"CRITICAL SAFETY HALT: Cannot migrate to non-staging bucket '{TARGET_BUCKET}'!")

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
if not (account_id and access_key and secret_key):
    raise RuntimeError("Missing R2 credentials in staging environment.")

endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
s3 = boto3.client(
    "s3",
    endpoint_url=endpoint_url,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name="auto"
)

videos_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "public", "videos"
)

if not os.path.exists(videos_dir):
    raise RuntimeError(f"Videos directory not found at {videos_dir}")

print(f"=== MIGRATING VIDEO ASSETS TO R2 BUCKET: {TARGET_BUCKET} ===")
migrated = []

for fname in sorted(os.listdir(videos_dir)):
    fpath = os.path.join(videos_dir, fname)
    if not os.path.isfile(fpath):
        continue

    size = os.path.getsize(fpath)
    h = hashlib.sha256()
    with open(fpath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    file_sha256 = h.hexdigest()

    storage_key = f"videos/{fname}"
    print(f"\n[Uploading] {fname} ({size:,} bytes, {size/(1024*1024):.2f} MB)...")
    
    with open(fpath, "rb") as f:
        s3.put_object(
            Bucket=TARGET_BUCKET,
            Key=storage_key,
            Body=f,
            ContentType="video/mp4"
        )

    # Verify durability via HeadObject
    head = s3.head_object(Bucket=TARGET_BUCKET, Key=storage_key)
    content_len = head.get("ContentLength", 0)
    etag = head.get("ETag", "").strip('"')

    assert content_len == size, f"Size mismatch for {storage_key}: expected {size}, got {content_len}"

    # Generate presigned download URL to verify playback signing
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": TARGET_BUCKET, "Key": storage_key},
        ExpiresIn=300
    )

    print(f"[Verified] Key: {storage_key} | ContentLength: {content_len:,} | ETag: {etag}")
    print(f"           Presigned Download Probe: {presigned_url[:80]}...")

    migrated.append({
        "filename": fname,
        "storage_key": storage_key,
        "size_bytes": size,
        "sha256": file_sha256,
        "etag": etag
    })

print(f"\n=== MIGRATION COMPLETE: {len(migrated)} assets durably stored in {TARGET_BUCKET} ===")
