"""FastAPI dependency injection for the repository bundle.

The bundle is built once per process (cached via `lru_cache`). Tests override
this dependency to inject memory or moto-backed repos per test.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.repositories.base import RepoBundle
from app.repositories.factory import build_repos


@lru_cache
def _cached_bundle() -> RepoBundle:
    return build_repos(get_settings())


def get_repos(settings: Settings = Depends(get_settings)) -> RepoBundle:
    # When settings pull from env vars we still want a stable bundle per process,
    # so the cache keys on the fact that `get_settings` is itself lru_cached.
    del settings
    return _cached_bundle()


def reset_repo_cache() -> None:
    """Clear the cached bundle — called from tests between setups."""
    _cached_bundle.cache_clear()
