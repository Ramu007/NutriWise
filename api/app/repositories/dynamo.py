"""DynamoDB-backed repositories.

Pydantic ↔ DynamoDB mapping: we use `model.model_dump(mode="json")` to get
JSON-safe dicts (ISO datetime strings, enum values), then convert floats to
Decimal for DynamoDB, which rejects native floats. On read we go Decimal →
float in the same hop and hand the dict to Pydantic for validation.

TTL: food_logs rows include a `ttl` attribute (unix seconds, 2 years out) so
the table auto-expires old data. The app sets it on write; DynamoDB's TTL
sweeper deletes rows asynchronously.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeDeserializer
from pydantic import BaseModel

from app.models.booking import BookingOut
from app.models.food import FoodLogEntry
from app.models.health import HealthProfileOut
from app.models.nutritionist import NutritionistOut

_FOOD_LOG_TTL = timedelta(days=365 * 2)
_deserializer = TypeDeserializer()


def _to_item(model: BaseModel) -> dict[str, Any]:
    """Serialize a Pydantic model into a DynamoDB-safe dict."""
    raw = model.model_dump(mode="json")
    return _convert_floats(raw)


def _convert_floats(value: Any) -> Any:
    if isinstance(value, float):
        # Decimal(str(float)) avoids binary-precision surprises.
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _convert_floats(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert_floats(v) for v in value]
    return value


def _from_item(item: dict[str, Any]) -> dict[str, Any]:
    return _decimal_to_float(item)


def _decimal_to_float(value: Any) -> Any:
    if isinstance(value, Decimal):
        # Whole numbers stay ints so Pydantic's int fields don't complain.
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, dict):
        return {k: _decimal_to_float(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_decimal_to_float(v) for v in value]
    return value


def _table(table_name: str, endpoint_url: str | None, region: str):
    kwargs: dict[str, Any] = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.resource("dynamodb", **kwargs).Table(table_name)


class DynamoUserRepo:
    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None) -> None:
        self._t = _table(table_name, endpoint_url, region)

    def get_profile(self, user_id: str) -> HealthProfileOut | None:
        resp = self._t.get_item(Key={"user_id": user_id})
        item = resp.get("Item")
        if not item:
            return None
        return HealthProfileOut.model_validate(_from_item(item))

    def put_profile(self, profile: HealthProfileOut) -> HealthProfileOut:
        self._t.put_item(Item=_to_item(profile))
        return profile


class DynamoNutritionistRepo:
    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None) -> None:
        self._t = _table(table_name, endpoint_url, region)

    def get(self, nutritionist_id: str) -> NutritionistOut | None:
        resp = self._t.get_item(Key={"nutritionist_id": nutritionist_id})
        item = resp.get("Item")
        if not item:
            return None
        return NutritionistOut.model_validate(_from_item(item))

    def put(self, n: NutritionistOut) -> NutritionistOut:
        self._t.put_item(Item=_to_item(n))
        return n

    def list_all(self) -> list[NutritionistOut]:
        # Phase 1 full scan — acceptable while volume is small. When volume
        # grows, route through OpenSearch rather than paginating a scan.
        items: list[dict[str, Any]] = []
        kwargs: dict[str, Any] = {}
        while True:
            resp = self._t.scan(**kwargs)
            items.extend(resp.get("Items", []))
            last = resp.get("LastEvaluatedKey")
            if not last:
                break
            kwargs["ExclusiveStartKey"] = last
        return [NutritionistOut.model_validate(_from_item(i)) for i in items]


class DynamoFoodLogRepo:
    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None) -> None:
        self._t = _table(table_name, endpoint_url, region)

    def add(self, entry: FoodLogEntry) -> FoodLogEntry:
        item = _to_item(entry)
        # Unix timestamp 2 years out — DynamoDB's TTL sweeper will delete it.
        item["ttl"] = int((entry.logged_at + _FOOD_LOG_TTL).timestamp())
        self._t.put_item(Item=item)
        return entry

    def list_for_day(self, user_id: str, day: date) -> list[FoodLogEntry]:
        start = datetime.combine(day, datetime.min.time(), tzinfo=UTC).isoformat()
        end = datetime.combine(day, datetime.max.time(), tzinfo=UTC).isoformat()
        resp = self._t.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("logged_at").between(start, end),
        )
        return [FoodLogEntry.model_validate(_from_item(i)) for i in resp.get("Items", [])]


class DynamoBookingRepo:
    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None) -> None:
        self._t = _table(table_name, endpoint_url, region)

    def get(self, booking_id: str) -> BookingOut | None:
        resp = self._t.get_item(Key={"booking_id": booking_id})
        item = resp.get("Item")
        if not item:
            return None
        return BookingOut.model_validate(_from_item(item))

    def put(self, b: BookingOut) -> BookingOut:
        self._t.put_item(Item=_to_item(b))
        return b

    def list_for_nutritionist(self, nutritionist_id: str) -> list[BookingOut]:
        resp = self._t.query(
            IndexName="by_nutritionist_start",
            KeyConditionExpression=Key("nutritionist_id").eq(nutritionist_id),
        )
        ids = [i["booking_id"] for i in resp.get("Items", [])]
        return [b for b in (self.get(i) for i in ids) if b is not None]

    def list_for_user(self, user_id: str) -> list[BookingOut]:
        resp = self._t.query(
            IndexName="by_user_start",
            KeyConditionExpression=Key("user_id").eq(user_id),
        )
        ids = [i["booking_id"] for i in resp.get("Items", [])]
        return [b for b in (self.get(i) for i in ids) if b is not None]


# Exported for the TypeDeserializer import to be used; keeps linters happy.
__all__ = [
    "DynamoUserRepo",
    "DynamoNutritionistRepo",
    "DynamoFoodLogRepo",
    "DynamoBookingRepo",
    "_deserializer",
]
