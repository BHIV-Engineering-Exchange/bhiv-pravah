# BHIV Phase IV Tier 1 Runtime Capture — 20260713T035150Z

- **Live gateway**: `https://bhiv-hr-gateway-l0xp.onrender.com`
- **Local gateway**: in-process FastAPI harness (mongomock_motor)
- **Correlation id**: `c530d0b7-eb17-4fb8-bc78-e81a500042fd`

## Per-partner tier

| Partner | Tier | Notes |
|---|---|---|
| artha | Tier 2 — dispatcher invoked directly; partner server not booted | `sig-66c8d789c660` |
| crm | Tier 2 — dispatcher invoked directly; partner server not booted | `sig-5f80c230999c` |
| logistics | Tier 2 — CRM dispatcher + `subsystem: logistics` | `sig-8ae9c683f2ef` |
| niyantran | Not Yet Available — Blocked on server MODULE_NOT_FOUND + dispatch script failure | boot probe recorded |

## No Sampada dispatcher

Bucket, PRANA, InsightFlow, Karma — **Not evidenced** (no dispatcher code). Route to GC/MDU.
