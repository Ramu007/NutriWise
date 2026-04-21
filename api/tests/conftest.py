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
    from app.main import create_app
    from app.routers import bookings as bk_router
    from app.routers import food as food_router
    from app.routers import nutritionists as n_router

    # Fresh in-memory stores per test.
    n_router._registry.clear()
    bk_router._bookings.clear()
    food_router._logs.clear()

    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def customer_headers() -> dict[str, str]:
    return {"X-User-Id": "user-abc", "X-User-Role": "customer"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"X-User-Id": "admin-1", "X-User-Role": "admin"}
