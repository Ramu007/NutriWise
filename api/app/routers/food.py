"""Food photo analysis + daily summary."""
from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.security import Principal, get_current_principal
from app.deps import get_repos
from app.models.food import DailySummary, FoodLogEntry, FoodPhotoAnalysis
from app.models.health import HealthProfileIn, enrich_profile
from app.repositories.base import RepoBundle
from app.services.bedrock import analyze_food_photo
from app.services.daily_summary import summarize

router = APIRouter(prefix="/v1/food", tags=["food"])

_SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


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
