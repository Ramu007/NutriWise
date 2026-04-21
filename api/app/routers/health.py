"""Health profile router — BMI/BMR/TDEE enrichment for the caller."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import Principal, get_current_principal
from app.models.health import HealthProfileIn, HealthProfileOut, enrich_profile

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.post("/profile", response_model=HealthProfileOut)
def upsert_profile(
    body: HealthProfileIn,
    principal: Principal = Depends(get_current_principal),
) -> HealthProfileOut:
    """Compute BMI/BMR/TDEE/daily target. Phase 0 is stateless — persistence lands with DynamoDB wiring."""
    return enrich_profile(principal.user_id, body)
