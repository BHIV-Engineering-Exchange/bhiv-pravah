# Consequence Rules Documentation

## Overview

The Consequence Rules system defines deterministic mappings from runtime events to engine actions. Each rule specifies:
- **Event type** (on) - What event triggers the rule
- **Condition** (if) - What conditions must be met
- **Actions** (then) - What actions to execute

## Rule Structure

### Basic Format

```json
{
  "rule_id": "collision_player_obstacle",
  "on": "collision",
  "if": {
    "condition": "player_hits_obstacle",
    "entities": ["player", "obstacle"],
    "context_checks": {
      "entity_type": "obstacle"
    }
  },
  "then": [
    {
      "action": "END_GAME",
      "priority": "critical",
      "payload": {
        "reason": "collision_with_obstacle",
        "show_game_over": true
      }
    }
  ],
  "description": "End game when player collides with obstacle"
}
```

### Required Fields

- **rule_id** (string): Unique identifier for the rule
- **on** (string): Event type that triggers this rule
- **if** (object): Condition that must be met
  - **condition** (string): Condition name
  - **entities** (array, optional): Required entities
  - **context_checks** (object, optional): Context validation
- **then** (array): Actions to execute
  - **action** (string): Action name
  - **priority** (string): Priority level (critical/high/medium/low)
  - **payload** (object): Action parameters
- **description** (string, optional): Human-readable description

## Supported Event Types

### Required Events (Task Specification)

1. **collision** - Entity collision events
2. **entity_destroyed** - Entity destruction (enemy_killed)
3. **pickup_collected** - Item collection events
4. **timer_expired** - Timer expiration events

### Additional Events

5. **player_death** - Player death events
6. **score_update** - Score change events
7. **level_complete** - Level completion events
8. **health_changed** - Health modification events
9. **entity_spawned** - Entity spawn events
10. **game_start** - Game start events
11. **game_end** - Game end events
12. **position_update** - Position change events

## Priority Levels

| Priority | Value | Description | Use Case |
|----------|-------|-------------|----------|
| critical | 1 | Must be processed immediately | Game end, player death |
| high | 2 | Should be processed quickly | Damage, health checks |
| medium | 3 | Normal priority, can be queued | Score updates, spawning |
| low | 4 | Can be delayed or batched | Sound effects, visual effects |

## Rule Examples

### 1. Collision Rules

#### Player Hits Obstacle
```json
{
  "rule_id": "collision_player_obstacle",
  "on": "collision",
  "if": {
    "condition": "player_hits_obstacle",
    "entities": ["player", "obstacle"],
    "context_checks": {
      "entity_type": "obstacle"
    }
  },
  "then": [
    {
      "action": "END_GAME",
      "priority": "critical",
      "payload": {
        "reason": "collision_with_obstacle",
        "show_game_over": true
      }
    }
  ]
}
```

#### Player Hits Enemy
```json
{
  "rule_id": "collision_player_enemy",
  "on": "collision",
  "if": {
    "condition": "player_hits_enemy",
    "entities": ["player", "enemy"],
    "context_checks": {
      "entity_type": "enemy"
    }
  },
  "then": [
    {
      "action": "DAMAGE_PLAYER",
      "priority": "high",
      "payload": { "damage": 1 }
    },
    {
      "action": "CHECK_PLAYER_HEALTH",
      "priority": "high",
      "payload": {}
    }
  ]
}
```

### 2. Enemy Killed Rule

```json
{
  "rule_id": "enemy_killed",
  "on": "entity_destroyed",
  "if": {
    "condition": "enemy_killed",
    "context_checks": {
      "entity_type": "enemy"
    }
  },
  "then": [
    {
      "action": "UPDATE_SCORE",
      "priority": "medium",
      "payload": {
        "score_delta": 100,
        "reason": "enemy_killed"
      }
    },
    {
      "action": "SPAWN_ENTITY",
      "priority": "low",
      "payload": {
        "entity_type": "enemy",
        "delay": 2000
      }
    }
  ]
}
```

### 3. Pickup Collected Rules

#### Coin Collection
```json
{
  "rule_id": "pickup_collected_coin",
  "on": "pickup_collected",
  "if": {
    "condition": "coin_collected",
    "context_checks": {
      "entity_type": "collectible"
    }
  },
  "then": [
    {
      "action": "UPDATE_SCORE",
      "priority": "medium",
      "payload": {
        "score_delta": 10,
        "reason": "coin_collected"
      }
    },
    {
      "action": "SPAWN_ENTITY",
      "priority": "low",
      "payload": {
        "entity_type": "collectible",
        "delay": 1000
      }
    }
  ]
}
```

### 4. Timer Expired Rules

#### Game Over
```json
{
  "rule_id": "timer_expired_game_over",
  "on": "timer_expired",
  "if": {
    "condition": "game_timer_expired",
    "context_checks": {
      "timer_value": 0
    }
  },
  "then": [
    {
      "action": "END_GAME",
      "priority": "critical",
      "payload": {
        "reason": "time_up",
        "show_game_over": true,
        "show_final_score": true
      }
    }
  ]
}
```

## Action Definitions

### Core Actions

| Action | Description | Required Payload | Optional Payload |
|--------|-------------|------------------|------------------|
| END_GAME | Terminate game session | reason | show_game_over, show_final_score |
| UPDATE_SCORE | Update player score | score_delta | reason |
| SPAWN_ENTITY | Spawn new entity | entity_type | delay, position |
| DAMAGE_PLAYER | Apply damage to player | damage | - |
| CHECK_PLAYER_HEALTH | Check if health depleted | - | - |
| PLAY_SOUND | Play sound effect | sound_id | - |

### Advanced Actions

| Action | Description | Required Payload | Optional Payload |
|--------|-------------|------------------|------------------|
| APPLY_POWERUP | Apply powerup effect | powerup_type | duration |
| INCREASE_DIFFICULTY | Increase difficulty | difficulty_level | - |
| RESPAWN_PLAYER | Respawn player | - | delay, invincibility_duration |
| LOAD_NEXT_LEVEL | Load next level | - | delay |

## API Reference

### Load Rules

```javascript
const { loadConsequenceRules } = require('./consequence/ruleValidator');

const rules = loadConsequenceRules();
```

### Validate Rules

```javascript
const { validateAllRules } = require('./consequence/ruleValidator');

const validation = validateAllRules(rules);
if (!validation.valid) {
  console.error('Invalid rules:', validation.errors);
}
```

### Get Rules for Event

```javascript
const { getRulesForEvent } = require('./consequence/ruleValidator');

const collisionRules = getRulesForEvent(rules, 'collision');
```

### Get Rule by ID

```javascript
const { getRuleById } = require('./consequence/ruleValidator');

const rule = getRuleById(rules, 'collision_player_obstacle');
```

### Sort Actions by Priority

```javascript
const { sortActionsByPriority } = require('./consequence/ruleValidator');

const sortedActions = sortActionsByPriority(rule.then);
// Returns actions ordered by priority (critical first)
```

## Rule Matching Logic

### Step 1: Event Type Match
```javascript
// Match event type
const matchingRules = rules.filter(rule => rule.on === event.event_type);
```

### Step 2: Entity Match
```javascript
// Check if required entities are present
const entityMatch = rule.if.entities.every(entity => 
  event.entities.includes(entity)
);
```

### Step 3: Context Check
```javascript
// Validate context conditions
const contextMatch = Object.entries(rule.if.context_checks).every(
  ([key, value]) => event.context[key] === value
);
```

### Step 4: Execute Actions
```javascript
// Sort by priority and execute
const sortedActions = sortActionsByPriority(rule.then);
sortedActions.forEach(action => {
  executeAction(action);
});
```

## Testing

Run the test suite:

```bash
cd backend
node test_consequence_rules.js
```

Expected output:
- ✅ Rules loaded successfully
- ✅ All rules are valid
- ✅ No duplicate rule IDs
- ✅ All required event types covered
- ✅ Rule matching works correctly

## Statistics

Current rule set:
- **Total rules:** 13
- **Total actions:** 26
- **Unique actions:** 19
- **Collision rules:** 3
- **Entity destroyed rules:** 1
- **Pickup collected rules:** 2
- **Timer expired rules:** 2

## Adding New Rules

### Step 1: Define the Rule

```json
{
  "rule_id": "new_rule_name",
  "on": "event_type",
  "if": {
    "condition": "condition_name",
    "entities": ["entity1", "entity2"],
    "context_checks": {
      "field": "value"
    }
  },
  "then": [
    {
      "action": "ACTION_NAME",
      "priority": "medium",
      "payload": {
        "param": "value"
      }
    }
  ],
  "description": "What this rule does"
}
```

### Step 2: Add Action Definition (if new)

```json
"ACTION_NAME": {
  "description": "What the action does",
  "job_type": "JOB_TYPE",
  "required_payload": ["param1"],
  "optional_payload": ["param2"]
}
```

### Step 3: Validate

```bash
node test_consequence_rules.js
```

## Integration with Consequence Compiler

The Consequence Compiler (Day 1c) will use these rules:

```javascript
// Pseudo-code for Day 1c
function processEvent(event) {
  // 1. Get matching rules
  const rules = getRulesForEvent(allRules, event.event_type);
  
  // 2. Filter by condition
  const matchedRules = rules.filter(rule => 
    matchesCondition(rule, event)
  );
  
  // 3. Extract and sort actions
  const actions = matchedRules.flatMap(rule => rule.then);
  const sortedActions = sortActionsByPriority(actions);
  
  // 4. Generate jobs
  const jobs = sortedActions.map(action => 
    generateJob(action, event)
  );
  
  // 5. Dispatch jobs
  dispatcher.queueJobs(jobs);
}
```

## Security Considerations

1. **Rule Validation:** All rules validated on load
2. **Action Whitelist:** Only defined actions allowed
3. **Payload Validation:** Required fields enforced
4. **Priority Enforcement:** Critical actions processed first
5. **No Code Injection:** Pure data-driven rules

## Performance Considerations

1. **Rule Caching:** Load rules once at startup
2. **Index by Event Type:** Fast rule lookup
3. **Priority Sorting:** Pre-sort when possible
4. **Action Batching:** Group low-priority actions

## Next Steps

### Day 1c: Consequence Compiler
Build the compiler that:
1. Receives runtime events
2. Matches consequence rules
3. Generates engine jobs
4. Dispatches to job queue

**File to create:** `backend/consequence/consequenceCompiler.js`

## Files

- `consequenceRules.json` - Rule definitions
- `consequence_rule_schema.json` - JSON schema
- `ruleValidator.js` - Validation utilities
- `README.md` - This documentation

## Support

For questions or issues:
1. Check the schema: `consequence_rule_schema.json`
2. Review examples in `consequenceRules.json`
3. Run tests: `test_consequence_rules.js`
4. Contact: Rudra (Gameplay Consequence System)
