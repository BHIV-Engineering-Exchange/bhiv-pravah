# Frontend Test Payloads

Copy-paste these into the JSON Config Panel to test the adapter.

---

## Test 1: Legacy Cube (Simple)
```json
{"color": "#ff0000", "size": 2}
```
**Expected:** Red cube, size 2

---

## Test 2: Legacy Cube (Different Color)
```json
{"color": "#00ff00", "size": 1.5}
```
**Expected:** Green cube, size 1.5

---

## Test 3: LLM Output (Forest Level)
```json
{
  "metadata": {
    "level_name": "Dark Forest",
    "difficulty": "medium",
    "theme": "forest"
  },
  "environment": {
    "type": "forest",
    "lighting": "filtered_sunlight",
    "terrain": ["grass", "dirt"],
    "weather": "clear"
  },
  "npcs": [
    {
      "id": "wolf_1",
      "name": "Wolf",
      "role": "enemy",
      "type": "hostile",
      "location": "dark_forest",
      "behavior": "aggressive",
      "stats": {"health": 80, "attack": 25, "defense": 15}
    }
  ],
  "quests": [
    {
      "id": "quest_1",
      "name": "Defeat Wolf",
      "objective": "Defeat the wolf",
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
- Jobs: BUILD_SCENE, LOAD_ASSETS, SPAWN_ENTITY
- 2 entities (player + wolf)
- 1 quest

---

## Test 4: LLM Output (Desert Level)
```json
{
  "metadata": {
    "level_name": "Desert Temple",
    "difficulty": "hard",
    "theme": "desert"
  },
  "environment": {
    "type": "desert",
    "lighting": "harsh_sunlight",
    "terrain": ["sand"],
    "weather": "clear"
  },
  "npcs": [
    {
      "id": "merchant_1",
      "name": "Merchant",
      "role": "trader",
      "type": "friendly",
      "location": "temple",
      "behavior": "stationary",
      "stats": {"health": 100, "attack": 0, "defense": 10}
    }
  ],
  "quests": [
    {
      "id": "quest_1",
      "name": "Find Treasure",
      "objective": "Find the hidden treasure",
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
- Scene: desert_sky, harsh sunlight
- 2 entities (player + merchant)

---

## Test 5: Engine Schema (Already Valid)
```json
{
  "schema_version": "1.0",
  "world": {
    "id": "world_test",
    "name": "Test World",
    "gravity": [0, -9.8, 0]
  },
  "scene": {
    "id": "scene_test",
    "ambientLight": [1, 0.5, 0.5],
    "skybox": "test_sky"
  },
  "entities": [
    {
      "id": "cube_test",
      "type": "object",
      "transform": {
        "position": [0, 0, 0],
        "rotation": [0, 0, 0],
        "scale": [2.5, 2.5, 2.5]
      },
      "material": {
        "shader": "standard",
        "texture": "none",
        "color": [0, 0.5, 1]
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
**Expected:** Blue cube, size 2.5

---

## How to Test

1. Start backend: `cd backend && npm start`
2. Start frontend: `cd frontend && npm run dev`
3. Open dashboard in browser
4. Find "Cube Config (JSON)" panel
5. Copy one of the payloads above
6. Paste into textarea
7. Click "Generate World"
8. Watch:
   - Job Queue Panel (shows jobs)
   - Cube Preview (updates)
   - Browser console (shows world_update event)

---

## What to Check

### Backend Console
```
[ENGINE SCHEMA VALIDATED]
[QUEUE RECEIVED] BUILD_SCENE
[QUEUE RECEIVED] LOAD_ASSETS
[QUEUE RECEIVED] SPAWN_ENTITY
```

### Browser Console
```javascript
// Open DevTools → Console
// Should see:
world_update event with full engine schema
```

### Job Queue Panel
- Should show 3 jobs for LLM/schema inputs
- All should complete successfully

### Cube Preview
- Should update with correct color/size
- For LLM inputs: uses first entity's material/transform

---

## Troubleshooting

**Cube doesn't update:**
- Check browser console for `world_update` event
- Check backend logs for validation errors

**Jobs fail:**
- Check error message in Job Queue Panel
- Verify JSON is valid (no syntax errors)

**"Unknown input format" error:**
- JSON doesn't match any of the 3 formats
- Check structure matches examples above
