# Resume JSON v0

See schema in `packages/resume-json-schema/src/schema.ts`.

Minimal example:

```json
{
  "person": { "name": "Demo Dev", "headline": "Full-Stack Engineer" },
  "trust": { "score": 92, "breakdown": { "verified": 0.8, "corroborated": 0.15, "self": 0.05 } },
  "skills": [ { "name": "React", "verified": true, "evidenceRefs": ["github_repo:demo/react-app"] } ],
  "experiences": [ { "role": "Engineer", "startDate": "2023-01", "highlights": ["Built X"], "verificationStatus": "verified", "evidenceRefs": [] } ],
  "education": [],
  "projects": [ { "name": "AWS deployment pipeline", "summary": "CI/CD", "links": [], "evidenceRefs": [] } ],
  "verifications": [],
  "links": { "publicCardUrl": "https://work.id/u/demo-dev" },
  "meta": { "cardId": "abc123", "version": "0", "generatedAt": "2024-01-01T00:00:00Z" }
}
```
