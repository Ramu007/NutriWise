"""Food photo analysis + daily summary."""
from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal
from uuid import uuid4

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.security import Principal, get_current_principal
from app.deps import get_repos
from app.models.food import DailySummary, FoodLogEntry, FoodPhotoAnalysis
from app.models.health import HealthProfileIn, enrich_profile
from app.repositories.base import RepoBundle
from app.services.bedrock import analyze_food_photo
from app.services.daily_summary import summarize
from app.services.uploads import ImageContentType, fetch_object, presign_put

router = APIRouter(prefix="/v1/food", tags=["food"])

_SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


class PresignUploadIn(BaseModel):
    content_type: ImageContentType


class PresignUploadOut(BaseModel):
    url: str
    s3_key: str
    expires_in: int
    method: Literal["PUT"] = "PUT"
    required_headers: dict[str, str]


class AnalyzeKeyIn(BaseModel):
    s3_key: str
    hint: str | None = None


@router.post("/analyze", response_model=FoodPhotoAnalysis)
async def analyze(
    photo: UploadFile = File(...),
    hint: str | None = Form(default=None),
    principal: Principal = Depends(get_current_principal),
) -> FoodPhotoAnalysis:
    if photo.content_type not in _SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"unsupported image type {photo.content_type!r}; use jpeg/png/webp/gif",
        )
    data = await photo.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty photo")
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"] = (
        photo.content_type  # type: ignore[assignment]
    )
    return analyze_food_photo(data, media_type=media_type, user_hint=hint)


@router.post("/uploads/presign", response_model=PresignUploadOut)
def presign_upload(
    body: PresignUploadIn,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> PresignUploadOut:
    """Hand the client a short-lived PUT URL so photos go straight to S3.

    The client must PUT with exactly `Content-Type: <body.content_type>`. Any
    mismatch and S3 returns 403 — that's the whole point, it stops the URL
    being reused for non-image payloads.
    """
    url, key, ttl = presign_put(settings, principal.user_id, body.content_type)
    return PresignUploadOut(
        url=url,
        s3_key=key,
        expires_in=ttl,
        required_headers={"Content-Type": body.content_type},
    )


@router.post("/analyze-key", response_model=FoodPhotoAnalysis)
def analyze_by_key(
    body: AnalyzeKeyIn,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> FoodPhotoAnalysis:
    """Analyze a photo already uploaded to S3 under this user's prefix."""
    # Enforce ownership from the key shape — prevents analyzing someone else's upload.
    expected_prefix = f"uploads/{principal.user_id}/"
    if not body.s3_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="s3_key not owned by caller")
    try:
        data, content_type = fetch_object(settings, body.s3_key)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("NoSuchKey", "404"):
            raise HTTPException(status_code=404, detail="upload not found") from e
        raise
    if content_type not in _SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"unsupported image type {content_type!r}; use jpeg/png/webp/gif",
        )
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"] = (
        content_type  # type: ignore[assignment]
    )
    return analyze_food_photo(data, media_type=media_type, user_hint=body.hint)


@router.post("/logs", response_model=FoodLogEntry, status_code=201)
def add_log(
    entry: FoodLogEntry,
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> FoodLogEntry:
    stamped = entry.model_copy(
        update={
            "user_id": principal.user_id,
            "entry_id": entry.entry_id or str(uuid4()),
            "logged_at": entry.logged_at or datetime.now(UTC),
        }
    )
    return repos.food_logs.add(stamped)


@router.post("/summary", response_model=DailySummary)
def daily_summary(
    day: date,
    profile: HealthProfileIn,
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> DailySummary:
    enriched = enrich_profile(principal.user_id, profile)
    entries = repos.food_logs.list_for_day(principal.user_id, day)
    return summarize(principal.user_id, day, entries, enriched.daily_target_kcal)
