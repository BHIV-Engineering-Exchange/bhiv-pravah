# TRUTH & REPLAY VALIDATION

Date: 2026-05-21

Objective
- Validate Bucket as a truth anchor: write integrity, read-back integrity, lineage continuity, deterministic replay readiness.

Environment
- Staging server: http://127.0.0.1:9005
- Staging artifact path: `data/artifacts-staging`

Test performed
1. Fetched staging chain head `/bucket/latest-hash`.
   - Previous chain: `{"last_hash":"a8787ca0...","artifact_count":1}`
2. Posted a `truth_event` artifact using the existing contract (allowed envelope fields).
   - Artifact written: `dc2b3cac-de28-4049-83d9-71ef76f1dce7`
   - Server returned computed hash: `3f2f3f9593ce10b474c0cfd682ef9714d5396dea05449cbf070559e618f6d33c`
3. Locally computed deterministic hash using the canonical algorithm (sorted keys, separators=(',',':')).
   - Local computed hash matched server hash exactly.
4. Read the artifact back via `/bucket/artifact/{id}` and recomputed the hash from the stored envelope.
   - Read-back hash matched server hash exactly.
5. Verified lineage
   - Stored `parent_hash` matched the previous chain head.
   - `/bucket/latest-hash` after write showed new head `3f2f3f95...` and `artifact_count` incremented by 1.

Checks (all passed)
- stored hash == produced hash (server returned hash == local computed hash)
- read-back hash == stored hash (read-back recomputed hash == server hash)
- lineage preserved (parent_hash matched previous head)
- deterministic replay readiness: artifacts are stored with deterministic server-computed hashes and the chain advanced predictably

Command run
```
python tests/truth_replay_validation.py http://127.0.0.1:9005
```

Result: PASS — the staging instance demonstrates write & read integrity and lineage continuity for the tested flow.

Next recommended actions
- Extend these checks to one representative product flow (SVACS) with its payload shape.
- Archive `data/artifacts-staging/artifact_log.jsonl` as proof-of-run for audit.
- Proceed to Phase 5 (SVACS integration readiness).
