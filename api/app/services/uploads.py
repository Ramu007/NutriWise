"""S3 presigned uploads for food photos.

The mobile app uploads bytes directly to S3 with a presigned PUT URL, then
hands the returned `s3_key` to the API for analysis. This keeps large image
payloads out of API Gateway's 10 MB cap and off the Lambda's egress hop.

Bucket layout:
    uploads/{user_id}/{uuid}.{ext}   — raw uploads, expire after 30 days
    processed/{user_id}/...          — derived thumbnails, auto-tiered

Security:
- Presigned URLs are constrained to a specific `Content-Type`, so a client
  can't swap the payload for JS/HTML and trick the CDN into serving it.
- Keys are server-generated from the authenticated principal's `user_id` —
  the client never picks its own key.
"""
from __future__ import annotations

from typing import Literal
from uuid import uuid4

import boto3
from botocore.config import Config

from app.core.config import Settings

ImageContentType = Literal[
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
]

_EXT_FOR_TYPE: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

_PRESIGN_TTL_SECONDS = 300  # 5 minutes — plenty for mobile, short enough to limit replay.


def _s3_client(settings: Settings):
    # SigV4 is required for presigned URLs with content-type binding.
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        config=Config(signature_version="s3v4"),
    )


def build_upload_key(user_id: str, content_type: ImageContentType) -> str:
    ext = _EXT_FOR_TYPE[content_type]
    return f"uploads/{user_id}/{uuid4()}.{ext}"


def presign_put(
    settings: Settings,
    user_id: str,
    content_type: ImageContentType,
) -> tuple[str, str, int]:
    """Return `(presigned_url, s3_key, expires_in)`.

    The client must PUT with the exact `Content-Type` header — S3 will reject
    a mismatch. That lets us enforce image-only uploads without scanning bytes.
    """
    key = build_upload_key(user_id, content_type)
    url = _s3_client(settings).generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.food_photos_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=_PRESIGN_TTL_SECONDS,
        HttpMethod="PUT",
    )
    return url, key, _PRESIGN_TTL_SECONDS


def fetch_object(settings: Settings, key: str) -> tuple[bytes, str]:
    """Download bytes + content-type from S3. Raises botocore ClientError on 404."""
    resp = _s3_client(settings).get_object(Bucket=settings.food_photos_bucket, Key=key)
    return resp["Body"].read(), resp.get("ContentType", "image/jpeg")
