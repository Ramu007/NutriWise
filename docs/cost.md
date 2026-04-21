# Cost Posture

NutriWise is serverless-first. This doc lists the decisions that shape the
monthly bill and the guardrails that keep them in place.

## TL;DR estimates

At no traffic (synthesized dev env, nobody logging in): **~$2/month.**

- CloudFront: $0 at rest
- S3: a few cents for request metadata
- Cognito: free tier covers <50K MAU
- DynamoDB: $0 on-demand with no reads/writes
- Lambda: $0 at zero invocations
- CloudWatch Logs: ~$0.50/GB ingested, capped by 2-week retention in dev

At 10K monthly active users, roughly 3 photos + 2 API calls per user per day:

- Lambda (ARM64, 512 MiB, avg 400 ms): ~$4
- API Gateway HTTP API: ~$1
- DynamoDB on-demand: ~$3
- Bedrock Claude vision (~300K food-photo calls): by far the dominant line
  item; sized by model + tokens, not infra. Managed by prompt-caching and
  serving smaller images.
- CloudFront: ~$2 at moderate egress
- S3: <$1

## Decisions

### Compute — Lambda, not ECS/Fargate

Zero at rest. ARM64 Graviton is ~20% cheaper than x86 and usually faster on
Python. Memory right-sized at 512 MiB; CPU on Lambda scales with memory so
over-provisioning memory also overpays for CPU. `aws_lambda_power_tuning` is
the next step once we have real traffic — the optimum varies by workload.

### API — HTTP API, not REST API

HTTP API: $1.00 / million. REST API: $3.50 / million. We don't need API keys,
usage plans, or request validation at the edge — FastAPI handles those.

### Data — DynamoDB on-demand

No capacity to provision at rest. GSIs use `KEYS_ONLY` or `INCLUDE` with the
minimum attributes rather than `ALL` — halves storage and write amplification.
TTL on `food_logs` auto-deletes rows older than 2 years.

Aurora is **not** provisioned in Phase 0. Aurora Serverless v2 has a 0.5 ACU
minimum floor (~$43/month just to exist). We'll introduce it only when a
real relational need shows up.

### Storage — S3 + CloudFront

Raw uploads expire at 30 days (`uploads/` prefix lifecycle). Processed
objects transition to Intelligent-Tiering at 30 days, Glacier Instant
Retrieval at 180. CloudFront price class in dev is `PriceClass_100`
(NA + EU only, ~40% cheaper); prod is `PriceClass_All` for APAC latency.

### Networking — no VPC (yet)

No VPC means no NAT gateway ($32/mo per AZ), no interface endpoints, no idle
load balancers. Lambda reaches DynamoDB, S3, and Bedrock over the AWS
network without a VPC. We'll add one when Aurora lands and Lambdas need to
reach it privately.

### Observability — structured logs, short retention

CloudWatch Logs retention is 14 days in dev, 30 days in prod. The default is
*indefinite*, which silently grows forever. For long-term audit, ship logs
to S3 (cheap, lifecycled) rather than paying CloudWatch storage rates.

### Auth — Cognito free tier

50K MAU free, then $0.0055 / MAU. Social federation (Google, Apple, Facebook)
is free; SAML/OIDC with non-social providers costs extra — avoid unless
enterprise customers show up.

## Guardrails

These are asserted by CDK tests in `infra/tests/test_stacks.py`:

- Lambda architecture is `arm64`
- Lambda memory is 512 MiB (changes require intentional test update)
- Dev CloudFront uses `PriceClass_100`; prod uses `PriceClass_All`
- At least one GSI uses `KEYS_ONLY` projection
- `food_logs` has TTL enabled
- No PITR in dev (saves ~$0.20/GB/month)
- No VPC, no NAT gateway anywhere

## Things we *haven't* done yet (deliberate)

- **Savings Plans / RIs.** Premature; revisit once Lambda + API Gateway +
  DynamoDB on-demand usage has 3 months of history.
- **Bedrock provisioned throughput.** $20/hour minimum — only makes sense
  once on-demand InvokeModel spend exceeds it. Watch Bedrock cost monthly.
- **Multi-region.** Single region (us-east-1) until DPDP Act residency pushes
  us to ap-south-1 for Indian users.
- **WAF.** ~$5/month plus $1/rule plus $0.60/million. Skip until abuse appears.
- **X-Ray.** $5/million traces; enable selectively when debugging, not always.

## Monitoring the bill

- Cost-allocation tags (`project`, `env`, `component`) flow from `app.py`.
  Activate them in Billing preferences once per account.
- Set a monthly Budget alert at $50 for dev, $500 for prod as starting
  points. Tighten once real usage lands.
- Cost Explorer filters by tag, not by stack, so the tags above are how you
  see "what did the api component cost this month."
