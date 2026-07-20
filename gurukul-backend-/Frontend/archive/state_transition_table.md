# PRANA-G Cognitive States

Converts browser behavior into learning states.

## The 7 States

Only ONE state active at any time:

1. **ON_TASK** - Actively learning
2. **THINKING** - Pausing to process
3. **IDLE** - No activity 10+ minutes
4. **DISTRACTED** - Browser lost focus
5. **AWAY** - Tab hidden/switched
6. **OFF_TASK** - Frustrated/anxious behavior
7. **DEEP_FOCUS** - Intense concentration

## Priority Rules

Higher priority states override lower ones:

1. AWAY (highest - overrides everything)
2. DISTRACTED
3. IDLE
4. OFF_TASK
5. DEEP_FOCUS
6. THINKING
7. ON_TASK (default)

## State Triggers

### AWAY
- **When:** Tab not visible
- **Meaning:** You switched tabs or apps

### DISTRACTED  
- **When:** Window lost focus
- **Meaning:** Clicked outside browser

### IDLE
- **When:** No interaction for 10+ minutes
- **Meaning:** Stepped away or just reading

### OFF_TASK
- **When:** Rapid clicking (3+ in 2s) OR fast mouse (2500+ px/s)
- **Meaning:** Frustrated or stressed

### DEEP_FOCUS
- **When:** 60+ seconds on page, calm behavior, sustained 15 seconds
- **Meaning:** Fully concentrated

### THINKING
- **When:** Very slow mouse, 1-5 second pause
- **Meaning:** Processing information

### ON_TASK
- **When:** Active, but doesn't match other states
- **Meaning:** Normal learning activity

### State-Specific Cooldowns

| State      | Cooldown Type | Duration | Purpose                           |
|------------|---------------|----------|-----------------------------------|
| AWAY       | None          | Instant  | Immediate priority override       |
| DISTRACTED | None          | Instant  | Immediate priority override       |
| IDLE       | Standard      | 5s       | Prevent flicker on brief activity |
| OFF_TASK   | Standard      | 5s       | Confirm sustained frustration     |
| DEEP_FOCUS | Entry Delay   | 15s      | Prevent false positives           |
| THINKING   | Standard      | 5s       | Distinguish from momentary pauses |
| ON_TASK    | Standard      | 5s       | Standard transition timing        |

## State Transition Matrix

| From → To            | Allowed?   | Typical Trigger              | Cooldown  |
|----------------------|------------|------------------------------|-----------|
| Any → AWAY           | ✅ Always | Tab hidden                   | None      |
| Any → DISTRACTED     | ✅ Always | Focus lost                   | None      |
| Any → IDLE           | ✅ Yes    | 10min inactivity             | 5s        |
| ON_TASK → OFF_TASK   | ✅ Yes    | Rapid clicks / high velocity | 5s        |
| ON_TASK → DEEP_FOCUS | ✅ Yes    | Sustained calm (15s)         | 15s entry |
| ON_TASK → THINKING   | ✅ Yes    | Contemplative pause          | 5s        |
| THINKING → ON_TASK   | ✅ Yes    | Activity resumes             | 5s        |
| THINKING → IDLE      | ✅ Yes    | Pause extends                | 5s        |
| DEEP_FOCUS → ON_TASK | ✅ Yes    | Activity increases           | 5s        |
| OFF_TASK → ON_TASK   | ✅ Yes    | Behavior normalizes          | 5s        |
| IDLE → ON_TASK       | ✅ Yes    | User returns                 | 5s        |
| AWAY → ON_TASK       | ✅ Yes    | Tab visible again            | 5s        |

**Note:** All transitions respect minimum 5-second cooldown unless marked "None".

## Example Flow

```
Page Load → ON_TASK (5s)
Reading, scrolling → ON_TASK (30s)  
Pause to think → THINKING (8s)
Resume reading → ON_TASK (60s)
Calm, sustained → DEEP_FOCUS (180s)
Switch tab → AWAY (instantly)
```

## Console Output

Every state change logs:
```
[PRANA] STATE_CHANGE: ON_TASK → IDLE | reason: inactivity > 10min | duration: 45s
```

