# Atharva Sync Checklist - Engine Integration

**Date:** 2025-02-05  
**Purpose:** Confirm field-level compatibility between Micro-Bridge and TG Engine

---

## Pre-Sync Preparation

- [x] Created `docs/engine_adapter.md` with proposed contract
- [ ] Reviewed with Atharva
- [ ] Documented agreed changes below

---

## Critical Questions

### 1. Field Naming Convention

**Question:** Are you using snake_case or camelCase?

- [ ] **snake_case** (e.g., `job_id`, `world_spec`, `submitted_at`)
- [ ] **camelCase** (e.g., `jobId`, `worldSpec`, `submittedAt`)
- [ ] **Mixed** (specify which fields use which convention)

**Agreed Format:** _____________

---

### 2. Socket Event Names

**Question:** What event names does your engine listen for and emit?

**Outbound (Backend → Engine):**
- [ ] `engine_job` ← Proposed
- [ ] Other: _____________

**Inbound (Engine → Backend):**
- [ ] `engine_ready` ← Proposed
- [ ] `engine_heartbeat` ← Proposed
- [ ] `job_started` ← Proposed
- [ ] `job_progress` ← Proposed
- [ ] `job_completed` ← Proposed
- [ ] `job_failed` ← Proposed
- [ ] Other: _____________

**Agreed Events:** _____________

---

### 3. Job Data Structure

**Question:** What data do you need with each job?

- [ ] Full `world_spec` object (complete world definition)
- [ ] Job-specific `payload` only (extracted data)
- [ ] Both `world_spec` and `payload`
- [ ] Other: _____________

**Agreed Structure:** _____________

---

### 4. Job Execution Model

**Question:** How does your engine process jobs?

- [ ] Sequential (one job at a time)
- [ ] Concurrent (multiple jobs in parallel)
- [ ] Batched (group of jobs together)

**Max Concurrent Jobs:** _____________

**Agreed Model:** _____________

---

### 5. Job Types

**Question:** Do you support all 3 job types?

- [ ] `BUILD_SCENE` - Create scene environment
- [ ] `LOAD_ASSETS` - Load meshes/textures
- [ ] `SPAWN_ENTITY` - Instantiate entities

**Alternative:** Should we send one combined job instead?
- [ ] Yes, send combined job
- [ ] No, send separate jobs

**Agreed Types:** _____________

---

### 6. Telemetry Events

**Question:** What status updates will you send?

- [ ] `job_started` - When execution begins
- [ ] `job_progress` - Progress updates (0-100)
- [ ] `job_completed` - Successful completion
- [ ] `job_failed` - Error occurred

**Progress Update Frequency:** _____________

**Agreed Telemetry:** _____________

---

### 7. Error Codes

**Question:** What error codes will you emit?

Proposed:
- [ ] `ASSET_NOT_FOUND` - Missing asset
- [ ] `INVALID_ENTITY` - Malformed entity data
- [ ] `SCENE_BUILD_FAILED` - Scene creation error
- [ ] `TIMEOUT` - Job exceeded timeout
- [ ] `ENGINE_ERROR` - Internal error

**Additional Codes:** _____________

**Agreed Codes:** _____________

---

### 8. Timeout Handling

**Question:** What timeout should we use?

- [ ] 5 minutes (300000 ms) ← Proposed
- [ ] Other: _____________ ms

**Who handles timeout?**
- [ ] Backend (we cancel job after timeout)
- [ ] Engine (you cancel and send `job_failed`)
- [ ] Both (redundant safety)

**Agreed Timeout:** _____________

---

### 9. Connection Details

**Question:** How does the engine connect?

**Connection Direction:**
- [ ] Engine connects to backend at `ws://localhost:3000/engine`
- [ ] Backend connects to engine at: _____________

**Authentication:**
- [ ] JWT in handshake `auth.token`
- [ ] Other: _____________

**JWT Issuer:**
- [ ] `sovereign-core` ← Current
- [ ] Other: _____________

**Agreed Connection:** _____________

---

### 10. World Spec Format

**Question:** Is the frozen schema v1.0 compatible?

- [ ] Yes, schema is compatible as-is
- [ ] No, need changes (specify below)

**Required Changes:**
_____________________________________________
_____________________________________________

**Agreed Schema:** _____________

---

## Data Type Confirmations

### Colors
- [ ] RGB arrays [0-1] floats (e.g., `[0.4, 0.6, 0.4]`)
- [ ] RGB arrays [0-255] integers
- [ ] Hex strings (e.g., `"#66AA66"`)

**Agreed:** _____________

### Positions/Vectors
- [ ] Arrays [x, y, z] floats (e.g., `[0, 0, 0]`)
- [ ] Objects `{ x, y, z }`

**Agreed:** _____________

### Timestamps
- [ ] Unix timestamp milliseconds (e.g., `1738425600000`)
- [ ] Unix timestamp seconds
- [ ] ISO 8601 strings

**Agreed:** _____________

---

## Security Confirmations

### Message Signing
- [ ] `job_status` messages require HMAC signature
- [ ] No signing required
- [ ] Other: _____________

**Shared Secret:** (coordinate separately)

**Agreed:** _____________

### Heartbeat
- [ ] 5 second interval, 10 second timeout ← Current
- [ ] Other interval: _____________

**Agreed:** _____________

---

## Post-Sync Actions

After sync, update:
- [ ] `docs/engine_adapter.md` with agreed changes
- [ ] `backend/engine/engine_adapter.js` implementation
- [ ] `backend/engine/engine_socket.js` event handlers
- [ ] Test with mock engine client

---

## Notes

_____________________________________________
_____________________________________________
_____________________________________________
_____________________________________________

---

## Sign-Off

**Micro-Bridge Team:** _____________  
**TG Engine Team (Atharva):** _____________  
**Date:** _____________

**Status:** 
- [ ] Sync Complete
- [ ] Pending Changes
- [ ] Blocked (specify reason)
