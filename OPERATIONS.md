# OPERATIONS

This document describes how to operate the AI Identity Platform in production.

## Environments
- dev: ephemeral, feature branches, preview deployments
- staging: production-like, QA, e2e tests, seeded data
- prod: customer-facing

Each environment has dedicated resources (DB, Redis, buckets) and isolated secrets.

## Deployments
- CI: build, lint, typecheck, test
- CD: tagged releases → build Docker images → deploy via compose/Helm
- Rollback: redeploy previous image tag; DB migrations use safe, reversible changes

## Secrets Management
- Source: GitHub Actions secrets → environment-specific .env files
- Rotate: quarterly or upon incident; maintain key inventory
- Access: principle of least privilege; audit access quarterly

Secrets include:
- OPENAI_API_KEY
- JWT_SECRET
- OAUTH (Google, GitHub, LinkedIn)
- DATABASE_URL, REDIS_URL
- SENDGRID_API_KEY, SENTRY_DSN

## Backups
- PostgreSQL: daily full + 15-min WAL; retain 30 days (prod), 7 days (staging)
- Redis: AOF enabled; snapshot every 5 minutes
- Verify restores monthly; document RTO/RPO

## Monitoring & Alerting
- Health probes: /status on web, api, ai-engine
- Error tracking: Sentry
- Tracing: OpenTelemetry OTLP → collector
- Metrics: p50/p95 latency, error rates, chat rate-limit rejections, verification job lag

## Incident Response
- On-call: rotation documented separately
- SEV triage: SEV1 (outage), SEV2 (degradation), SEV3 (minor)
- Comms: status page, stakeholder updates
- Postmortem within 48h

## Data Retention
- Raw source artifacts: not stored; only proofs metadata
- Claims: retained until user deletes account
- Logs: 14 days (dev), 30 days (staging), 90 days (prod) with PII redaction

## Key Rotations
- API keys and JWT secrets: rotate quarterly
- OAuth client secrets: rotate annually or when members change

## Change Management
- All changes via PR with CI green
- Security review for public endpoints and AI prompt changes

## Runbooks
- Restart services: docker compose restart
- Reindex DB: documented in DB folder
- Migrations: prisma migrate deploy; verify with /status
