# SAMPADA Phase 2 — Postman / Curl Snippets

Purpose: quick, copyable curl examples to validate critical cross-system endpoints during Phase 2 owner sign-off.

Variables used in examples:
- `API_BASE` = `http://localhost:8000`
- `API_KEY` = Gateway API Key (or use appropriate JWT)
- `CORRELATION_ID` = UUID for correlation (example: `3fa85f64-5717-4562-b3fc-2c963f66afa6`)

1) GET Top Matches (Gateway → Agent)

```bash
curl -s -H "Authorization: Bearer $API_KEY" \
  -H "X-Correlation-Id: $CORRELATION_ID" \
  "$API_BASE/v1/match/679a1b2c3d4e5f6789012345/top?limit=5"
```

2) POST Batch Match

```bash
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: $CORRELATION_ID" \
  -d '{"job_ids":[679a1b2c3d4e5f6789012345,679a1b2c3d4e5f6789012346]}' \
  "$API_BASE/v1/match/batch"
```

3) POST Workflow Trigger (Gateway → LangGraph)

```bash
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: $CORRELATION_ID" \
  -d '{
    "workflow_id":"wf_abc123",
    "workflow_type":"candidate_application",
    "input_data":{ "candidate_id":"60a7c2e5f1e4a2b3c4d5e6f7", "job_id":"679a1b2c3d4e5f6789012345", "candidate_email":"alice@example.com" }
  }' \
  "$API_BASE/v1/langgraph/trigger"
```

4) POST RL Feedback (Gateway → LangGraph)

```bash
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: $CORRELATION_ID" \
  -d '{"candidate_id":"60a7c2e5f1e4a2b3c4d5e6f7","job_id":"679a1b2c3d4e5f6789012345","feedback":{"quality":5,"comments":"Good fit."}}' \
  "$API_BASE/rl/feedback"
```

5) Payroll Visibility Ingest (placeholder — Artha contract required)

```bash
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: $CORRELATION_ID" \
  -d '{"employee_id_hashed":"sha256:ab12cd...","payroll_period":"2026-05","gross_amount":2543.75,"payroll_state":"calculated"}' \
  "$API_BASE/external/artha/payroll_visibility"
```

Notes:
- Replace placeholders with real endpoints and credentials once Artha/Niyantran owners confirm contracts.
- Use `X-Correlation-Id` header to propagate correlation IDs; Gateway also accepts `correlation_id` in JSON payloads where applicable.
