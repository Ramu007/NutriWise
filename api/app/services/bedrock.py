"""Bedrock food photo analysis via Claude vision.

Uses the Anthropic SDK's Bedrock client. The SDK handles SigV4 via boto3's
credential chain — no manual signing. Vision input is sent as base64-encoded
image bytes; output is parsed into a Pydantic model using structured outputs.
"""
from __future__ import annotations

import base64
import logging
from typing import Literal

from anthropic import AnthropicBedrock

from app.core.config import Settings, get_settings
from app.models.food import FoodPhotoAnalysis

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a nutrition analyst. Given a photo of a meal, identify every distinct food item and estimate its serving size and macros.

Rules:
- Prefer common units (e.g. "1 cup", "150 g", "1 slice") that a home cook would use.
- If the photo is ambiguous, lower `confidence` for that item but still return your best guess.
- kcal/protein/carbs/fat must be non-negative. Fiber is optional (0 if unknown).
- `confidence` is 0.0-1.0, your subjective certainty for that single item.
- In `notes`, flag anything relevant: poor lighting, occluded items, unusual dish, branded packaging visible, etc. Keep it under 300 chars.
- Always include `model_used` = the model id you are.
"""

ImageMediaType = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


def _client(settings: Settings) -> AnthropicBedrock:
    return AnthropicBedrock(aws_region=settings.aws_region)


def analyze_food_photo(
    image_bytes: bytes,
    media_type: ImageMediaType = "image/jpeg",
    user_hint: str | None = None,
    settings: Settings | None = None,
) -> FoodPhotoAnalysis:
    """Send a food photo to Claude on Bedrock and parse the response.

    `user_hint` lets the caller pass context Claude can't see from the photo alone
    (e.g. "this is a home-cooked South Indian thali, ~2 people").
    """
    s = settings or get_settings()
    client = _client(s)

    b64 = base64.standard_b64encode(image_bytes).decode("ascii")

    user_text = "Analyze this meal photo and return a structured breakdown."
    if user_hint:
        user_text += f"\n\nUser context: {user_hint.strip()}"

    result = client.messages.parse(
        model=s.bedrock_model_id,
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
        response_model=FoodPhotoAnalysis,
    )

    analysis: FoodPhotoAnalysis = result.parsed
    # Recompute totals from items — the model sometimes rounds inconsistently.
    analysis.total_kcal = round(sum(i.kcal for i in analysis.items), 1)
    analysis.total_protein_g = round(sum(i.protein_g for i in analysis.items), 1)
    analysis.total_carbs_g = round(sum(i.carbs_g for i in analysis.items), 1)
    analysis.total_fat_g = round(sum(i.fat_g for i in analysis.items), 1)
    if not analysis.model_used:
        analysis.model_used = s.bedrock_model_id
    analysis.request_id = getattr(result, "id", None)
    return analysis
