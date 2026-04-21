"""Repository protocols.

Kept narrow on purpose — routers should use only these methods, not backend-
specific ones. New access patterns go here first, then get implemented in
both `memory` and `dynamo`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.models.booking import BookingOut
from app.models.food import FoodLogEntry
from app.models.health import HealthProfileOut
from app.models.nutritionist import NutritionistOut


class UserRepo(Protocol):
    def get_profile(self, user_id: str) -> HealthProfileOut | None: ...
    def put_profile(self, profile: HealthProfileOut) -> HealthProfileOut: ...


class NutritionistRepo(Protocol):
    def get(self, nutritionist_id: str) -> NutritionistOut | None: ...
    def put(self, nutritionist: NutritionistOut) -> NutritionistOut: ...
    def list_all(self) -> list[NutritionistOut]: ...


class FoodLogRepo(Protocol):
    def add(self, entry: FoodLogEntry) -> FoodLogEntry: ...
    def list_for_day(self, user_id: str, day: date) -> list[FoodLogEntry]: ...


class BookingRepo(Protocol):
    def get(self, booking_id: str) -> BookingOut | None: ...
    def put(self, booking: BookingOut) -> BookingOut: ...
    def list_for_nutritionist(self, nutritionist_id: str) -> list[BookingOut]: ...
    def list_for_user(self, user_id: str) -> list[BookingOut]: ...


@dataclass
class RepoBundle:
    """All four repos, injected together so the DI graph is a single object."""

    users: UserRepo
    nutritionists: NutritionistRepo
    food_logs: FoodLogRepo
    bookings: BookingRepo
