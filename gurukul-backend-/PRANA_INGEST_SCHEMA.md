# PRANA Packet Ingestion Schema

This document defines the required schema and validation rules for the `/api/v1/bucket/prana/ingest` endpoint.

## 1. Required Fields
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `string` | ISO-8601 format (e.g., `2026-05-14T10:30:00Z`) |
| `active_seconds` | `float` | Time spent active in the 5s window |
| `idle_seconds` | `float` | Time spent idle in the 5s window |
| `away_seconds` | `float` | Time spent away in the 5s window |
| `raw_signals` | `object` | Dictionary of raw telemetry signals |

## 2. State Mapping (At least one required)
| Field | Type | Description |
|-------|------|-------------|
| `state` | `string` | Must be: `WORKING`, `IDLE`, `AWAY`, `DISTRACTED`, `FAKING` |
| `cognitive_state` | `string` | Custom state label (e.g., `"DEEP_WORK"`) |

## 3. Optional Metadata
| Field | Type | Description |
|-------|------|-------------|
| `user_id` | `string` | Unique identifier for the user |
| `session_id` | `string` | Current session identifier |
| `lesson_id` | `string` | Current lesson identifier |
| `focus_score` | `float` | Range `0.0` to `100.0` |
| `integrity_score` | `float` | Range `0.0` to `1.0` |

## 4. Critical Validation Rules (Avoid 422 Errors)
1.  **The 5-Second Window**: The sum of `active_seconds + idle_seconds + away_seconds` must equal **exactly 5.0**.
2.  **Non-Negative**: All time values must be `>= 0`.
3.  **ISO Format**: The `timestamp` must be a valid ISO-8601 string.

## Example Payload
```json
{
  "user_id": "student_001",
  "timestamp": "2026-05-14T12:00:00Z",
  "state": "WORKING",
  "active_seconds": 4.2,
  "idle_seconds": 0.8,
  "away_seconds": 0.0,
  "focus_score": 85.0,
  "raw_signals": {
    "mouse_clicks": 12,
    "keystrokes": 45
  }
}
```
