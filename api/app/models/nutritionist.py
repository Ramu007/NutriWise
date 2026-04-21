from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class Credential(StrEnum):
    # US
    rdn = "RDN"
    rd = "RD"
    cns = "CNS"
    # India
    ida_rd = "IDA-RD"
    bsc_nutrition = "BSc-Nutrition"
    msc_nutrition = "MSc-Nutrition"


class VerificationStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class NutritionistSpecialty(StrEnum):
    weight_loss = "weight_loss"
    diabetes = "diabetes"
    pcos = "pcos"
    pediatric = "pediatric"
    sports = "sports"
    prenatal = "prenatal"
    gut_health = "gut_health"
    plant_based = "plant_based"


class NutritionistIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    country: Literal["US", "IN"]
    city: str
    credentials: list[Credential] = Field(min_length=1)
    credential_doc_urls: list[str] = Field(default_factory=list)
    specialties: list[NutritionistSpecialty] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["en"])
    bio: str = Field(default="", max_length=2000)

    # All rates in the nutritionist's local currency (USD for US, INR for IN).
    virtual_rate: float = Field(gt=0)
    in_home_rate: float | None = None
    kitchen_audit_rate: float | None = None


class NutritionistOut(NutritionistIn):
    nutritionist_id: str
    verification_status: VerificationStatus = VerificationStatus.pending
    rating_avg: float = 0.0
    rating_count: int = 0
    created_at: datetime
