SHELL := /bin/bash

.PHONY: dev test e2e seed fmt audit build up down status

 dev:
	npm run dev

 test:
	npx playwright test tests/e2e || true; pytest -q || true

 e2e:
	npx playwright test tests/e2e

 seed:
	npm run db:seed --workspace=packages/database

 fmt:
	black apps/api packages/ai-engine || true; isort apps/api packages/ai-engine || true; npx prettier --write . || true

 audit:
	npm audit --audit-level=moderate || true; pip install pip-audit && pip-audit || true

 build:
	docker compose build

 up:
	docker compose up -d

 down:
	docker compose down -v

 status:
	curl -s http://localhost:8000/status || true; curl -s http://localhost:8001/status || true
