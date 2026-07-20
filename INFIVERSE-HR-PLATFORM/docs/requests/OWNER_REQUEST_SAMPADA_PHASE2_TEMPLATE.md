# SAMPADA Phase 2 — Owner Request & Checklist (Template)

Purpose: request missing API docs, contact details, and confirm contract items required to finalize the SETU convergence map and signal schemas.

To: [owner-name] <owner-email>
From: Sampada Integration Team
Subject: Request: API docs & owner confirmation for Phase 2 convergence (Sampada ↔ SETU)

Dear [owner-name],

We are preparing the Phase 2 convergence artifacts for Sampada integrations and need your input to finalize signal contracts and test endpoints.

Please provide the following items and confirm the checklist below.

1) Contact details
- Integration owner (name):
- Technical contact (name, email, phone):
- Business owner (name, email):

2) API documentation
- Public endpoint list (base URL + path) for systems: [Niyantran | Artha | Logistics | CRM]
- Auth method (API Key / OAuth2 / Mutual TLS / JWT). Provide example tokens and scopes.
- Rate limits, SLA, and acceptable test window.

3) Endpoint specifics we need filled or confirmed
- Payroll visibility ingest: path, required fields, accepted identifiers (only hashed/opaque IDs), expected response codes.
- Candidate / employee linking endpoints: supported identifiers (hashed employee_id, candidate_id, email_hash).
- Delivery patterns: push webhook vs pull API; if webhooks, provide example payload and retry semantics.

4) Privacy & PII constraints (must be explicit)
- Confirm that raw personally-identifying information will NOT be accepted (no plain-text SSN, payroll account numbers, raw email addresses unless hashed/consented).
- Allowed hashed identifiers and accepted hash algorithms (e.g., SHA-256 with salt). Provide example format.

5) Correlation & observability
- Confirm header or payload field used for correlation IDs (prefer `X-Correlation-Id`).
- Provide any request/response fields we must capture for replay/trace continuity.

6) Example payloads
- Provide 2 example request/response pairs for each critical endpoint (match, workflow trigger, payroll visibility).

7) Test environment access
- Test base URL, test API key/token, and any IP allowlist requirements.

8) Sign-off checklist (please reply with YES/NO next to each)
- I confirm ownership for the listed endpoints and will act as the integration owner. []
- I confirm the provided endpoints accept only hashed/opaque identifiers per privacy rules. []
- I confirm `X-Correlation-Id` is supported and will be passed downstream. []
- I will provide a test API key or test sandbox by [date]. []

Additional notes:
- We will not request or store payroll ownership or credentials — only visibility events and minimal telemetry as per agreed schema.
- If you require a narrower schema or additional privacy constraints, please attach them and we will adapt the draft schemas in `docs/schemas/` accordingly.

Next steps after your reply:
- We will generate a Postman collection (or share existing curl snippets) for owner testing.
- After successful test runs, we will finalize the `docs/SAMPADA_SETU_CONVERGENCE_MAP.md` participation matrix and JSON Schemas.

Thank you,
Sampada Integration Team
