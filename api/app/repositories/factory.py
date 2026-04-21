"""Repo backend selection.

Selection rule:
- `REPO_BACKEND=dynamo` (or `ENV=prod`/`staging`) → DynamoDB backend.
- Anything else (including `dev` when unset) → in-memory.

We pick in-memory as the default so `uvicorn app.main:app` works without
any AWS setup. Set `REPO_BACKEND=dynamo` (and `DYNAMO_ENDPOINT` if using
DynamoDB Local) to exercise the real code path locally.
"""
from __future__ import annotations

from app.core.config import Settings
from app.repositories.base import RepoBundle
from app.repositories.dynamo import (
    DynamoBookingRepo,
    DynamoFoodLogRepo,
    DynamoNutritionistRepo,
    DynamoUserRepo,
)
from app.repositories.memory import (
    InMemoryBookingRepo,
    InMemoryFoodLogRepo,
    InMemoryNutritionistRepo,
    InMemoryUserRepo,
)


def _want_dynamo(settings: Settings) -> bool:
    explicit = getattr(settings, "repo_backend", None)
    if explicit:
        return explicit.lower() == "dynamo"
    return settings.env in ("staging", "prod")


def build_repos(settings: Settings) -> RepoBundle:
    if _want_dynamo(settings):
        return RepoBundle(
            users=DynamoUserRepo(settings.users_table, settings.aws_region, settings.dynamo_endpoint),
            nutritionists=DynamoNutritionistRepo(
                settings.nutritionists_table, settings.aws_region, settings.dynamo_endpoint
            ),
            food_logs=DynamoFoodLogRepo(
                settings.food_logs_table, settings.aws_region, settings.dynamo_endpoint
            ),
            bookings=DynamoBookingRepo(
                settings.bookings_table, settings.aws_region, settings.dynamo_endpoint
            ),
        )
    return RepoBundle(
        users=InMemoryUserRepo(),
        nutritionists=InMemoryNutritionistRepo(),
        food_logs=InMemoryFoodLogRepo(),
        bookings=InMemoryBookingRepo(),
    )
