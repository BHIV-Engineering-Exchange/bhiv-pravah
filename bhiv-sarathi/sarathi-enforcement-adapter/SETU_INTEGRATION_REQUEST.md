# Sarathi ↔ SETU — Integration Guide & Request

**For:** SETU team
**Re:** Real approval endpoint, authentication, request/response contract, allow/deny behaviour — and what Sarathi needs back from SETU.
**Scope:** Wire contract only. Self-contained — read top to bottom and you have everything to call Sarathi for approvals.

You asked for four things; §1–§5 answer them. §6 is what we need from you to switch it on. §7 covers an alternative pattern if SETU is a decision *producer* rather than a *caller*.

---

## 1. Approval model & allow/deny behaviour

Sarathi is a **fail-closed Policy Enforcement Point**. Every request gets an explicit verdict:

| `verdict` | Meaning | `execution_state` |
|---|---|---|
| `ALLOW` | Approved | `EXECUTION_PERMITTED` |
| `DENY` | Rejected | `EXECUTION_BLOCKED` |
| `ESCALATE` | Needs higher authority / human review | `EXECUTION_BLOCKED` |

**Fail-closed rule:** anything that is not an explicit `ALLOW` is treated as not-approved. Any auth failure, malformed request, unknown caller, missing permission, or rate-limit breach returns a **deny/blocked** outcome — never a silent allow. Read the outcome from **two fields**: `verdict` (`ALLOW`/`DENY`/`ESCALATE`) and `execution_state` (`EXECUTION_PERMITTED`/`EXECUTION_BLOCKED`). `read` actions are governed exactly like `write`/`execute`/`delete` — same allow/deny path.

---

## 2. Approval endpoint

```
POST  https://<sarathi-url>/approve            # approval request → allow/deny
GET   https://<sarathi-url>/health             # liveness
```

> Wire path: `POST /v1/enforce`. The live base URL is shared out-of-band once the tunnel/host is up. One request → one synchronous verdict; no callback needed.

---

## 3. Authentication method

- **Per-request API key** in the `X-API-Key` header. SETU is registered as a named caller; each request must carry the pre-shared key.
- **Key handover (key never generated on Sarathi's side):** SETU generates a 32-byte secret locally; sends Sarathi only the **SHA-256 fingerprint** out-of-band. SETU then sends the raw secret in `X-API-Key` on every call; Sarathi verifies `sha256(X-API-Key) == registered fingerprint` (constant-time).
- **Transport:** HTTPS only.
- **Optional hardening:** if a signed-request mode is required on your side, we can additionally pin an Ed25519 identity for SETU — tell us in §6 and we'll exchange public keys.

---

## 4. Request contract

```
POST https://<sarathi-url>/approve
Content-Type: application/json
X-API-Key: <SETU pre-shared secret>
```
```json
{
  "agent_id":       "<the actor the action is on behalf of>",
  "resource_id":    "<the target resource>",
  "action":         "read | write | execute | delete",
  "correlation_id": "<your unique id for this request>",
  "caller_system":  "setu",
  "caller_version": "1.0.0",
  "requested_at":   "2026-06-06T00:00:00Z",
  "idempotency_key": "<optional, for safe retries>"
}
```

| Field | Required | Notes |
|---|---|---|
| `agent_id` | yes | identity the action is attributed to |
| `resource_id` | yes | what is being acted on |
| `action` | yes | one of `read`/`write`/`execute`/`delete` |
| `correlation_id` | yes | unique per request; echoed back; used in audit |
| `caller_system` | yes | must be your registered caller id (`setu`) |
| `caller_version` | recommended | your build, for compatibility tracking |
| `requested_at` | recommended | RFC3339 UTC |
| `idempotency_key` | optional | identical retries return the same outcome |

---

## 5. Response contract (how to read allow/deny)

**Approved (HTTP 200):**
```json
{
  "verdict": "ALLOW",
  "execution_state": "EXECUTION_PERMITTED",
  "decision_id": "<stable decision id>",
  "correlation_id": "<your id, echoed>",
  "enforcement_hash": "<sha256 enforcement proof>",
  "request_hash": "<sha256 of the request>",
  "error_code": "OK",
  "enforced_at": "<RFC3339 UTC>",
  "trace_id": "<trace id>"
}
```

**Not approved (HTTP 200 with deny verdict, or 4xx on a malformed/unauthorized request):**
```json
{
  "verdict": "DENY",
  "execution_state": "EXECUTION_BLOCKED",
  "block_reason": "<human-readable reason>",
  "error_code": "<stable error code>",
  "correlation_id": "<your id, echoed>",
  "enforced_at": "<RFC3339 UTC>"
}
```

Decision logic on your side: **treat the request as approved only if `verdict == "ALLOW"` AND `execution_state == "EXECUTION_PERMITTED"`.** Anything else (any other verdict, any non-2xx, any missing field) = not approved. Every error also carries an `X-Sarathi-Error-Code` response header mirroring `error_code`.

---

## 6. What Sarathi needs FROM SETU (to enable the integration)

Please send the following out-of-band so we can register SETU as an approved caller:

1. **Caller identity** — the `caller_system` id you will send (we suggest `setu`) and a version string.
2. **API key fingerprint** — generate a 32-byte secret locally; send us the **SHA-256 fingerprint** only (never the secret). You will use the secret in `X-API-Key`.
3. **Permissions** — which actions SETU needs approved: any of `read`, `write`, `execute`, `delete`.
4. **Action / resource model** — sample `agent_id` and `resource_id` values you'll use, so we can validate/scope correctly.
5. **Expected throughput** — peak requests/minute, so we size your rate limit.
6. **Environments** — your environment names (dev/stage/prod) and, if you front Sarathi behind your own host, those base URLs.
7. **Read-check vs enforce** — confirm whether you want enforced decisions, or a non-mutating "would this be allowed?" check (dry-run). If dry-run is needed, say so and we'll confirm the exact flag.
8. **Signed-identity option** — if you want to additionally sign requests with Ed25519, send your public key + key_id + algorithm (otherwise API-key auth is sufficient).

When we have items 1–5 we can register SETU and run a live approval smoke test against `/approve`.

---

## 7. Alternative pattern — if SETU produces signed decisions

If SETU is not asking Sarathi to decide, but instead **emits already-signed governance decisions** for Sarathi to enforce (like an upstream authority), there is a separate signed-decision ingestion surface with its own contract (Ed25519-signed decision body, registered evaluator, canonical hashing). Tell us your direction in §6 and we'll send that contract instead. Most caller integrations use §2–§5 above.

---

## 8. One-line ask

Tell us (a) your integration direction (caller asking for approvals vs. signed-decision producer), and (b) items 1–5 in §6. With those, SETU is registered and we run a live `/approve` test.
