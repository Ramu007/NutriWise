"""Daily summary rollup bands."""
from __future__ import annotations

from datetime import UTC, date, datetime

from app.models.food import FoodItem, FoodLogEntry
from app.services.daily_summary import summarize


def _entry(kcal: float, meal: str = "lunch") -> FoodLogEntry:
    return FoodLogEntry(
        entry_id=f"e-{kcal}-{meal}",
        user_id="u-1",
        logged_at=datetime.now(UTC),
        meal=meal,  # type: ignore[arg-type]
        items=[FoodItem(name="x", kcal=kcal, protein_g=10, carbs_g=20, fat_g=5)],
    )


def test_empty_day_is_under():
    s = summarize("u-1", date(2026, 5, 1), [], target_kcal=2000.0)
    assert s.status == "under"
    assert s.entry_count == 0
    assert s.remaining_kcal == 2000.0


def test_on_track_within_band():
    # 2000 target, 1900 eaten -> within 10% -> on_track
    s = summarize("u-1", date(2026, 5, 1), [_entry(1900)], target_kcal=2000.0)
    assert s.status == "on_track"


def test_over_above_band():
    s = summarize("u-1", date(2026, 5, 1), [_entry(2500)], target_kcal=2000.0)
    assert s.status == "over"
    assert s.remaining_kcal == -500.0


def test_totals_sum_items():
    s = summarize("u-1", date(2026, 5, 1), [_entry(500), _entry(600, "dinner")], target_kcal=2000.0)
    assert s.total_kcal == 1100.0
    assert s.entry_count == 2
    assert s.total_protein_g == 20.0  # 10 * 2 items
