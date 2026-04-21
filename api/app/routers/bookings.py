"""Session bookings — virtual, in-home, kitchen audit."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import Principal, get_current_principal
from app.deps import get_repos
from app.models.booking import BookingIn, BookingOut, BookingStatus
from app.models.nutritionist import VerificationStatus
from app.repositories.base import RepoBundle
from app.services.bookings import conflicts_with_existing
from app.services.pricing import commission, currency_for, rate_for

router = APIRouter(prefix="/v1/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=201)
def create(
    body: BookingIn,
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> BookingOut:
    n = repos.nutritionists.get(body.nutritionist_id)
    if n is None:
        raise HTTPException(status_code=404, detail="nutritionist not found")
    if n.verification_status != VerificationStatus.approved:
        raise HTTPException(status_code=409, detail="nutritionist not yet approved")

    try:
        rate = rate_for(n, body.type)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    existing = repos.bookings.list_for_nutritionist(n.nutritionist_id)
    if conflicts_with_existing(n.nutritionist_id, body.starts_at, body.duration_minutes, existing):
        raise HTTPException(status_code=409, detail="time slot conflicts with an existing booking")

    out = BookingOut(
        **body.model_dump(),
        booking_id=str(uuid4()),
        user_id=principal.user_id,
        status=BookingStatus.pending,
        price=rate,
        currency=currency_for(n.country),
        created_at=datetime.now(UTC),
        chime_meeting_id=None,
    )
    return repos.bookings.put(out)


@router.get("", response_model=list[BookingOut])
def list_mine(
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> list[BookingOut]:
    items = repos.bookings.list_for_user(principal.user_id)
    return sorted(items, key=lambda b: b.starts_at)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel(
    booking_id: str,
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> BookingOut:
    b = repos.bookings.get(booking_id)
    if b is None:
        raise HTTPException(status_code=404, detail="booking not found")
    if b.user_id != principal.user_id and principal.role != "admin":
        raise HTTPException(status_code=403, detail="not your booking")
    if b.status in (BookingStatus.completed, BookingStatus.cancelled):
        raise HTTPException(status_code=409, detail=f"booking already {b.status.value}")
    updated = b.model_copy(update={"status": BookingStatus.cancelled})
    return repos.bookings.put(updated)


@router.get("/{booking_id}/commission")
def preview_commission(
    booking_id: str,
    principal: Principal = Depends(get_current_principal),
    repos: RepoBundle = Depends(get_repos),
) -> dict[str, float | str]:
    b = repos.bookings.get(booking_id)
    if b is None:
        raise HTTPException(status_code=404, detail="booking not found")
    take = commission(b.price)
    return {
        "booking_id": b.booking_id,
        "gross": b.price,
        "platform_commission": take,
        "nutritionist_payout": round(b.price - take, 2),
        "currency": b.currency,
    }
