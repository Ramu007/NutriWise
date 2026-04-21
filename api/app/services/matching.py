"""Nutritionist search + filtering.

Phase 0: in-memory filter over a list. Phase 1 will replace with OpenSearch
Serverless queries keyed on the same filter shape.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.models.nutritionist import (
    NutritionistOut,
    NutritionistSpecialty,
    VerificationStatus,
)


@dataclass
class SearchFilters:
    country: str | None = None
    city: str | None = None
    specialty: NutritionistSpecialty | None = None
    language: str | None = None
    min_rating: float | None = None
    max_virtual_rate: float | None = None
    only_approved: bool = True


def filter_nutritionists(
    items: Iterable[NutritionistOut], f: SearchFilters
) -> list[NutritionistOut]:
    def keep(n: NutritionistOut) -> bool:
        if f.only_approved and n.verification_status != VerificationStatus.approved:
            return False
        if f.country and n.country != f.country:
            return False
        if f.city and n.city.lower() != f.city.lower():
            return False
        if f.specialty and f.specialty not in n.specialties:
            return False
        if f.language and f.language not in n.languages:
            return False
        if f.min_rating is not None and n.rating_avg < f.min_rating:
            return False
        if f.max_virtual_rate is not None and n.virtual_rate > f.max_virtual_rate:
            return False
        return True

    ranked = [n for n in items if keep(n)]
    # Highest rating first; then review count as tiebreaker.
    ranked.sort(key=lambda n: (n.rating_avg, n.rating_count), reverse=True)
    return ranked
