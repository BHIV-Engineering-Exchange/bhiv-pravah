# API / Trace Matrix

| Domain | Endpoint | Correlation ID Used | Replay Endpoint | Evidence |
|---|---|---|---|---|
| Workforce runtime | `POST /v1/workforce/organizations` | Yes | `GET /v1/workforce/trace-replay` | `api_proof_workforce.json` |
| Workforce runtime | `POST /v1/workforce/employees` | Yes | `GET /v1/workforce/trace-replay` | `api_proof_workforce.json` |
| Lifecycle | `POST /v1/workforce/employees/{id}/lifecycle/onboard` | Yes | `GET /v1/workforce/trace-replay` | `replay_trace_proof.md` |
| Policy engine | `POST /v1/policies/evaluate` | Yes | `GET /v1/workforce/trace-replay` | `replay_trace_proof.md` |
| Challenge flow | `POST /v1/governance/challenges` | Yes | `GET /v1/workforce/trace-replay` | `replay_trace_proof.md` |
| Decision ledger | `POST /v1/decisions` | Yes | `GET /v1/decisions/replay` | `replay_trace_proof.md` |
| SETU participation | `POST /v1/setu/signals/{signal_type}` | Yes | `GET /v1/setu/trace/{trace_id}` | `setu_signal_proof.json` |

Write routes propagate correlation IDs from gateway request state. Replay endpoints are read-only and validate lineage continuity.
