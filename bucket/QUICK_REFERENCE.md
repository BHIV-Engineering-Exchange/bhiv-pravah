# 🚀 Append-Only Storage - Quick Reference

**Version:** 1.0.0  
**Status:** PRODUCTION READY

---

## 📖 TL;DR

Bucket is now an **append-only, tamper-evident artifact ledger**. Artifacts are stored immutably with hash chains for integrity verification.

---

## 🎯 Core Philosophy

> **"Bucket is MEMORY, not DECISION"**

- ✅ Validates **structure**, not **content**
- ✅ Stores artifacts **exactly as produced**
- ✅ **Never** interprets payload data
- ✅ **Never** makes decisions

---

## 🔑 Key Concepts

### 1. Append-Only Storage

```
artifact_log.jsonl
├── artifact_1 (line 1) ← Never modified
├── artifact_2 (line 2) ← Never modified
└── artifact_3 (line 3) ← Never modified
```

**Rule:** Once written, **never changed**.

### 2. Hash Chain

```
A1 (hash=H1, parent=null)
  ↓
A2 (hash=H2, parent=H1)
  ↓
A3 (hash=H3, parent=H2)
```

**Rule:** Each artifact links to previous via `parent_hash`.

### 3. Server-Side Hashing

```
Client sends artifact (no hash)
  ↓
Server computes SHA256
  ↓
Server stores with hash
  ↓
Server returns hash to client
```

**Rule:** **Never trust client hashes**.

---

## 📝 Artifact Structure

### Required Fields

```json
{
  "artifact_id": "unique_id",
  "timestamp_utc": "2025-01-20T10:30:00Z",
  "schema_version": "1.0.0",
  "source_module_id": "your_system",
  "artifact_type": "your_type",
  "parent_hash": "previous_hash",  // null for first
  "payload": {
    "your_data": "..."
  }
}
```

### Validation Rules

| Rule | Description |
|------|-------------|
| **Required fields** | All metadata fields must be present |
| **No unknown fields** | Only allowed envelope fields |
| **Schema version** | Must be "1.0.0" |
| **Payload size** | Max 16MB |
| **Parent hash** | Must match previous artifact |

---

## 🔌 API Endpoints

### Store Artifact

```bash
POST /bucket/artifact

{
  "artifact_id": "A001",
  "timestamp_utc": "2025-01-20T10:30:00Z",
  "schema_version": "1.0.0",
  "source_module_id": "my_system",
  "artifact_type": "analysis",
  "payload": {"data": "..."}
}

# Response
{
  "success": true,
  "artifact_id": "A001",
  "hash": "abc123...",
  "storage_type": "append_only"
}
```

### Get Artifact

```bash
GET /bucket/artifact/A001

# Response
{
  "artifact": {...},
  "storage_type": "append_only",
  "chain_verified": true
}
```

### Validate Chain

```bash
POST /bucket/validate-replay

# Response
{
  "valid": true,
  "artifact_count": 1234,
  "last_hash": "abc123...",
  "message": "Chain integrity validated"
}
```

### Get Chain State

```bash
GET /bucket/chain-state

# Response
{
  "chain_state": {
    "last_hash": "abc123...",
    "artifact_count": 1234
  }
}
```

### Get Storage Stats

```bash
GET /bucket/storage-stats

# Response
{
  "statistics": {
    "artifact_count": 1234,
    "log_file_size_mb": 50.0,
    "schema_version": "1.0.0"
  }
}
```

### Get Certification

```bash
GET /bucket/certification

# Response
{
  "certification": "APPEND_ONLY_ENFORCED",
  "guarantees": {
    "immutability": "...",
    "deterministic_hashes": "...",
    ...
  }
}
```

---

## ✅ Do's and Don'ts

### ✅ DO

- **Store artifacts exactly as produced**
- **Include all required metadata**
- **Use schema version 1.0.0**
- **Keep payload under 16MB**
- **Let server compute hashes**

### ❌ DON'T

- **Don't modify artifacts after storage**
- **Don't trust client-provided hashes**
- **Don't add unknown envelope fields**
- **Don't interpret payload content**
- **Don't make decisions based on data**

---

## 🧪 Testing

### Quick Test

```python
# Store artifact
artifact = {
    "artifact_id": "TEST001",
    "timestamp_utc": "2025-01-20T10:30:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "test",
    "artifact_type": "test",
    "payload": {"test": "data"}
}

response = requests.post(
    "http://localhost:8000/bucket/artifact",
    json=artifact
)

print(response.json())
# {"success": true, "hash": "...", ...}
```

### Run Test Suite

```bash
python test_append_only_storage.py
```

---

## 🚨 Common Errors

### Error: "Missing required field"

**Cause:** Required metadata field missing  
**Fix:** Include all required fields

### Error: "Duplicate artifact_id"

**Cause:** artifact_id already exists  
**Fix:** Use unique artifact_id

### Error: "Invalid parent_hash"

**Cause:** Parent hash doesn't match previous  
**Fix:** Use correct parent hash from chain state

### Error: "Payload size exceeds limit"

**Cause:** Payload > 16MB  
**Fix:** Reduce payload size or split into multiple artifacts

### Error: "Unknown envelope field"

**Cause:** Field not in allowed list  
**Fix:** Remove unknown field

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **APPEND_LOG_STORAGE.md** | Storage architecture |
| **CHAIN_INTEGRITY_ENFORCEMENT.md** | Hash chains |
| **HASH_AUTHORITY_POLICY.md** | Server hashing |
| **DOMAIN_INGESTION_READINESS.md** | AIAIC/Marine ingestion |

---

## 🎯 Use Cases

### AIAIC Satellite Analysis

```json
{
  "artifact_id": "aiaic_sat_001",
  "artifact_type": "satellite_analysis",
  "source_module_id": "aiaic_processor",
  "payload": {
    "satellite_image_analysis": {...}
  }
}
```

### Marine Sensor Telemetry

```json
{
  "artifact_id": "marine_sensor_001",
  "artifact_type": "sensor_telemetry",
  "source_module_id": "marine_gateway",
  "payload": {
    "temperature": 23.5,
    "salinity": 35.2
  }
}
```

### AI Model Predictions

```json
{
  "artifact_id": "ai_prediction_001",
  "artifact_type": "model_prediction",
  "source_module_id": "ml_engine",
  "payload": {
    "prediction_output": {...}
  }
}
```

---

## 🔍 Monitoring

### Health Check

```bash
curl http://localhost:8000/health

# Check append_only_storage status
```

### Chain Validation

```bash
curl -X POST http://localhost:8000/bucket/validate-replay

# Verify chain integrity
```

### Storage Stats

```bash
curl http://localhost:8000/bucket/storage-stats

# Monitor storage growth
```

---

## 🆘 Support

**Documentation:** `docs/` directory  
**Tests:** `test_append_only_storage.py`  
**Bucket Owner:** Ashmit Pandey  
**Status:** PRODUCTION READY

---

## 🎉 Quick Start

```bash
# 1. Start server
python main.py

# 2. Check health
curl http://localhost:8000/health

# 3. Store artifact
curl -X POST http://localhost:8000/bucket/artifact \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_id": "TEST001",
    "timestamp_utc": "2025-01-20T10:30:00Z",
    "schema_version": "1.0.0",
    "source_module_id": "test",
    "artifact_type": "test",
    "payload": {"test": "data"}
  }'

# 4. Validate chain
curl -X POST http://localhost:8000/bucket/validate-replay

# Done! ✅
```

---

**Version:** 1.0.0  
**Certification:** APPEND-ONLY ENFORCED  
**Status:** PRODUCTION READY
