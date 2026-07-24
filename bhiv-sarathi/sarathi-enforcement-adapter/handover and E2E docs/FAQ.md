# Sarathi — FAQ

Fast answers to the questions a new owner asks first. Deeper detail is in
`SETUP_GUIDE.md`, `SYSTEM_OVERVIEW.md`, and `ARCHITECTURE_FLOW.md`.

---

**Q: What is Sarathi in one line?**
A Policy Enforcement Point: it verifies a sealed decision, enforces it, signs and
audits the result, and optionally propagates it to downstream peers.

**Q: How do I build and run it?**
`go build -o sarathi-enforcement-adapter.exe .` then
`.\sarathi-enforcement-adapter.exe --service`. See `SETUP_GUIDE.md`.

**Q: Does it need a database?**
No. Runtime is a single binary. A PostgreSQL integration exists but is opt-in via
`SARATHI_DB_*` and is not needed to run or test.

**Q: What port does it listen on?**
`SARATHI_SERVICE_ADDR`, default `127.0.0.1:8443`. Set `0.0.0.0:<port>` for any
cloud/non-local host.

**Q: When I send an input, does Sarathi do everything automatically?**
Enforcement runs automatically on every `POST /v1/ingest-decision`. Propagation
to peers does NOT — it requires `SARATHI_PROPAGATE_ON_INGEST=1` plus peer URLs and
the InsightFlow API key. Without those, Sarathi enforces but stays silent to peers.

**Q: Will it work on a cloud host out of the box?**
You must set `SARATHI_SERVICE_ADDR=0.0.0.0:<port>` so the platform can reach it.
That's an env var, not a code change. Local default stays `127.0.0.1:8443`.

**Q: Where are transmissions and decisions logged?**
`proof_logs/peer_propagation_audit.jsonl` (one row per fan-out), plus
`proof_logs/downstream_ack_receipts.jsonl` (receipts), `proof_logs/bucket/`
(Bucket proofs), and `live/<peer>/` (per-peer event logs).

**Q: How do I test the Bucket integration?**
Run `.\scripts\test_bucket.ps1`, or follow `BUCKET_TEST_COMMANDS.md` step by step.
Bucket integration is verified working.

**Q: How do I test InsightFlow?**
Run `.\scripts\test_insightflow.ps1`. NOTE: as of this handover the deployed
InsightFlow server returns 500 on all POST endpoints (server-side, on their end).
The Sarathi side is correct; this is blocked on the InsightFlow team.

**Q: Why does the Bucket `--bucket-transmit` say "Duplicate artifact_id" on re-run?**
It uses a fixed test `decision_id`, so the deterministic `artifact_id` already
exists in the chain. That is expected idempotent behavior (Bucket treats a
duplicate as success), not a failure. Use the manual runbook for fresh writes.

**Q: Why does Bucket's stored `hash` differ from the hash Sarathi sent?**
By design. Bucket computes its own authority hash over its own representation and
does not store raw wire bytes. Integrity is proven by Sarathi's read-back
verification, not by hash equality.

**Q: Where does `trace_id` go in the Bucket envelope?**
Inside `payload`, not top-level. The live deployment rejects unknown top-level
fields. Always check `GET /bucket/schema-info` for the authoritative field list.

**Q: What signs what?**
Sarathi signs its own custody receipts with its Ed25519 enforcement key. Peers
sign their receipts with their own keys; Sarathi verifies each against the
registered public key for that peer. Private keys never cross the wire.

**Q: Is propagation safe to leave off?**
Yes. Enforcement and audit are complete without it. Turn it on only when peer
URLs are configured and you want downstream fan-out.

**Q: How do I add or rotate a peer's key?**
Use `cmd_peer_key_register.go` (`--peer-key-register`) and the trust snapshot.
Old in-flight receipts verify until the registry updates; after update the old
key is rejected.

**Q: What's the difference between `/v1/ingest-decision` and `/v1/enforce`?**
`/v1/ingest-decision` is the primary ingest that also fires the propagation hook.
`/v1/enforce` and `/sarathi/enforce` are enforcement entry points. The service
prints all routes at startup.

**Q: Production mode won't start — why?**
With `SARATHI_ENV=production`, the service refuses to boot without inbound auth
(`SARATHI_INBOUND_AUTH=required`), non-default caller keys
(`SARATHI_CALLER_KEY_<SYSTEM>`), and a trust snapshot. Unset `SARATHI_ENV` for a
development smoke-test. See `SETUP_GUIDE.md` §5.5.

**Q: Where do I start reading the code?**
`enforcement_adapter_main.go` (dispatch) → `service_runtime_cli.go` (service boot)
→ `service_boundary.go` (routes) → `REPO_MAP.md` to jump to any subsystem.
