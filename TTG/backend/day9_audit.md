# Day 9 - Demo-Only Execution Paths Audit

## Backend Demo Paths to Remove

### 1. Socket.IO `generate_world` Event Handler
**File**: `backend/socket.js`
**Lines**: ~240-380
**Purpose**: Direct world generation from UI without core ingestion
**Action**: Remove entire event handler

### 2. TTG Routes (Text-to-Game)
**File**: `backend/routes/ttgRoutes.js`
**Routes**:
- POST `/api/intent/compile` - Compiles text to schema
- POST `/api/intent/start-game` - Starts game directly from text
- GET `/api/intent/features` - Lists supported features

**Action**: Remove `/start-game` route (bypasses core ingestion)
**Keep**: `/compile` and `/features` (read-only, no execution)

### 3. Index.js Route Registration
**File**: `backend/index.js`
**Line**: `app.use("/api/intent", ttgRoutes);`
**Action**: Keep registration but remove start-game route from ttgRoutes

## Frontend Demo Paths to Remove

### 1. JsonConfigPanel - Generate World Button
**File**: `frontend/src/components/JsonConfigPanel.jsx`
**Function**: `handleGenerate()` - Emits `generate_world` socket event
**Action**: Remove generate button and handler

### 2. IntentInputPanel - Dispatch to Engine Button
**File**: `frontend/src/components/IntentInputPanel.jsx`
**Function**: `handleSendToEngine()` - Calls `/api/intent/start-game`
**Action**: Remove dispatch button and handler

## Execution Flow After Cleanup

### BEFORE (Multiple Paths)
```
UI → generate_world socket event → Job Queue → Engine
UI → /api/intent/start-game → Job Queue → Engine
UI → JsonConfigPanel → generate_world → Engine
Core → /core/execute → Dispatcher → Job Queue → Engine
```

### AFTER (Single Path)
```
Prompt Runner → /core/execute → Dispatcher → Job Queue → Engine
```

## Files to Modify

1. `backend/socket.js` - Remove generate_world handler
2. `backend/routes/ttgRoutes.js` - Remove start-game route
3. `frontend/src/components/JsonConfigPanel.jsx` - Remove generate button
4. `frontend/src/components/IntentInputPanel.jsx` - Remove dispatch button

## What to Keep

### Backend
- ✅ `/core/execute` endpoint (ONLY execution path)
- ✅ `/api/intent/compile` (read-only schema compilation)
- ✅ `/api/intent/features` (read-only feature list)
- ✅ Job queue system
- ✅ Engine socket handlers

### Frontend
- ✅ Schema preview/compilation UI
- ✅ Job queue monitoring
- ✅ Engine status display
- ✅ Cube preview (visual only)

## Security Impact

Removing demo paths ensures:
- All executions go through security enforcement layer
- Signature/nonce validation cannot be bypassed
- Trace ID tracking is mandatory
- Audit trail is complete
