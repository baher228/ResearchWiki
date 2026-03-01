"""Lean S3 helper — upload files, get public URLs."""

import os
import logging
from urllib.parse import quote
import boto3
from botocore.exceptions import ClientError
from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_client():
    settings = get_settings()
    kwargs = {
        "region_name": settings.AWS_REGION,
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    }
    if settings.AWS_SESSION_TOKEN:
        kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
    return boto3.client("s3", **kwargs)


def upload_file(local_path: str, s3_key: str, content_type: str = None, public: bool = False) -> str:
    """Upload a single file to S3. Returns the S3 key."""
    settings = get_settings()
    client = _get_client()
    extra = {}
    if content_type:
        extra["ContentType"] = content_type
    
    # Note: We no longer send ACL="public-read" because the bucket has ACLs disabled 
    # (Object Ownership: Bucket owner enforced). 
    # Public access is handled via the S3 Bucket Policy instead.
    client.upload_file(local_path, settings.S3_BUCKET_NAME, s3_key, ExtraArgs=extra or None)
    logger.info("Uploaded %s → s3://%s/%s", local_path, settings.S3_BUCKET_NAME, s3_key)
    return s3_key


def upload_bytes(data: bytes, s3_key: str, content_type: str = "application/octet-stream", public: bool = False) -> str:
    """Upload raw bytes to S3."""
    settings = get_settings()
    client = _get_client()
    kwargs = {
        "Bucket": settings.S3_BUCKET_NAME,
        "Key": s3_key,
        "Body": data,
        "ContentType": content_type,
    }
    
    # Note: We no longer send ACL="public-read" because the bucket has ACLs disabled 
    # (Object Ownership: Bucket owner enforced). 
    # Public access is handled via the S3 Bucket Policy instead.
    client.put_object(**kwargs)
    logger.info("Uploaded bytes (%d) → s3://%s/%s", len(data), settings.S3_BUCKET_NAME, s3_key)
    return s3_key


def get_text(s3_key: str) -> str:
    """Get text content of an S3 object."""
    settings = get_settings()
    client = _get_client()
    response = client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
    return response["Body"].read().decode("utf-8")


def upload_directory(local_dir: str, s3_prefix: str, public: bool = False) -> int:
    """Upload all files in a directory to S3 under a prefix. Returns count."""
    count = 0
    for fname in os.listdir(local_dir):
        fpath = os.path.join(local_dir, fname)
        if os.path.isfile(fpath):
            ct = "image/png" if fname.endswith(".png") else "image/jpeg" if fname.endswith((".jpg", ".jpeg")) else None
            upload_file(fpath, f"{s3_prefix}/{fname}", content_type=ct, public=public)
            count += 1
    return count


def get_url(s3_key: str) -> str:
    """Get the public URL for an S3 object."""
    settings = get_settings()
    # URL-encode each path segment to handle spaces and special characters in S3 keys
    encoded_key = "/".join(quote(segment, safe="") for segment in s3_key.split("/"))
    
    # Check if bucket is in a different region and use exact subdomain to avoid 301 redirects
    try:
        loc = _get_client().get_bucket_location(Bucket=settings.S3_BUCKET_NAME).get('LocationConstraint')
        region = loc if loc else settings.AWS_REGION
    except Exception:
        region = settings.AWS_REGION
        
    return f"https://{settings.S3_BUCKET_NAME}.s3.{region}.amazonaws.com/{encoded_key}"
