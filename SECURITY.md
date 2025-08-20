# SECURITY

## PII Classification
- Class A (Sensitive): emails, phone numbers, addresses, government IDs
- Class B (Confidential): employer names, education institution, dates
- Class C (Public): skills, project names, verified claim proofs (URLs, hashed IDs)

Only Class C appears on public endpoints. Class A must never be sent to AI models or logs.

## Data Handling
- Storage: structured claims and proof metadata only (no raw docs/emails)
- Redaction: all logs and AI prompts pass through redaction utils
- Encryption: TLS in transit; at rest via managed storage
- Access: RBAC; admin access logged and reviewed monthly

## Breach Policy
- Detection: Sentry alerts, anomaly detection on public traffic
- Response: contain → assess scope → rotate secrets → notify affected users within 72h
- Forensics: retain logs (redacted) for 90 days

## Vulnerability Management
- CI runs npm audit + pip-audit
- Monthly dependency review

## Secrets
- Stored in GitHub Actions and environment managers; no secrets in repo

## AI Safety
- Refusal policy for questions requesting PII not present on card
- Verified-facts-only RAG; no hallucinated employers/education
