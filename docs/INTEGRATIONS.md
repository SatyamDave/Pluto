# Integrations

## ATS Integration Gateway
- Endpoints:
  - POST `/ats/:vendor/sync-candidate` – Sync candidate with Resume JSON + PDF
  - POST `/ats/:vendor/webhook` – Receive ATS events
- Vendors: Greenhouse, Lever (initial)
- Auth: per-employer API credentials (encrypted)

## Apply with Work.ID (OIDC)
- Discovery: `/.well-known/openid-configuration`
- Scopes:
  - `work_card.basic`: headline, top skills, trust score
  - `work_card.verified_claims`: verified skills/experiences only
- Consent: selective disclosure; short-lived signed JWTs

## Resume JSON + PDF
- Resume JSON v0 schema in `@workid/resume-json`
- PDF maker in `@workid/pdf-maker`
- API endpoints:
  - GET `/export/public/cards/:slug/resume.json`
  - POST `/export/cards/:id/pdf`
