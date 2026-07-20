# PRANA MongoDB Data Audit

**Document Type**: Database Schema Audit  
**Observer**: System Auditor  
**Date**: 2026-02-09  
**Database**: PostgreSQL (not MongoDB - correction noted)  
**System**: Gurukul Backend

---

## Important Correction

**Database Technology**: PostgreSQL (SQL), not MongoDB  
**Source**: `backend/app/models/prana_models.py` uses SQLAlchemy ORM  
**Reason for Correction**: Task brief mentioned MongoDB, but actual implementation uses PostgreSQL

---

## Database Collections (Tables)

### Table: `prana_packets`

**Purpose**: Stores PRANA packets from frontend before Karma Tracker processes them

**Source**: `backend/app/models/prana_models.py` (lines 18-70)

---

## Field Inventory

### Primary Key

| Field Name | Data Type | Nullable | Indexed | Description |
|------------|-----------|----------|---------|-------------|
| `packet_id` | String (UUID) | No | Yes (Primary) | Unique packet identifier |

### User Identification

| Field Name | Data Type | Nullable | Indexed | Description |
|------------|-----------|----------|---------|-------------|
| `user_id` | String | Yes | Yes | Gurukul user database ID |
| `employee_id` | String | Yes | Yes | EMS employee ID (legacy field) |
| `session_id` | String | Yes | Yes | Session UUID |
| `lesson_id` | String | Yes | No | Current lesson ID |

### System Context

| Field Name | Data Type | Nullable | Indexed | Description |
|------------|-----------|----------|---------|-------------|
| `system_type` | String | Yes | No | "gurukul" or "ems" |
| `role` | String | Yes | No | "student" or "employee" |

### Timestamps

| Field Name | Data Type | Nullable | Indexed | Description |
|------------|-----------|----------|---------|-------------|
| `client_timestamp` | DateTime (TZ) | No | No | When PRANA created the packet |
| `received_at` | DateTime (TZ) | No | Yes | When bucket received packet |
| `processed_at` | DateTime (TZ) | Yes | Yes | When Karma Tracker processed packet |

### Cognitive State

| Field Name | Data Type | Nullable | Indexed | Description |
|------------|-----------|----------|---------|-------------|
| `cognitive_state` | String | Yes | No | Unified state (ON_TASK, THINKING, IDLE, etc.) |
| `state` | String | Yes | No | Legacy state field (WORKING, IDLE, AWAY, etc.) |

### Time Accounting

| Field Name | Data Type | Nullable | Indexed | Description |
|------------|-----------|----------|---------|-------------|
| `active_seconds` | Float | No | No | Time in active state (0-5.0) |
| `idle_seconds` | Float | No | No | Time in idle state (0-5.0) |
| `away_seconds` | Float | No | No | Time in away state (0-5.0) |

**Invariant**: `active_seconds + idle_seconds + away_seconds = 5.0` (validated on ingestion)

### Scores

| Field Name | Data Type | Nullable | Indexed | Description |
|------------|-----------|----------|---------|-------------|
| `focus_score` | Float | Yes | No | 0-100 focus metric |
| `integrity_score` | Float | Yes | No | 0-1 legacy integrity metric |

### Raw Signals

| Field Name | Data Type | Nullable | Indexed | Description |
|------------|-----------|----------|---------|-------------|
| `raw_signals` | JSON | No | No | Aggregate signal counts (see below) |

### Processing Status

| Field Name | Data Type | Nullable | Indexed | Description |
|------------|-----------|----------|---------|-------------|
| `processed_by_karma` | Boolean | No | Yes | Whether Karma Tracker processed this packet |
| `karma_actions` | JSON | Yes | No | List of karma actions generated from this packet |
| `processing_error` | Text | Yes | No | Error message if processing failed |

---

## Composite Indexes

| Index Name | Fields | Purpose |
|------------|--------|---------|
| `idx_user_processed` | `user_id`, `processed_by_karma` | Query unprocessed packets for specific user |
| `idx_received_at` | `received_at` | Time-based queries |
| `idx_processed_at` | `processed_at` | Processing time queries |

---

## Raw Signals JSON Structure

### Observed Fields in `raw_signals`

**Source**: `prana-core/signals.js` (lines 19-51) and `bucket.py` ingestion

| Field Name | Data Type | Description |
|------------|-----------|-------------|
| `timestamp` | String (ISO8601) | Signal collection timestamp |
| `window_focus` | Boolean | Whether window has focus |
| `browser_visibility` | String | "visible" or "hidden" |
| `browser_hidden` | Boolean | Whether browser is hidden |
| `tab_visible` | Boolean | Whether tab is visible |
| `panel_focused` | Boolean | Whether panel has focus |
| `task_tab_active` | Boolean | Whether task tab is active |
| `keystroke_count` | Integer | Aggregate keystroke count |
| `mouse_events` | Integer | Aggregate mouse event count |
| `mouse_distance` | Float | Total mouse distance (pixels) |
| `scroll_events` | Integer | Aggregate scroll event count |
| `content_clicks` | Integer | Aggregate click count |
| `app_switches` | Integer | Number of app/tab switches |
| `mouse_velocity` | Float | Instantaneous mouse velocity (px/s) |
| `scroll_depth` | Float | Scroll position (0-100%) |
| `hover_loops` | Integer | Detected hover loop count |
| `idle_seconds` | Integer | Seconds since last activity |
| `inactivity_ms` | Integer | Milliseconds since last activity |
| `dwell_time_ms` | Integer | Time on page while focused |
| `rapid_click_count` | Integer | Rapid click detection count |

---

## Data Retention

### Observed Behavior

**Retention Policy**: Not explicitly defined in code  
**Deletion Logic**: No automatic deletion observed  
**Growth Pattern**: Unbounded (packets accumulate indefinitely)

**Estimated Growth**:
- 1 packet every 5 seconds per active user
- 12 packets/minute per user
- 720 packets/hour per user
- ~4,320 packets per 6-hour session per user

**Recommendation**: Retention policy should be defined externally (not part of PRANA)

---

## Privacy Audit

### Personal Data Assessment

**Fields Containing User Identifiers**:
- ✅ `user_id` - Database ID (not PII, pseudonymous)
- ✅ `employee_id` - Database ID (legacy, not PII)
- ✅ `session_id` - Session UUID (ephemeral, not user-identifying)
- ✅ `lesson_id` - Lesson ID (not user-identifying)

**Fields NOT Containing Personal Data**:
- ❌ No names
- ❌ No emails
- ❌ No IP addresses
- ❌ No geolocation
- ❌ No device fingerprints
- ❌ No user-generated content

### Content Data Assessment

**Confirmed Absent**:
- ❌ No keystroke content (only counts)
- ❌ No mouse coordinates (only velocity and distance)
- ❌ No click targets (only counts)
- ❌ No scroll content (only depth percentage)
- ❌ No DOM structure
- ❌ No text content
- ❌ No media content

### Behavioral Judgment Assessment

**Confirmed Absent**:
- ❌ No "productivity" scores
- ❌ No "attention" metrics
- ❌ No "engagement" ratings
- ❌ No "relevance" flags
- ❌ No "misuse" indicators
- ❌ No "policy violation" markers

**Present (Observational Only)**:
- ✅ `cognitive_state` - Observational classification (not judgment)
- ✅ `focus_score` - Derived from signals (not behavioral judgment)
- ✅ `active_seconds` - Time accounting (not productivity metric)

---

## Data Flow

### Ingestion Path

1. **Frontend** → Packet constructed every 5 seconds
2. **POST** `/api/v1/bucket/prana/ingest` → Packet transmitted
3. **Validation** → Schema validation (`bucket.py` lines 129-219)
4. **Database** → Inserted into `prana_packets` table
5. **Redis Queue** → Enqueued for Karma Tracker processing
6. **Response** → `{status: "ingested", packet_id: "...", received_at: "..."}`

### Processing Path

1. **Karma Tracker** → Polls `/api/v1/bucket/prana/packets/pending`
2. **Dequeue** → Retrieves packets from Redis queue
3. **Process** → Determines karma action (`bucket_consumer.py` lines 46-84)
4. **Update Karma** → Calls Karma Tracker API
5. **Mark Processed** → POST `/api/v1/bucket/prana/packets/mark-processed`
6. **Database Update** → Sets `processed_by_karma = True`, `processed_at = now()`
7. **Redis Cleanup** → Removes packet from queue

---

## Query Patterns

### Common Queries (from `bucket.py`)

**Get Pending Packets**:
```sql
SELECT * FROM prana_packets 
WHERE processed_by_karma = FALSE 
ORDER BY received_at ASC 
LIMIT {limit}
```

**Get User Packets**:
```sql
SELECT * FROM prana_packets 
WHERE user_id = {user_id} 
  AND processed_by_karma = {processed_only}
ORDER BY received_at DESC 
LIMIT {limit}
```

**Get Bucket Status**:
```sql
SELECT COUNT(*) FROM prana_packets;
SELECT COUNT(*) FROM prana_packets WHERE processed_by_karma = TRUE;
SELECT COUNT(*) FROM prana_packets WHERE processed_by_karma = FALSE;
```

---

## Data Validation

### Ingestion Validation (Enforced)

**Schema Validation** (`bucket.py` lines 31-80):
- ✅ `timestamp` must be valid ISO-8601
- ✅ `active_seconds`, `idle_seconds`, `away_seconds` must be non-negative
- ✅ Sum of time values must equal 5.0 (±0.1 tolerance)
- ✅ `focus_score` must be 0-100 (if provided)
- ✅ `integrity_score` must be 0-1 (if provided)
- ✅ `raw_signals` must be a valid JSON object
- ✅ Either `cognitive_state` or `state` must be provided

**Rejection Behavior**:
- Invalid packets → HTTP 400 or 422
- Packet discarded (not stored)
- No retry from frontend (fail-open)

---

## Security Observations

### Access Control

**Endpoint Security**: Not observed in code (assumed handled by FastAPI middleware)

**Query Restrictions**:
- No user-based access control in queries
- Any authenticated request can query any user's packets
- **Recommendation**: Add user-based authorization (external to PRANA)

### Data Integrity

**Cryptographic Guarantees**: None observed  
**Tampering Protection**: None observed  
**Audit Trail**: Timestamps only (no signature or hash)

**Implication**: Packets are observational telemetry, not authoritative audit logs

---

## Summary

### Database Structure

**Table**: `prana_packets` (PostgreSQL)  
**Fields**: 20 total (11 metadata, 3 time accounting, 2 scores, 1 JSON signals, 3 processing status)  
**Indexes**: 6 total (1 primary key, 5 query optimization)  
**Growth**: Unbounded (no automatic deletion)

### Data Content

**User Identifiers**: Database IDs only (pseudonymous)  
**Personal Data**: None (no PII)  
**Content Data**: None (aggregate counts only)  
**Behavioral Judgments**: None (observational classifications only)

### Privacy Compliance

✅ **No Content Inspection**: Confirmed  
✅ **No Personal Data**: Confirmed (user_id is pseudonymous)  
✅ **Aggregate Counts Only**: Confirmed  
✅ **No Behavioral Judgment**: Confirmed (states are observational)

### Data Integrity

⚠️ **No Cryptographic Guarantees**: Packets are telemetry, not audit logs  
⚠️ **No Access Control**: Queries not user-restricted (external concern)  
⚠️ **No Retention Policy**: Unbounded growth (external concern)

---

## Recommendations (Documentation Only)

**Note**: These are documentation clarifications, not system changes.

1. **Retention Policy**: Define external retention policy (e.g., 90 days)
2. **Access Control**: Add user-based authorization to query endpoints
3. **Data Minimization**: Consider aggregating old packets to reduce storage
4. **Audit Trail**: Document that packets are telemetry, not audit logs
