"""AWS Lambda entrypoint.

Mangum adapts ASGI (FastAPI) apps to Lambda/API Gateway. Imported only by the
container image; local dev uses uvicorn against `app.main:app`.
"""
from __future__ import annotations

from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="auto")
