# NutriWise Infrastructure (AWS CDK, Python)

All AWS resources are provisioned via the CDK in this directory.

## Stacks

- **AuthStack** — Cognito user pool, mobile app client, customer/nutritionist/admin groups.
- **DataStack** — DynamoDB tables (users, nutritionists, food logs, bookings) with GSIs sized for the query patterns in `api/app/services/*`.
- **MediaStack** — S3 bucket for food photos with 30-day lifecycle on raw uploads, plus CloudFront distribution for thumbnail delivery.
- **ApiStack** — Docker-image Lambda that runs the FastAPI app via Mangum, fronted by an HTTP API.

## Quickstart

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'

# Run stack smoke tests (no AWS credentials needed)
pytest

# Synthesize (needs aws-cdk CLI: npm i -g aws-cdk)
ENV=dev cdk synth

# Deploy (requires AWS creds + Docker for the Lambda image asset)
ENV=dev cdk deploy --all
```

## Environment selection

`ENV` defaults to `dev`. Non-prod stacks have `RemovalPolicy.DESTROY` so teardown is cheap; `prod` retains tables and the photo bucket.
