"""Lean S3 helper — upload files, get public URLs."""

import os
import logging
import boto3
from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def upload_file(local_path: str, s3_key: str, content_type: str = None) -> str:
    """Upload a single file to S3. Returns the S3 key."""
    settings = get_settings()
    client = _get_client()
    extra = {}
    if content_type:
        extra["ContentType"] = content_type
    client.upload_file(local_path, settings.S3_BUCKET_NAME, s3_key, ExtraArgs=extra)
    logger.info("Uploaded %s → s3://%s/%s", local_path, settings.S3_BUCKET_NAME, s3_key)
    return s3_key


def upload_bytes(data: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
    """Upload raw bytes to S3."""
    settings = get_settings()
    client = _get_client()
    client.put_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key, Body=data, ContentType=content_type)
    logger.info("Uploaded bytes (%d) → s3://%s/%s", len(data), settings.S3_BUCKET_NAME, s3_key)
    return s3_key


def upload_directory(local_dir: str, s3_prefix: str) -> int:
    """Upload all files in a directory to S3 under a prefix. Returns count."""
    count = 0
    for fname in os.listdir(local_dir):
        fpath = os.path.join(local_dir, fname)
        if os.path.isfile(fpath):
            ct = "image/png" if fname.endswith(".png") else None
            upload_file(fpath, f"{s3_prefix}/{fname}", content_type=ct)
            count += 1
    return count


def get_url(s3_key: str) -> str:
    """Get the public URL for an S3 object."""
    settings = get_settings()
    return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
