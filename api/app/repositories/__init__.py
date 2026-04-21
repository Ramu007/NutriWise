"""Repository layer — persistence abstraction.

Each aggregate (users, nutritionists, food logs, bookings) has a protocol
in `base` and two concrete implementations:

- `memory` — in-process dicts, used for unit tests and local dev when
  DynamoDB isn't available.
- `dynamo` — boto3-backed, used for staging/prod Lambdas.

Routers receive repos via FastAPI `Depends` (`app.deps`). Never import a
repo class directly from a router — always go through the DI getter so tests
can swap backends.
"""
from app.repositories.base import (
    BookingRepo,
    FoodLogRepo,
    NutritionistRepo,
    RepoBundle,
    UserRepo,
)

__all__ = [
    "BookingRepo",
    "FoodLogRepo",
    "NutritionistRepo",
    "RepoBundle",
    "UserRepo",
]
