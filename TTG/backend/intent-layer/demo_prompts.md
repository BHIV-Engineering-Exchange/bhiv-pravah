## Demo Prompt 1: Classic Runner

**Prompt:**
```
Make a fast runner with jump and obstacles
```

**Expected Output:**
```json
{
  "game_mode": "runner",
  "movement": { "speed": 8, "jump_height": 5 },
  "camera": { "type": "third_person", "distance": 10 },
  "spawn_rules": { "obstacles": 2, "frequency": 2 },
  "score_rules": { "distance": 1, "collectibles": 0 },
  "end_conditions": ["collision"],
  "player_params": { "jetpack": false, "health": 3 },
  "world_params": { "gravity": -9.8, "theme": "default" }
}
```

**Why It Works:**
- Clear game mode (runner)
- Fast pacing (speed: 8)
- Jump ability included
- Obstacles enabled
- Distance-based scoring

---

## Demo Prompt 2: Jetpack Runner

**Prompt:**
```
Make temple run with jetpack and score
```

**Expected Output:**
```json
{
  "game_mode": "runner",
  "movement": { "speed": 5 },
  "camera": { "type": "third_person", "distance": 10 },
  "spawn_rules": { "obstacles": 0, "frequency": 2 },
  "score_rules": { "distance": 1, "collectibles": 0 },
  "end_conditions": ["collision"],
  "player_params": { "jetpack": true, "health": 3 },
  "world_params": { "gravity": -9.8, "theme": "default" }
}
```

**Why It Works:**
- Jetpack ability enabled
- Score-based gameplay
- Medium speed (default)
- No obstacles (focus on flying)

---

## Demo Prompt 3: Easy Platformer

**Prompt:**
```
Create an easy platform jump game
```

**Expected Output:**
```json
{
  "game_mode": "sidescroller",
  "movement": { "speed": 5, "jump_height": 5 },
  "camera": { "type": "side_view", "distance": 10 },
  "spawn_rules": { "obstacles": 0, "frequency": 3 },
  "score_rules": { "distance": 1, "collectibles": 0 },
  "end_conditions": ["collision"],
  "player_params": { "jetpack": false, "health": 5 },
  "world_params": { "gravity": -9.8, "theme": "default" }
}
```

**Why It Works:**
- Sidescroller mode
- Side view camera
- Easy difficulty (health: 5)
- Jump ability
- Slower spawn rate

---

## Demo Prompt 4: Collection Game

**Prompt:**
```
Runner with collectibles and coins
```

**Expected Output:**
```json
{
  "game_mode": "runner",
  "movement": { "speed": 5 },
  "camera": { "type": "third_person", "distance": 10 },
  "spawn_rules": { "obstacles": 0, "frequency": 2 },
  "score_rules": { "distance": 0, "collectibles": 10 },
  "end_conditions": ["collision"],
  "player_params": { "jetpack": false, "health": 3 },
  "world_params": { "gravity": -9.8, "theme": "default" }
}
```

**Why It Works:**
- Collection-based scoring
- No distance points
- Focus on pickups
- Medium difficulty

---

## Demo Prompt 5: Hard Challenge

**Prompt:**
```
Hard fast runner with obstacles to dodge
```

**Expected Output:**
```json
{
  "game_mode": "runner",
  "movement": { "speed": 8 },
  "camera": { "type": "third_person", "distance": 10 },
  "spawn_rules": { "obstacles": 2, "frequency": 1.5 },
  "score_rules": { "distance": 1, "collectibles": 0 },
  "end_conditions": ["collision"],
  "player_params": { "jetpack": false, "health": 1 },
  "world_params": { "gravity": -9.8, "theme": "default" }
}
```

**Why It Works:**
- Hard difficulty (health: 1)
- Fast speed (8)
- Frequent obstacles (1.5s)
- High challenge level

---

## Testing Results

All 5 prompts tested with:
```bash
cd backend/intent-compiler
node test_intentCompiler.js
```

### Validation Checklist

| Prompt | Compiles | Valid Schema | Deterministic | Playable |
|--------|----------|--------------|---------------|----------|
| Demo 1 | ✅ | ✅ | ✅ | ✅ |
| Demo 2 | ✅ | ✅ | ✅ | ✅ |
| Demo 3 | ✅ | ✅ | ✅ | ✅ |
| Demo 4 | ✅ | ✅ | ✅ | ✅ |
| Demo 5 | ✅ | ✅ | ✅ | ✅ |

---

## Usage in Dashboard

These prompts can be pre-loaded as "Quick Examples":

```javascript
const examplePrompts = [
  "Make a fast runner with jump and obstacles",
  "Make temple run with jetpack and score",
  "Create an easy platform jump game",
  "Runner with collectibles and coins",
  "Hard fast runner with obstacles to dodge"
];
```

---

## Engine Compatibility

All prompts produce schemas matching engine_contract_schema.json:

```json
{
  "game_mode": "runner" | "sidescroller",
  "movement": { "speed": 1-15, "jump_height": 0-10 },
  "camera": { "type": "third_person" | "side_view" | "top_down", "distance": 5-20 },
  "spawn_rules": { "obstacles": 0-10, "frequency": 0.5-10 },
  "score_rules": { "distance": 0+, "collectibles": 0+ },
  "end_conditions": ["collision", "time_limit", "distance_goal", "score_goal"],
  "player_params": { "jetpack": boolean, "health": 1-100 },
  "world_params": { "gravity": number, "theme": string }
}
```

---

## Demo Flow

1. User enters/selects prompt
2. intentCompiler.compile() processes text
3. JSON contract generated
4. Validator checks schema (optional)
5. Contract sent to engine
6. Game starts

---

## Safety Features

✅ All prompts use supported features only  
✅ No unsupported keywords (enemies, weapons, multiplayer, powerups)  
✅ Deterministic output (same prompt = same schema)  
✅ Valid enum values only (runner/sidescroller)  
✅ Required fields always present  
✅ Bounded values (speed: 1-15, health: 1-100)  
✅ No hallucinated fields  

---

## Customization Guide

Users can modify these prompts:

**Change Speed:**
- "fast" (8) → "slow" (3) or "medium" (5)

**Change Difficulty:**
- "easy" (health: 5, freq: 3) → "medium" (health: 3, freq: 2) → "hard" (health: 1, freq: 1.5)

**Add/Remove Abilities:**
- Add: "with jump", "with jetpack"
- Remove: omit ability keywords

**Add/Remove Features:**
- Add: "with obstacles", "with collectibles", "with score"
- Remove: omit feature keywords

**Change Game Mode:**
- "runner" → "platform" or "sidescroller"

---


