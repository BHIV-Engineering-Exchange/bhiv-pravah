# TRACE CONTINUITY PROOF

Date: 2026-05-20

Summary:
- Local verification: PASS — trace preserved end-to-end on local instance.
- Deployed verification (Render): ATTEMPTED — write failed due to schema mismatch (server rejected `trace_id` as an unknown envelope field).

Local run (non-destructive):
- Command: `python tests/trace_continuity_test.py http://127.0.0.1:8005`
- Result: POST 200, Stored `artifact_id`: d5021366-e162-4b72-9e58-d981644b88e5
- Read-back: GET returned `trace_id`: trace-test-1779260651
- Conclusion: `trace_id` preserved; chain head advanced; local chain state updated.

Deployed run (writes to production):
- Command: `python tests/trace_continuity_test.py https://bhiv-bucket.onrender.com`
- Result: POST 400
- Server response body:

```
{"detail":{"error":"ValidationError","message":"Artifact validation failed: Unknown envelope field: trace_id. Schema drift detected.","artifact_id":"ee1c3239-694d-4cdc-822c-12ad90fd95bb"}}
```

Interpretation:
- The deployed Render instance enforces a different artifact envelope contract than the local instance used for testing. Specifically, `trace_id` is not accepted as a top-level envelope field on the deployed service.
- Because the deployed schema differs, the same test payload that passed locally is rejected remotely.

Next steps / remediation options:
1. Adapt test payload to the deployed contract:
   - Move `trace_id` into `payload` or include it via header `X-Context: {"trace_id":"..."}` per constitutional docs.
   - Ensure envelope fields match the deployed `ALLOWED_ENVELOPE_FIELDS` (inspect `/constitutional/core/contract` or coordinate with ops).
   - Re-run test against Render after adapting payload.
2. Coordinate a brief staging deployment that mirrors the local schema so integration tests can run without impacting production.
3. If you want, I can automatically adapt and retry the deployed write (I will not proceed without explicit approval).

Artifacts & logs:
- Local artifact appended to `data/artifacts/artifact_log.jsonl` with hash and chain update.
- Deployed error response captured above.

Signature: automated test suite run by agent (trace continuity verifier)
