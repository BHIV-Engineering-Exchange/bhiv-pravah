# Failure Simulation Visual Test Guide

## Setup

1. Start backend: `cd backend && npm start`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser: `http://localhost:5173`
4. Open DevTools Console

---

## Test 1: Bad Asset Failure

### Steps
1. Open JSON Config Panel
2. Paste this config:
```json
{
  "schema_version": "1.0",
  "world": { "id": "test_bad_asset", "name": "Test", "gravity": [0, -9.8, 0] },
  "scene": { "id": "scene_test", "ambientLight": [1, 1, 1], "skybox": "default" },
  "entities": [{
    "id": "player_1",
    "type": "player",
    "transform": { "position": [0, 0, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1] },
    "material": { "shader": "basic", "texture": "corrupted_texture.png", "color": [1, 1, 1] },
    "components": { "mesh": "player_mesh", "collider": "box" }
  }],
  "quests": []
}
```
3. Click "Generate World"
4. Watch Job Queue Panel

### Expected UI Behavior
- Job card appears with "QUEUED" status (blue dot)
- Status changes to "DISPATCHED" (blue dot)
- Status changes to "RUNNING" (amber dot)
- After ~3 seconds, status changes to "FAILED" (red dot, pulsing)
- Red error card appears with:
  - Red background gradient
  - ⚠️ Warning icon
  - Error message: "BAD_ASSET: corrupted_texture.png"
  - Timestamp preserved
  - Red border and accent

### Console Output
```
[QUEUE RECEIVED] LOAD_ASSETS
[JOB FAILED] job_xxx: BAD_ASSET: corrupted_texture.png
```

---

## Test 2: Invalid Entity Failure

### Steps
1. Paste this config:
```json
{
  "schema_version": "1.0",
  "world": { "id": "test_invalid", "name": "Test", "gravity": [0, -9.8, 0] },
  "scene": { "id": "scene_test", "ambientLight": [1, 1, 1], "skybox": "default" },
  "entities": [{
    "id": "invalid_entity_999",
    "type": "player",
    "transform": { "position": [0, 0, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1] },
    "material": { "shader": "basic", "color": [1, 1, 1] },
    "components": { "mesh": "player_mesh" }
  }],
  "quests": []
}
```
2. Click "Generate World"
3. Watch Job Queue Panel

### Expected UI Behavior
- SPAWN_ENTITY job appears
- Progresses through states
- Fails with red error card
- Error message: "INVALID_ENTITY: invalid_entity_999"
- Full error visible in expandable section

### Console Output
```
[QUEUE RECEIVED] SPAWN_ENTITY
[JOB FAILED] job_xxx: INVALID_ENTITY: invalid_entity_999
```

---

## Test 3: Missing Transform Failure

### Steps
1. Paste this config:
```json
{
  "schema_version": "1.0",
  "world": { "id": "test_missing", "name": "Test", "gravity": [0, -9.8, 0] },
  "scene": { "id": "scene_test", "ambientLight": [1, 1, 1], "skybox": "default" },
  "entities": [{
    "id": "player_2",
    "type": "player",
    "material": { "shader": "basic", "color": [1, 1, 1] },
    "components": { "mesh": "player_mesh" }
  }],
  "quests": []
}
```
2. Click "Generate World"
3. Watch Job Queue Panel

### Expected UI Behavior
- SPAWN_ENTITY job fails
- Red error card
- Error message: "INVALID_ENTITY: missing transform"
- Validation error clearly visible

### Console Output
```
[QUEUE RECEIVED] SPAWN_ENTITY
[JOB FAILED] job_xxx: INVALID_ENTITY: missing transform
```

---

## Test 4: Demo Mode Recovery

### Steps
1. After any failure above
2. Click "Launch Demo" button in Demo Mode Panel
3. Watch Job Queue Panel

### Expected UI Behavior
- Demo button shows loading state (🔄 Running Demo...)
- Button disabled during execution
- New jobs appear in queue
- All jobs complete successfully (green dots)
- Cube preview updates
- Demo button returns to ready state

### Console Output
```
[QUEUE RECEIVED] BUILD_SCENE
[QUEUE RECEIVED] LOAD_ASSETS
[QUEUE RECEIVED] SPAWN_ENTITY
[JOB COMPLETED] job_xxx
[JOB COMPLETED] job_yyy
[JOB COMPLETED] job_zzz
```

---

## Test 5: Multiple Failures

### Steps
1. Run Test 1 (bad asset)
2. Immediately run Test 2 (invalid entity)
3. Watch Job Queue Panel

### Expected UI Behavior
- Multiple failed jobs visible
- Each with distinct error message
- All errors clearly labeled
- Job history preserved
- Scroll to see all jobs
- Each job card independent

---

## Test 6: Engine Disconnect (Manual)

### Steps
1. Start a world generation
2. While jobs are running, stop the backend server (Ctrl+C)
3. Watch Job Queue Panel

### Expected UI Behavior
- Running jobs fail immediately
- Error message: "ENGINE_DISCONNECTED"
- All active jobs show red error cards
- System remains responsive
- Frontend doesn't crash

### Console Output (Backend)
```
[ENGINE DISCONNECT] Failing job job_xxx
[ENGINE DISCONNECT] Failing job job_yyy
```

### Recovery
1. Restart backend server
2. Frontend reconnects automatically
3. Click "Launch Demo" to verify system working

---

## Visual Checklist

For each failed job, verify:
- [ ] Red background gradient visible
- [ ] ⚠️ Warning icon present
- [ ] Error message in red text
- [ ] Monospace font for error details
- [ ] Red pulsing dot indicator
- [ ] "FAILED" status badge in red
- [ ] Timestamp preserved
- [ ] Error details expandable/readable
- [ ] Hover effects still work
- [ ] Red border and accent visible

---

## Demo Mode Checklist

Verify:
- [ ] "Launch Demo" button visible
- [ ] Button shows loading state when clicked
- [ ] Button disabled during execution
- [ ] Shimmer animation on button
- [ ] Pipeline description visible
- [ ] Random world selected
- [ ] All jobs complete successfully
- [ ] Cube preview updates
- [ ] Button returns to ready state

---

## Error Message Verification

Check each error message is:
- [ ] Clear and actionable
- [ ] Includes specific details (filename, entity ID, etc.)
- [ ] Visible without scrolling
- [ ] Properly formatted
- [ ] Color-coded (red for errors)
- [ ] Monospace font for technical details

---

## System Stability

After all tests, verify:
- [ ] Frontend still responsive
- [ ] No console errors (except expected job failures)
- [ ] Demo mode still works
- [ ] New jobs can be submitted
- [ ] Job history preserved
- [ ] No memory leaks (check DevTools Memory tab)

---

## Screenshots to Capture

1. **Failed Job Card** - showing red error with full details
2. **Multiple Failures** - job queue with several failed jobs
3. **Demo Mode Panel** - showing launch button
4. **Demo Mode Running** - showing loading state
5. **Successful Recovery** - demo jobs completing after failures
6. **Error Details** - close-up of error message formatting

---

## Notes

- All tests should complete within 5 seconds per job
- Error messages should appear immediately on failure
- UI should never freeze or become unresponsive
- Demo mode should always work as fallback
- Page refresh clears client state but preserves server state

---

**Test Duration**: ~5 minutes for all scenarios  
**Expected Result**: All failures handled gracefully with clear UI feedback
