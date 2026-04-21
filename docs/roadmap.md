# Roadmap

## Phase 0 — Foundation (this repo)

- [x] Monorepo with api/, mobile/, infra/, docs/, CI
- [x] FastAPI backend: health profile, nutritionist directory, Bedrock food
      photo analysis, daily summary, bookings
- [x] 56 pytest cases covering math, validation, matching, conflicts, HTTP
- [x] CDK stacks (Auth, Data, Media, Api) with 5 synth smoke tests
- [x] Expo app: onboarding, profile, meal logging, nutritionist list
- [x] GitHub Actions CI across all three surfaces

## Phase 1 — MVP (target Q3 2026)

**Backend**

- [ ] DynamoDB DAOs replace in-memory stores (`api/app/repositories/`)
- [ ] Cognito JWKS validation and role-scoped endpoints
- [ ] `POST /v1/bookings` creates a Chime SDK meeting and stores the id
- [ ] Nutritionist verification workflow (doc upload, admin review UI)
- [ ] Subscription billing — Stripe for US, Razorpay for India
- [ ] AppSync chat schema + subscription resolvers
- [ ] OpenSearch index for nutritionist discovery

**Mobile**

- [ ] Real Cognito auth (hosted UI + Google + Apple)
- [ ] Booking flow: calendar picker → confirmation → Chime video session
- [ ] In-app chat (AppSync subscriptions)
- [ ] Daily summary screen with progress rings
- [ ] Push notifications (APNS/FCM via SNS)

**Compliance**

- [ ] BAAs executed
- [ ] DPDP consent flow, data-export endpoint, grievance contact
- [ ] Region routing — `ap-south-1` for India users, `us-east-1` for US
- [ ] CloudTrail + AWS Backup in prod

## Phase 2 — Scale

- [ ] Kitchen audit flow (5-section workflow: pantry / appliances / staples /
      practices / recommendations)
- [ ] Workout video catalog (HLS via CloudFront)
- [ ] Admin dashboard (web) for moderation + payouts
- [ ] Multi-language UI (Hindi, Kannada, Marathi, Spanish)
- [ ] Marketplace search ranking (popularity, locality, response time)

## Phase 3 — Expansion

- [ ] SaaS API for clinics (white-label)
- [ ] Integrations: Apple Health, Fitbit, Google Fit
- [ ] Group programs (cohort-based, multi-customer sessions)
