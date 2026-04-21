# NutriWise

A marketplace platform connecting customers with certified nutritionists for online consultations and in-home kitchen audits. AI-powered food photo analysis, daily tracking, and personalized meal recommendations — built for US and India metropolitan cities.

## Status

**Phase 0 — foundation in progress.** This repo contains the monorepo skeleton, a working FastAPI backend with Bedrock-powered food photo analysis, an Expo React Native app, and AWS CDK infra. See [docs/roadmap.md](docs/roadmap.md) for the phased plan.

## Repo layout

```
nutriwise/
├── api/          # FastAPI backend (Python 3.13)
├── mobile/       # Expo React Native app (iOS, Android, Web)
├── infra/        # AWS CDK stack (Python)
├── docs/         # Architecture, compliance, roadmap
├── scripts/      # Dev helpers
└── .github/      # CI/CD workflows
```

## Quickstart (dev)

```bash
# backend
cd api && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# mobile (requires Node 20+)
cd mobile && npm install && npx expo start

# infra (requires Node 20+ for CDK, Python 3.13)
cd infra && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && npx cdk synth
```

## Tech stack

- **Frontend**: React Native + Expo (iOS/Android/Web)
- **Backend**: Python 3.13 + FastAPI
- **Database**: DynamoDB (events/real-time) + Aurora Serverless v2 PostgreSQL (relational)
- **Auth**: Amazon Cognito (Google, Apple, email)
- **AI**: Amazon Bedrock — Claude Sonnet 4.6 for food photo analysis and meal recommendations
- **Real-time chat**: AWS AppSync
- **Video**: Amazon Chime SDK
- **Search**: OpenSearch Serverless
- **Storage**: S3 + CloudFront
- **Infra**: AWS CDK (Python)
- **Notifications**: SNS (push) + SES (email)

## Compliance

- HIPAA (US): PHI encryption at rest + in transit, BAAs with AWS, CloudTrail audit logging, least-privilege IAM
- DPDP Act 2023 (India): explicit consent, data residency options, parental consent for minors, defined retention windows

See [docs/compliance.md](docs/compliance.md) for the full checklist.

## License

Proprietary — all rights reserved.
