# Compliance

NutriWise operates in two regulatory regimes. This document is a working
checklist for how the architecture supports each, and is **not** legal advice.
Work with counsel before launch.

## United States — HIPAA

Nutritional status, allergies, and chronic conditions (PCOS, diabetes, etc.)
qualify as Protected Health Information when tied to an individual.

**Administrative**

- [ ] Business Associate Agreement in place with AWS (HIPAA-eligible services
      listed at https://aws.amazon.com/compliance/hipaa-eligible-services-reference).
- [ ] BAAs with any third parties that touch PHI: Chime SDK (if used for
      telehealth), SES, payment processor.
- [ ] Documented data-access policy; audit trail of admin reads on user
      records.
- [ ] Incident-response plan with 60-day breach notification commitment.

**Technical safeguards (how the architecture supports them)**

- PHI at rest is encrypted — DynamoDB `TableEncryption.AWS_MANAGED`, S3
  `BucketEncryption.S3_MANAGED`, Aurora storage encryption default-on.
- PHI in transit uses TLS 1.2+ — API Gateway default, CloudFront
  `REDIRECT_TO_HTTPS`, S3 `enforce_ssl=True`.
- Access control — Cognito user pool with per-user tokens; IAM policies
  scope Lambda's DynamoDB access to just the four NutriWise tables.
- Logging — structured JSON logs via `app.core.logging`, `x-request-id`
  propagated through every request for audit correlation.
- Minimum necessary — the API never returns a nutritionist's full email to
  other customers; booking responses scope to the requesting user.

**What we still need to wire (Phase 1)**

- CloudTrail + Config in the production account.
- AWS Backup for DynamoDB point-in-time recovery archives (PITR is enabled
  at the table level; backup vault is the next step).
- KMS CMKs for envelope encryption on PHI fields (pseudonymized IDs for
  anything that leaves the primary account).

## India — DPDP Act, 2023

India's Digital Personal Data Protection Act applies to any "digital
personal data" processed in connection with offering services to data
principals in India.

**Obligations we care about at launch**

- **Consent notice** — onboarding must show purpose, categories collected,
  and retention period before collecting health data. Consent must be
  granular and withdrawable.
- **Data principal rights** — the app must support access, correction,
  erasure, and grievance-redressal flows. Phase 1 ships a self-serve
  "download my data" endpoint that reads from DynamoDB and packages a JSON
  export.
- **Children** — processing of data of users under 18 requires verifiable
  parental consent. Our age-gate (min `age_years: 13`) is a floor; India
  users under 18 are blocked until we wire parental consent.
- **Breach notification** — notify the Data Protection Board of India of
  any personal data breach.
- **Data fiduciary registration** — if designated a Significant Data
  Fiduciary (by volume or sensitivity), additional obligations apply
  (DPO appointment, data protection impact assessments). Likely by Phase 2
  scale.

**Localization posture**

The DPDP Act does not currently mandate in-country storage, but the
government retains authority to restrict transfers to specific countries.
We provision Indian-user data in `ap-south-1` (Mumbai) by default and keep
US-user data in `us-east-1`. Nutritionist profiles are country-scoped and
stored in the region matching their `country` attribute.

## Cross-cutting

- Retention defaults: raw meal photos auto-expire after 30 days
  (`s3.LifecycleRule` in `MediaStack`). Parsed analyses persist indefinitely
  until user deletes.
- Audit: every mutating request carries `x-request-id` and authenticated
  `user_id`; logs are structured JSON (`app.core.logging.JSONFormatter`).
- Pen-test cadence (Phase 2): annual third-party assessment before scaling
  advertising.
