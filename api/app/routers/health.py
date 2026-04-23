"""Health profile router — BMI/BMR/TDEE enrichment for the caller."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import Principal, get_current_principal
from app.deps import get_repos
from app.models.health import HealthProfileIn, HealthProfileOut, enrich_profile
from app.repositories.base import RepoBundle

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.post("/profile", response_model=HealthProfileOut)
def upsert_profile(
    body: HealthProfileIn,
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> HealthProfileOut:
    """Compute BMI/BMR/TDEE and persist for the caller."""
    out = enrich_profile(principal.user_id, body)
    return repos.users.put_profile(out)


@router.get("/profile", response_model=HealthProfileOut)
def get_profile(
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> HealthProfileOut:
    profile = repos.users.get_profile(principal.user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="profile not set")
    return profile
