from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = Field(default="dev")
    aws_region: str = Field(default="us-east-1")
    bedrock_model_id: str = Field(default="us.anthropic.claude-sonnet-4-6-v1:0")

    dynamo_endpoint: str | None = None
    cognito_user_pool_id: str | None = None
    cognito_app_client_id: str | None = None
    food_photos_bucket: str = Field(default="nutriwise-food-photos-dev")

    users_table: str = Field(default="nutriwise-users")
    nutritionists_table: str = Field(default="nutriwise-nutritionists")
    food_logs_table: str = Field(default="nutriwise-food-logs")
    bookings_table: str = Field(default="nutriwise-bookings")

    # "memory" (default in dev) or "dynamo". In staging/prod we default to dynamo.
    repo_backend: str | None = None

    # Dev-only: return a canned food-photo analysis instead of calling Bedrock.
    # Handy for local web testing where we don't want to wire AWS credentials.
    analysis_stub: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
