# REVIEW_PACKET

## 1. ENTRY POINT

Path: `C:\Users\PC\Desktop\gurukul-backend-\backend\app\main.py`
Explanation: Boots FastAPI, registers Gurukul, Bucket, Karma, and PRANA runtime endpoints.

Path: `C:\Users\PC\Desktop\gurukul-backend-\backend\scripts\run_prana_validation.py`
Explanation: Executes fresh deterministic validation for run `20260328-100052-PRANA` and writes single-run proof artifacts.

## 2. CORE EXECUTION FLOW (ONLY 3 FILES)

Path: `C:\Users\PC\Desktop\gurukul-backend-\backend\app\services\prana_runtime.py`
Explanation: Ingestion, hashing, gap detection, anomaly signals, vitality metrics, replay verification, and append-only violation observation.

Path: `C:\Users\PC\Desktop\gurukul-backend-\backend\app\routers\prana.py`
Explanation: Live PRANA runtime endpoints for ingest, events, vitality, and replay verification.

Path: `C:\Users\PC\Desktop\gurukul-backend-\backend\scripts\run_prana_validation.py`
Explanation: Single-run validator for Gurukul, Bucket, Karma, append-only observation, and artifact generation.

## 3. LIVE FLOW (CRITICAL)

- run_id: `20260328-100052-PRANA`
- validation timestamp: `2026-03-28T10:01:25.559630+05:30`
- live Gurukul summary id: `ac7e09d8-7861-4c65-9fa2-f39478185d35`
- live Gurukul flashcard id: `02dc352b-9a9c-408b-ad1d-1021aa1fb7ab`
- live Bucket packet id: `d312b255-c4a4-4398-af3b-c2ccbb1c955a`
- live Karma submission id: `d2a6b914-e64c-4591-b00e-ca7cd816b47f`
- live PRANA event JSON:
```json
{
  "status": "success",
  "event_id": "304a35d5-06f6-4c04-92eb-1dd8b9eb55bb",
  "submission_id": "probe-20260328-100052-prana",
  "event_type": "task_submit_failed",
  "source_system": "gurukul",
  "payload_hash": "88a8abc35186084e2c97d7ea591cc36c27db099ea0595b2863d931ce3fe391b7",
  "expected_sequence": 26,
  "actual_sequence": 26,
  "gap_detected": false,
  "out_of_order": false,
  "anomaly_count": 1,
  "freshness_status": "fresh",
  "replay_status": "MATCH",
  "logged_at": "2026-03-28T04:31:24.460887"
}
```

- replay verification JSON:
```json
{
  "source_system": "gurukul",
  "status": "VALID",
  "events_verified": 32,
  "matches": 32,
  "mismatches": [],
  "validation_ids": [
    "d6674908-33e8-4a4b-b906-60ec6fc36af4",
    "91e75771-1ac4-4a23-996c-59b0d2a95ca4",
    "00a38855-2a19-483d-b8a2-1c8e2102bc8a",
    "1cfb171c-0551-4dcd-9216-722f1349b2d9",
    "9c01fb56-21c5-44b2-a7c3-0da6889cde49",
    "9c0ef6ab-20c7-4d40-ac20-185f49abb169",
    "13ae33b7-5c2f-4d79-9a7c-98bf56061a5c",
    "6542bd59-cc83-4624-92da-4f96f481298e",
    "126332a2-a2f0-479e-b74e-0ef0437ade12",
    "c913355c-eaa9-4991-82d3-018760c7cff1",
    "a8e26287-23ac-47a2-a227-f87785922904",
    "ad869d48-63cc-4230-b2b0-8dedee69936f",
    "f2de1986-07ce-47cd-b730-f5b9b1b34b86",
    "7147b3ee-5cea-4b14-bad7-63b8b5c7c545",
    "2cfbba40-90b8-4932-a54e-9787b8cc69c3",
    "644a7ebe-4910-46c3-a68e-a2fd797d4e90",
    "eea0cc1e-7ba8-41f7-a01f-a109772f6c0f",
    "310d9dd1-1d44-4de6-b3db-d51a4b193bdd",
    "6b7939eb-c302-4ed2-986c-83807c46aae4",
    "cee1fe05-d6bf-4864-a565-f539158e4177",
    "c9d63e87-6d14-4906-9adb-1a02a571d013",
    "61eca371-bae1-44c5-b39e-3f35ce5104d5",
    "9ae377f9-b8fd-49c2-85c2-77dc745f5cca",
    "41830ec0-6eb3-4a27-92f1-d5a56e6c8e98",
    "b95db861-40df-44ee-a9b0-115e290b2d65",
    "bff2040f-9096-46d9-93b1-c278a1277379",
    "683ba4da-5fcc-48bf-ad4d-f3c5e5f365ee",
    "a90ee1da-6e3e-49cb-846c-da35162f3d8e",
    "b4a9e430-c3ce-4b4a-a308-6e855fc6cd21",
    "dd6cc377-eaf9-43fa-a480-8424c25bccc6",
    "03d2321a-b456-4526-b63d-1ab6cc9e6362",
    "612dc473-cb7a-47ef-b05c-e9b15ab5cdb8"
  ]
}
```

## 4. WHAT WAS BUILT

- Working POST /api/v1/prana/ingest
- Real Gurukul hooks on summary save and flashcard review
- Bucket ingestion telemetry with source_system = Bucket
- Karma truth-classification telemetry with source_system = Karma
- Deterministic SHA-256 hashing with canonical JSON serialization
- Gap detection, out-of-order detection, burst detection, repeated-failure detection
- Replay validation with VALID / INVALID chain checks
- Append-only violation observation in code without database enforcement
- Fresh run-scoped artifacts generated for this run only

## 5. FAILURE CASES

- Missing sequence -> sequence_gap anomaly
- Duplicate sequence -> non-blocking retention
- Out-of-order timestamp -> out_of_order_timestamp anomaly
- Burst events -> threshold-crossing burst_events anomaly
- Repeated failures -> repeated_failures anomaly
- UPDATE / DELETE on prana_integrity_log -> APPEND_ONLY_VIOLATION observed, operation allowed

## 6. PROOF

- Trigger-free DB verification: `[]`
- Gurukul integration proof: summary `ac7e09d8-7861-4c65-9fa2-f39478185d35`, flashcard `02dc352b-9a9c-408b-ad1d-1021aa1fb7ab`
- Bucket validation proof: packet `d312b255-c4a4-4398-af3b-c2ccbb1c955a`, status `VALID`
- Karma validation proof: submission `d2a6b914-e64c-4591-b00e-ca7cd816b47f`, status `VALID`
- Run log: `C:\Users\PC\Desktop\gurukul-backend-\run-logs\prana_validation_20260328-100052-PRANA.log`
- JSON proof: `C:\Users\PC\Desktop\gurukul-backend-\run-logs\prana_validation_report_20260328-100052-PRANA.json`
- Testing report: `C:\Users\PC\Desktop\gurukul-backend-\run-logs\prana_testing_report_20260328-100052-PRANA.md`
- Review packet: `C:\Users\PC\Desktop\gurukul-backend-\run-logs\REVIEW_PACKET_20260328-100052-PRANA.md`