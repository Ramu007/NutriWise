"""Nutritionist directory — register, search, fetch."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import Principal, get_current_principal
from app.deps import get_repos
from app.models.nutritionist import (
    NutritionistIn,
    NutritionistOut,
    NutritionistSpecialty,
    VerificationStatus,
)
from app.repositories.base import RepoBundle
from app.services.matching import SearchFilters, filter_nutritionists

router = APIRouter(prefix="/v1/nutritionists", tags=["nutritionists"])


@router.post("", response_model=NutritionistOut, status_code=201)
def register(
    body: NutritionistIn,
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> NutritionistOut:
    out = NutritionistOut(
        **body.model_dump(),
        nutritionist_id=str(uuid4()),
        verification_status=VerificationStatus.pending,
        created_at=datetime.now(UTC),
    )
    return repos.nutritionists.put(out)


@router.get("", response_model=list[NutritionistOut])
def search(
    country: Annotated[str | None, Query(pattern="^(US|IN)$")] = None,
    city: str | None = None,
    specialty: NutritionistSpecialty | None = None,
    language: str | None = None,
    min_rating: Annotated[float | None, Query(ge=0, le=5)] = None,
    max_virtual_rate: Annotated[float | None, Query(gt=0)] = None,
    only_approved: bool = True,
    repos: RepoBundle = Depends(get_repos),
) -> list[NutritionistOut]:
    f = SearchFilters(
        country=country,
        city=city,
        specialty=specialty,
        language=language,
        min_rating=min_rating,
        max_virtual_rate=max_virtual_rate,
        only_approved=only_approved,
    )
    return filter_nutritionists(repos.nutritionists.list_all(), f)


@router.get("/{nutritionist_id}", response_model=NutritionistOut)
def get_one(
    nutritionist_id: str,
    repos: RepoBundle = Depends(get_repos),
) -> NutritionistOut:
    n = repos.nutritionists.get(nutritionist_id)
    if n is None:
        raise HTTPException(status_code=404, detail="nutritionist not found")
    return n


@router.post("/{nutritionist_id}/verify", response_model=NutritionistOut)
def verify(
    nutritionist_id: str,
    status: VerificationStatus,
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> NutritionistOut:
    if principal.role not in ("admin", "dev"):
        raise HTTPException(status_code=403, detail="admin only")
    n = repos.nutritionists.get(nutritionist_id)
    if n is None:
        raise HTTPException(status_code=404, detail="nutritionist not found")
    updated = n.model_copy(update={"verification_status": status})
    return repos.nutritionists.put(updated)
