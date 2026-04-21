# NutriWise API

FastAPI backend for NutriWise.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the Swagger UI.

## Test

```bash
pytest
pytest --cov=app --cov-report=term-missing
```

## Environment

Copy `.env.example` → `.env` and fill in AWS creds. The app reads:

| Var | Default | Purpose |
|-----|---------|---------|
| `AWS_REGION` | `us-east-1` | Bedrock + DynamoDB + S3 region |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-6-v1:0` | Vision + text generation model |
| `DYNAMO_ENDPOINT` | _(empty)_ | Local DynamoDB endpoint for tests |
| `ENV` | `dev` | `dev` / `staging` / `prod` |

## Structure

```
app/
├── main.py              # FastAPI app factory
├── core/
│   ├── config.py        # Settings via pydantic-settings
│   ├── security.py      # Cognito JWT validation stub
│   └── logging.py       # Structured JSON logging
├── models/              # Pydantic models (API) + SQLAlchemy models (DB)
├── routers/             # APIRouter modules per resource
└── services/            # Business logic (Bedrock, TDEE, matching)
```
