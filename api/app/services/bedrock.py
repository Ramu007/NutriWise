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
from app.models.food import FoodItem, FoodPhotoAnalysis

log = logging.getLogger(__name__)


def _stub_analysis(image_bytes: bytes, user_hint: str | None) -> FoodPhotoAnalysis:
    """Canned response for local dev without Bedrock access.

    Varies the item set slightly based on image byte size so the UI doesn't
    look like it's stuck returning the exact same thing every time.
    """
    bucket = len(image_bytes) % 3
    if bucket == 0:
        items = [
            FoodItem(name="Grilled chicken breast", serving="150 g", kcal=248,
                     protein_g=46.5, carbs_g=0.0, fat_g=5.4, confidence=0.82),
            FoodItem(name="Brown rice", serving="1 cup cooked", kcal=216,
                     protein_g=5.0, carbs_g=45.0, fat_g=1.8, fiber_g=3.5, confidence=0.78),
            FoodItem(name="Steamed broccoli", serving="1 cup", kcal=55,
                     protein_g=3.7, carbs_g=11.2, fat_g=0.6, fiber_g=5.1, confidence=0.88),
        ]
        notes = "Balanced lean-protein plate. Macros skew protein-heavy."
    elif bucket == 1:
        items = [
            FoodItem(name="Paneer tikka", serving="6 pieces (120 g)", kcal=340,
                     protein_g=18.0, carbs_g=6.0, fat_g=27.0, confidence=0.74),
            FoodItem(name="Roti (whole wheat)", serving="2 pieces", kcal=240,
                     protein_g=7.0, carbs_g=44.0, fat_g=4.0, fiber_g=4.8, confidence=0.80),
            FoodItem(name="Mint chutney", serving="2 tbsp", kcal=25,
                     protein_g=0.5, carbs_g=4.0, fat_g=0.8, confidence=0.60),
        ]
        notes = "Classic North-Indian combo. Fat is on the higher side — swap paneer for tofu to lighten."
    else:
        items = [
            FoodItem(name="Avocado toast", serving="1 slice sourdough + 1/2 avocado", kcal=310,
                     protein_g=8.0, carbs_g=32.0, fat_g=18.0, fiber_g=8.0, confidence=0.86),
            FoodItem(name="Poached egg", serving="1 large", kcal=72,
                     protein_g=6.3, carbs_g=0.4, fat_g=5.0, confidence=0.90),
            FoodItem(name="Cherry tomatoes", serving="6 pieces", kcal=18,
                     protein_g=0.9, carbs_g=3.9, fat_g=0.2, fiber_g=1.2, confidence=0.85),
        ]
        notes = "Good healthy-fats breakfast. Consider adding a fruit for micronutrients."

    hint_note = f" User hint noted: {user_hint.strip()}." if user_hint else ""
    return FoodPhotoAnalysis(
        items=items,
        total_kcal=round(sum(i.kcal for i in items), 1),
        total_protein_g=round(sum(i.protein_g for i in items), 1),
        total_carbs_g=round(sum(i.carbs_g for i in items), 1),
        total_fat_g=round(sum(i.fat_g for i in items), 1),
        notes=(notes + hint_note)[:300],
        model_used="stub:local-dev",
    )

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
    if s.analysis_stub:
        log.info("analysis_stub=True; returning canned FoodPhotoAnalysis")
        return _stub_analysis(image_bytes, user_hint)
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
