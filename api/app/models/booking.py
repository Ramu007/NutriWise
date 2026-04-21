from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class BookingType(StrEnum):
    virtual = "virtual"
    in_home = "in_home"
    kitchen_audit = "kitchen_audit"


class BookingStatus(StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class BookingIn(BaseModel):
    nutritionist_id: str
    type: BookingType
    starts_at: datetime
    duration_minutes: int = Field(default=45, ge=15, le=240)
    notes: str = Field(default="", max_length=2000)


class BookingOut(BookingIn):
    booking_id: str
    user_id: str
    status: BookingStatus = BookingStatus.pending
    price: float
    currency: str
    created_at: datetime
    chime_meeting_id: str | None = None
