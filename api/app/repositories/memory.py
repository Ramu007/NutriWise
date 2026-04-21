"""In-memory repository implementations — unit tests + local dev."""
from __future__ import annotations

from datetime import date

from app.models.booking import BookingOut
from app.models.food import FoodLogEntry
from app.models.health import HealthProfileOut
from app.models.nutritionist import NutritionistOut


class InMemoryUserRepo:
    def __init__(self) -> None:
        self._profiles: dict[str, HealthProfileOut] = {}

    def get_profile(self, user_id: str) -> HealthProfileOut | None:
        return self._profiles.get(user_id)

    def put_profile(self, profile: HealthProfileOut) -> HealthProfileOut:
        self._profiles[profile.user_id] = profile
        return profile


class InMemoryNutritionistRepo:
    def __init__(self) -> None:
        self._items: dict[str, NutritionistOut] = {}

    def get(self, nutritionist_id: str) -> NutritionistOut | None:
        return self._items.get(nutritionist_id)

    def put(self, n: NutritionistOut) -> NutritionistOut:
        self._items[n.nutritionist_id] = n
        return n

    def list_all(self) -> list[NutritionistOut]:
        return list(self._items.values())


class InMemoryFoodLogRepo:
    def __init__(self) -> None:
        self._by_user: dict[str, list[FoodLogEntry]] = {}

    def add(self, entry: FoodLogEntry) -> FoodLogEntry:
        self._by_user.setdefault(entry.user_id, []).append(entry)
        return entry

    def list_for_day(self, user_id: str, day: date) -> list[FoodLogEntry]:
        return [e for e in self._by_user.get(user_id, []) if e.logged_at.date() == day]


class InMemoryBookingRepo:
    def __init__(self) -> None:
        self._items: dict[str, BookingOut] = {}

    def get(self, booking_id: str) -> BookingOut | None:
        return self._items.get(booking_id)

    def put(self, b: BookingOut) -> BookingOut:
        self._items[b.booking_id] = b
        return b

    def list_for_nutritionist(self, nutritionist_id: str) -> list[BookingOut]:
        return [b for b in self._items.values() if b.nutritionist_id == nutritionist_id]

    def list_for_user(self, user_id: str) -> list[BookingOut]:
        return [b for b in self._items.values() if b.user_id == user_id]
