# DELIVERABLE 3: BHIV_EVENT_SCHEMA_ALIGNMENT_REPORT.md

## 1. Unified Event Schema Structure
All systems MUST encapsulate data using the following top-level wrapper:

```json
{
  "registry_reference": "string (URI format)",
  "event_type": "string (uppercase enumeration)",
  "truth_classification": "integer (0-4)",
  "source_system": "string (system_id)",
  "deterministic_payload_hash": "string (SHA-256)",
  "timestamp": "integer (Unix Epoch - immutable event generation time)",
  "payload": "object (schema defined by registry_reference)"
}
```

## 2. Field Definitions & Validation Rules
- `registry_reference`: Must strictly match a URI defined in the Canonical Registry (e.g., `registry://bhiv/schema_task_sub/v1.1`).
- `event_type`: Must evaluate against the allowed events assigned to that schema.
- `truth_classification`: Bounded strictly to integers 0 through 4.
- `source_system`: Must map exactly to a registered `system_id`.
- `deterministic_payload_hash`: An SHA-256 hash of the strictly alphabetized and stringified `payload` object. Time-based metadata must NOT be included inside `payload` to ensure reproducible hashing.
- `timestamp`: Event origination time. Replays MUST reuse the historical timestamp.
- `payload`: The business-logic specific object mapping to the referenced contract.

## 3. Example Event (Gurukul Backend)
```json
{
  "registry_reference": "registry://gurukul/task/v1.0.0",
  "event_type": "SCHEMA_TASK_SUBMITTED_V1",
  "truth_classification": 1,
  "source_system": "sys_gurukul_01",
  "deterministic_payload_hash": "a4d3b6...8f9e",
  "timestamp": 1710661200,
  "payload": {
    "student_id": "STU_8891",
    "task_id": "TSK_01",
    "status": "COMPLETED"
  }
}
```
