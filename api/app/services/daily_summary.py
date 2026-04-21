"""Roll up food log entries into a DailySummary."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from app.models.food import DailySummary, FoodLogEntry


def summarize(
    user_id: str,
    day: date,
    entries: Iterable[FoodLogEntry],
    target_kcal: float,
) -> DailySummary:
    entries = list(entries)
    total_kcal = round(sum(i.kcal for e in entries for i in e.items), 1)
    total_protein = round(sum(i.protein_g for e in entries for i in e.items), 1)
    total_carbs = round(sum(i.carbs_g for e in entries for i in e.items), 1)
    total_fat = round(sum(i.fat_g for e in entries for i in e.items), 1)
    remaining = round(target_kcal - total_kcal, 1)

    # Band is ±10% of target. Narrower on a small target would be noisy.
    lower, upper = target_kcal * 0.9, target_kcal * 1.1
    if total_kcal < lower:
        status = "under"
    elif total_kcal > upper:
        status = "over"
    else:
        status = "on_track"

    return DailySummary(
        user_id=user_id,
        day=day,
        total_kcal=total_kcal,
        total_protein_g=total_protein,
        total_carbs_g=total_carbs,
        total_fat_g=total_fat,
        target_kcal=target_kcal,
        remaining_kcal=remaining,
        status=status,
        entry_count=len(entries),
    )
