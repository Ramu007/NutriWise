from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class FoodItem(BaseModel):
    name: str
    serving: str = Field(default="1 serving")
    kcal: float = Field(ge=0)
    protein_g: float = Field(default=0, ge=0)
    carbs_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)
    fiber_g: float = Field(default=0, ge=0)
    confidence: float = Field(default=0.7, ge=0, le=1)


class FoodPhotoAnalysis(BaseModel):
    items: list[FoodItem]
    total_kcal: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    notes: str = ""
    model_used: str
    request_id: str | None = None


class FoodLogEntry(BaseModel):
    entry_id: str
    user_id: str
    logged_at: datetime
    meal: Literal["breakfast", "lunch", "dinner", "snack"]
    items: list[FoodItem]
    source: Literal["photo", "manual", "recommendation"] = "photo"
    photo_s3_key: str | None = None


class DailySummary(BaseModel):
    user_id: str
    day: date
    total_kcal: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    target_kcal: float
    remaining_kcal: float
    status: Literal["under", "on_track", "over"]
    entry_count: int
