# Replay Visualization API

## Purpose

Replay visualization APIs provide replay-safe observability only.

The dashboard never becomes an operational authority surface.

---

# Supported APIs

| API | Purpose |
|---|---|
| /api/replay/timeline | Replay timeline visibility |
| /api/replay/lineage | Lineage reconstruction |
| /api/replay/provenance | Provenance visibility |
| /api/replay/telemetry | Replay telemetry |
| /api/replay/trace | Trace reconstruction |

---

# Constitutional Restrictions

The dashboard cannot:

- execute actions
- mutate replay state
- alter telemetry
- modify governance
- bypass validation

---

# Replay Guarantees

Replay APIs preserve:

- deterministic replay
- append-only continuity
- provenance visibility
- lineage continuity
- replay-safe observability
