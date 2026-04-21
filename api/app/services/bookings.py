"""Booking conflict detection."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from app.models.booking import BookingOut, BookingStatus


def _end(b_start: datetime, duration_minutes: int) -> datetime:
    return b_start + timedelta(minutes=duration_minutes)


def conflicts_with_existing(
    nutritionist_id: str,
    start: datetime,
    duration_minutes: int,
    existing: Iterable[BookingOut],
) -> bool:
    """Does [start, start+duration) overlap any non-cancelled booking for this nutritionist?"""
    new_end = _end(start, duration_minutes)
    for b in existing:
        if b.nutritionist_id != nutritionist_id:
            continue
        if b.status == BookingStatus.cancelled:
            continue
        b_end = _end(b.starts_at, b.duration_minutes)
        # Overlap iff new_start < b_end AND b_start < new_end.
        if start < b_end and b.starts_at < new_end:
            return True
    return False
