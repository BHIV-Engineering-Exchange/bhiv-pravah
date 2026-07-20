# Testing Guide - Engine Adapter Integration

## ✅ Unit Tests Passed

Run: `node backend/engine/test_adapter.js`

All 3 conversion paths work:
- Legacy cube → Engine schema
- LLM output → Engine schema  
- Valid schema → Pass through

---

## 🧪 Manual Testing Steps

### 1. Start Backend
```bash
cd backend
npm start
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Test Legacy Cube (via JsonConfigPanel)

**In Dashboard:**
1. Go to "JSON Config Panel"
2. Enter:
```json
{
  "color": "#ff6b6b",
  "size": 2
}
```
3. Click "Generate World"
4. **Expected:** Cube preview updates with red color, size 2

**What happens internally:**
- Adapter converts `{color, size}` → full engine schema
- Jobs created: BUILD_SCENE, LOAD_ASSETS, SPAWN_ENTITY
- `world_update` event sent with engine schema
- CubePreview reads `entities[0].material.color` and `entities[0].transform.scale`

---

### 4. Test LLM Output (Python → Node)

**Option A: Mock LLM data in JsonConfigPanel**
```json
{
  "metadata": {
    "level_name": "Test World",
    "difficulty": "easy",
    "theme": "forest"
  },
  "environment": {
    "type": "forest",
    "lighting": "dappled_sunlight",
    "terrain": ["grass"],
    "weather": "clear"
  },
  "npcs": [
    {
      "id": "npc_1",
      "name": "Friendly NPC",
      "role": "guide",
      "type": "friendly",
      "location": "village_center",
      "behavior": "stationary",
      "stats": {"health": 100, "attack": 0, "defense": 10}
    }
  ],
  "quests": [
    {
      "id": "quest_1",
      "name": "Test Quest",
      "objective": "Complete test",
      "requirements": []
    }
  ],
  "physics": {},
  "win_conditions": [],
  "lose_conditions": [],
  "assets_required": {}
}
```

**Expected:**
- Adapter converts to engine schema
- World name: "Test World"
- 2 entities: player_1 + npc_1
- 1 quest
- Jobs queued and processed

---

### 5. Test Engine Schema (Already Valid)

**In JsonConfigPanel:**
```json
{
  "schema_version": "1.0",
  "world": {
    "id": "world_custom",
    "name": "Custom World",
    "gravity": [0, -9.8, 0]
  },
  "scene": {
    "id": "scene_custom",
    "ambientLight": [0.8, 0.9, 1],
    "skybox": "custom_sky"
  },
  "entities": [
    {
      "id": "cube_custom",
      "type": "object",
      "transform": {
        "position": [0, 0, 0],
        "rotation": [0, 0, 0],
        "scale": [3, 3, 3]
      },
      "material": {
        "shader": "standard",
        "texture": "none",
        "color": [1, 0.5, 0]
      },
      "components": {
        "mesh": "cube",
        "collider": "box",
        "script": ""
      }
    }
  ],
  "quests": []
}
```

**Expected:**
- Passes through adapter unchanged
- Cube preview shows orange cube, size 3

---

## 🔍 Debugging

### Check Backend Logs
```
[ENGINE SCHEMA VALIDATED]
[QUEUE RECEIVED] BUILD_SCENE
[QUEUE RECEIVED] LOAD_ASSETS
[QUEUE RECEIVED] SPAWN_ENTITY
```

### Check Browser Console
```javascript
// Should see world_update event
socket.on('world_update', (data) => {
  console.log('Engine Schema:', data);
});
```

### Check Job Queue Panel
- Jobs should show: BUILD_SCENE → LOAD_ASSETS → SPAWN_ENTITY
- All should complete successfully

---

## ❌ Common Issues

### Issue: "Unknown input format"
**Cause:** Input doesn't match any format (cube, LLM, schema)
**Fix:** Check JSON structure matches one of the 3 formats

### Issue: Cube doesn't update
**Cause:** `world_update` event not received
**Fix:** Check socket.js emits `world_update` after SPAWN_ENTITY finishes

### Issue: Validation fails
**Cause:** Adapter output doesn't match frozen schema
**Fix:** Check `engine_schema.schema.json` constraints

---

## ✅ Success Criteria

- [ ] Legacy cube converts and displays
- [ ] LLM output converts and creates jobs
- [ ] Valid schema passes through
- [ ] CubePreview updates on world_update
- [ ] Job queue shows all 3 job types
- [ ] No validation errors in backend logs

---

## 🚀 Next Steps (Day 2)

Once testing passes:
- Add `dispatched` and `running` states to job lifecycle
- Implement state machine validation
- Add engine socket bidirectional messaging
