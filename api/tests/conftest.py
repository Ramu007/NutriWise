from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

# Ensure dev mode (skips Cognito) before settings cache warms up.
os.environ.setdefault("ENV", "dev")
os.environ.pop("COGNITO_USER_POOL_ID", None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Import inside the fixture so env vars above take effect before Settings() is read.
    from app.deps import get_repos
    from app.main import create_app
    from app.repositories.base import RepoBundle
    from app.repositories.memory import (
        InMemoryBookingRepo,
        InMemoryFoodLogRepo,
        InMemoryNutritionistRepo,
        InMemoryUserRepo,
    )

    bundle = RepoBundle(
        users=InMemoryUserRepo(),
        nutritionists=InMemoryNutritionistRepo(),
        food_logs=InMemoryFoodLogRepo(),
        bookings=InMemoryBookingRepo(),
    )

    app = create_app()
    app.dependency_overrides[get_repos] = lambda: bundle
    with TestClient(app) as c:
        yield c


@pytest.fixture
def customer_headers() -> dict[str, str]:
    return {"X-User-Id": "user-abc", "X-User-Role": "customer"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"X-User-Id": "admin-1", "X-User-Role": "admin"}
