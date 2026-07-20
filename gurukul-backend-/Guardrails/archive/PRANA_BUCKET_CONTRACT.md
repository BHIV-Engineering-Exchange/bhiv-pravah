# PRANA Bucket Contract

## Purpose

Frozen contract between PRANA and Bucket ingestion. Exact payload schema, transmission semantics, failure handling. Immutable without specification update.

## Contract Version

**Version:** 1.0.0  
**Status:** Frozen

## Endpoint

**URL:** `POST https://bucket.bhiv.in/api/v1/telemetry/prana`  
**Auth:** `Authorization: Bearer {token}`  
**Content-Type:** `application/json`

## Payload Schema

```json
{
  "system_id": "UUID v4 (required)",
  "timestamp": "ISO8601 datetime (required)",
  "state": "IDLE|ACTIVE|READING|TYPING|NAVIGATING|SEARCHING|VIEWING (required)",
  "signals": {
    "keyboard_events": "integer (required, ≥0)",
    "mouse_events": "integer (required, ≥0)",
    "scroll_events": "integer (required, ≥0)",
    "focus_events": "integer (required, ≥0)",
    "route_changes": "integer (required, ≥0)",
    "search_queries": "integer (required, ≥0)",
    "content_displays": "integer (required, ≥0)"
  },
  "window_duration_ms": "integer (required, typically 2000)",
  "metadata": {
    "prana_version": "string (required, matches spec version)",
    "observation_window_id": "string (required, unique per window)"
  }
}
```

## Required Fields

**All fields required.** No optional fields. Missing fields → Packet construction fails → Packet discarded.

## Append-Only Guarantees

- **Immutability:** Packets cannot be modified, updated, or deleted
- **Idempotency:** Duplicate transmissions acceptable
- **Temporal Ordering:** Out-of-order packets acceptable

## Batch Semantics

- **Single Packet:** One packet per 2-second window
- **No Batching:** Each packet transmitted individually
- **Packet Independence:** No packet dependencies

## Retry Posture

**No Retries:** Single attempt only. On failure → Packet discarded.

**Failure Conditions:**
- Network timeout (5s)
- HTTP 4xx/5xx errors
- Connection refused
- DNS failure

## Transmission Semantics

- **Synchronous:** Transmission completes before next window
- **Timeout:** 5 seconds
- **Success:** HTTP 200/201/202
- **Failure:** Discard packet, continue

## Non-Authoritative Statement

PRANA is non-authoritative. PRANA does not:
- Request Bucket configuration changes
- Request Bucket availability
- Request Bucket capacity increases
- Request Bucket authentication changes

Bucket has full authority over ingestion acceptance, storage, and processing.

## Contract Immutability

Frozen contract. Changes require:
- Specification version update
- System-level approval
- Migration plan
- Backward compatibility analysis
