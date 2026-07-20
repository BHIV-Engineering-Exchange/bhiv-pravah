# Intent Compiler Module

**Purpose:** Convert user text into TG Engine Gameplay Contract (Atharva's schema)

---

## Day 1 Deliverables ✅

- ✅ **Day 1a:** `docs/intent_layer_scope.md` - Boundary definition
- ✅ **Day 1b:** `intent_taxonomy.json` - What users can say
- ✅ **Day 1c:** `compiler.js` - Intent → Schema conversion
- ✅ **Day 1d:** `parser.js` - Text → Intent extraction
- ✅ **Day 1e:** `validator.js` - Schema validation

---

## Usage

```javascript
const { textToSchema } = require('./intent-compiler');

const result = textToSchema('Make a fast temple run game with jump');

if (result.success) {
  console.log('Schema:', result.schema);
  // Send result.schema to Atharva's engine
} else {
  console.log('Error:', result.explanation);
}
```

---

## What Users Can Say

### Genres
- **runner**: "temple run", "endless runner", "subway"
- **platformer**: "side scroller", "mario", "platform"
- **arena**: "arena", "battle", "combat"

### Pacing
- **slow**: "slow", "easy", "casual"
- **medium**: "normal", "moderate"
- **fast**: "fast", "quick", "speedy"

### Abilities
- **jump**: "jump", "leap"
- **dash**: "dash", "jetpack", "boost"
- **lane_switch**: "lane switch", "dodge"

### Scoring
- **distance**: "distance", "far"
- **time**: "time", "survive"
- **collection**: "collect", "coins"

### Difficulty
- **easy**: "easy", "simple", "beginner"
- **medium**: "normal", "moderate"
- **hard**: "hard", "challenging"

### Entities
- **obstacles**: "obstacles", "avoid"
- **pickups**: "coins", "collect", "pickups"

---

## Example Outputs

### Input: "Make a fast temple run game with jump and dash"

```json
{
  "meta": {
    "game_title": "Make A Fast Temple",
    "version": "1.0"
  },
  "gameplay": {
    "game_mode": "infinite_runner",
    "movement_axis": "z",
    "global_speed": 8.0,
    "gravity": -9.8,
    "score_metric": "distance"
  },
  "camera": {
    "mode": "follow_third_person",
    "offset": [0, 5, -10],
    "look_at_offset": [0, 0, 0]
  },
  "player": {
    "start_pos": [0, 0, 0],
    "abilities": {
      "jump_force": 5.0,
      "dash_speed": 10.0
    },
    "mesh_id": "cube"
  },
  "entities": []
}
```

---

## Testing

### Quick Test (5 examples)
```bash
cd backend/intent-compiler
node test.js
```

### Interactive Terminal Test
```bash
node test_live.js
```
Type your own prompts, see results in real-time.

### Browser Test (Best for Demo)
```bash
node test_server.js
```
Then open: http://localhost:3001

### Validation Tests
```bash
node test_validation.js
```
Tests all validation rules, edge cases, determinism.

### Error Handling Tests
```bash
node test_errors.js
```
Tests invalid schemas and error messages.

### Run ALL Tests
```bash
node test_all.js
```
Runs complete Day 1 test suite.

---

## Files

```
intent-compiler/
├── index.js              # Main entry point
├── parser.js             # Text → Intent
├── compiler.js           # Intent → Schema
├── validator.js          # Schema validation
├── intent_taxonomy.json  # Supported features
├── test.js               # Test suite
├── docs/
│   └── intent_layer_scope.md
└── README.md
```

---

## Next Steps (Day 2)

- [ ] Integrate into dashboard UI
- [ ] Add consistency tests
- [ ] Create demo prompts
- [ ] Test with Atharva's engine
- [ ] Abuse testing

---

**Status:** Day 1 Complete ✅
