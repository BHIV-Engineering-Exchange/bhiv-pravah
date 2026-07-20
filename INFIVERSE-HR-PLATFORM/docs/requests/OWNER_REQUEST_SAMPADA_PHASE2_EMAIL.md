# Email Draft: Request for API Docs & Owner Confirmation — SAMPADA Phase 2

To: [integration-owner@example.com]
Cc: [technical-contact@example.com]
Subject: Request: API docs, sandbox access, and owner confirmation for Sampada↔SETU Phase 2

Hello [Owner Name],

We are preparing the Phase 2 convergence deliverable for Sampada (docs/SAMPADA_SETU_CONVERGENCE_MAP.md) and require your help to finalize signal contracts and test endpoints.

Attached: an importable Postman collection with example requests you can run against a test sandbox: `docs/postman/SAMPADA_PHASE2_postman_collection.json`.

Please provide or confirm the following by replying to this email:

- Integration owner and technical contact details.
- Base URLs for test and production environments.
- Authentication method and a test API key/token or sandbox credentials.
- Example request/response for the payroll visibility endpoint (confirm only hashed identifiers are accepted).
- Confirmation that `X-Correlation-Id` is supported for trace/replay continuity.
- Any privacy or PII constraints we must enforce beyond the standard (e.g., required hashing salts, token scopes).

Sign-off checklist (reply with YES/NO next to each):
- I accept ownership for the listed endpoints and will act as integration owner. []
- Endpoints accept hashed/opaque identifiers only per privacy rules. []
- `X-Correlation-Id` header is supported and will be propagated. []
- I will provide a test API key by [date]. []

If you prefer, we can schedule a short call to walk through the Postman collection and run live tests.

Thank you,
Sampada Integration Team
