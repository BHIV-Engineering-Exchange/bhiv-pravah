# Demo Rehearsal Script - Intent Compiler

**Date:** 2025-02-13  
**Duration:** 5-7 minutes  
**Objective:** Demonstrate full flow from text input to running game

---

## Pre-Demo Checklist

### ✅ Backend Setup
```bash
cd backend
npm start
```
**Verify:** Server running on port 3000

### ✅ Frontend Setup
```bash
cd frontend
npm run dev
```
**Verify:** Dashboard accessible at http://localhost:5173

### ✅ Engine Setup
```bash
cd backend
python python_bridge.py
```
**Verify:** Bridge connected, engine ready

### ✅ Browser Setup
- Open http://localhost:5173
- Open DevTools Console (F12)
- Clear console
- Zoom to 100%

---

## Demo Script

### **Part 1: Introduction (30 seconds)**

**Say:**
> "I'm going to demonstrate the Intent Compiler - a system that converts natural language into playable games. Watch as I type a simple description and the system generates a complete game schema and runs it in the engine."

**Show:**
- Dashboard overview
- Point to Text-to-Game panel
- Point to Game Telemetry panel

---

### **Part 2: Simple Example (1 minute)**

**Action 1:** Type in Text-to-Game panel:
```
fast runner with jump
```

**Say:**
> "Let's start simple. I'll type 'fast runner with jump'."

**Action 2:** Click "Compile Schema"

**Say:**
> "The system extracts the intent..."

**Show:**
- Extracted Intent panel appears
  - Genre: runner
  - Pacing: fast
  - Abilities: jump
- Compiled Schema panel appears
  - Game Mode: infinite_runner
  - Speed: 8
  - Entities: 0

**Action 3:** Click "Show JSON" (optional)

**Say:**
> "Here's the complete TG Engine Gameplay Contract generated from just 5 words."

**Action 4:** Click "Send to Engine"

**Say:**
> "Now let's send it to the engine..."

**Show:**
- Job Queue panel updates
- Job status: queued → dispatched → running → completed
- Game Telemetry panel goes LIVE
- Score starts incrementing
- FPS shows ~60
- Lives: 3

**Say:**
> "And the game is running! Real-time telemetry shows FPS, score, and lives."

---

### **Part 3: Complex Example (1.5 minutes)**

**Action 1:** Clear text input, type:
```
Make a hard temple run style game with jump, dash, obstacles, and coin pickups
```

**Say:**
> "Now let's try something more complex - a hard difficulty runner with multiple features."

**Action 2:** Click "Compile Schema"

**Show:**
- Extracted Intent:
  - Genre: runner
  - Pacing: medium (default)
  - Difficulty: hard
  - Abilities: jump, dash
  - Obstacles: yes
  - Pickups: yes

**Say:**
> "Notice how the system extracted all the features - difficulty, abilities, and entities."

**Action 3:** Click "Show JSON"

**Say:**
> "The schema now includes 2 abilities and 2 entity types with spawn rules."

**Action 4:** Click "Send to Engine"

**Show:**
- Game starts
- Telemetry updates
- Score increases faster (hard mode)

**Say:**
> "This game is harder - higher spawn rates for obstacles."

---

### **Part 4: Error Handling (1 minute)**

**Action 1:** Clear text, type:
```
runner with enemies and weapons
```

**Say:**
> "What happens if I request unsupported features like enemies and weapons?"

**Action 2:** Click "Compile Schema"

**Show:**
- Error message appears:
  - "❌ Enemies/Monsters, Weapons/Shooting not supported yet"
  - Lists supported features
  - Shows example prompt

**Say:**
> "The system rejects it with a clear explanation of what's supported and what's not. This prevents invalid schemas from reaching the engine."

---

### **Part 5: Consistency Demo (1 minute)**

**Action 1:** Clear text, type:
```
fast runner with jump
```

**Action 2:** Click "Compile Schema"

**Action 3:** Copy the JSON output

**Action 4:** Clear text, type:
```
Create a quick running game with jumping ability
```

**Say:**
> "Different wording, same intent..."

**Action 5:** Click "Compile Schema"

**Action 6:** Click "Show JSON"

**Say:**
> "Notice the gameplay section is identical - same game_mode, same speed, same abilities. The system is deterministic."

**Show:**
- Compare both JSON outputs
- Highlight matching fields:
  - game_mode: "infinite_runner"
  - global_speed: 8
  - abilities: { jump_force: 5 }

---

### **Part 6: Quick Examples (30 seconds)**

**Say:**
> "For convenience, we have quick example buttons."

**Action 1:** Click "Easy platformer with coin collection"

**Action 2:** Click "Compile Schema"

**Show:**
- Instant compilation
- Different game mode (side_scroller)
- Different scoring (collection)

**Say:**
> "Each example is pre-tested and guaranteed to work."

---

### **Part 7: Live Telemetry (1 minute)**

**Say:**
> "Let's watch a game run to completion."

**Action 1:** Use any compiled schema

**Action 2:** Click "Send to Engine"

**Show:**
- Game Telemetry panel:
  - Status: LIVE (green, pulsing)
  - Score incrementing
  - FPS ~60
  - Lives decreasing
  - Duration counting up

**Wait for game over**

**Show:**
- Status changes to ENDED (red)
- "GAME OVER" message appears
- Final score displayed

**Say:**
> "The telemetry updates in real-time via WebSocket connection to the engine."

---

### **Part 8: Wrap-up (30 seconds)**

**Say:**
> "To summarize:
> 1. Natural language input
> 2. Intent extraction
> 3. Schema compilation
> 4. Validation
> 5. Engine execution
> 6. Real-time telemetry
> 
> All in under 5 seconds from text to running game."

**Show:**
- Full dashboard overview
- Point to each panel

---

## Demo Variations

### **Variation A: Focus on Validation**
- Show multiple error cases
- Demonstrate empty input rejection
- Show nonsense input rejection

### **Variation B: Focus on Features**
- Show all 3 game modes (runner, platformer, arena)
- Show all 3 abilities (jump, dash, lane_switch)
- Show difficulty differences

### **Variation C: Focus on Consistency**
- Run consistency tests live
- Show deterministic output
- Compare multiple compilations

---

## Troubleshooting During Demo

### **Problem: Engine not connected**
**Solution:** 
- Check python_bridge.py is running
- Restart bridge if needed
- Show "Engine Offline" indicator

### **Problem: Compilation fails unexpectedly**
**Solution:**
- Use quick example buttons
- Show error message
- Explain validation

### **Problem: Game doesn't start**
**Solution:**
- Check Job Queue panel
- Show job status
- Check console for errors

---

## Recording Checklist

### **Before Recording**
- [ ] Clear browser cache
- [ ] Close unnecessary tabs
- [ ] Set zoom to 100%
- [ ] Clear console
- [ ] Restart all services
- [ ] Test full flow once

### **During Recording**
- [ ] Speak clearly
- [ ] Move mouse slowly
- [ ] Pause after each action
- [ ] Show results clearly
- [ ] Highlight important elements

### **After Recording**
- [ ] Review video
- [ ] Check audio quality
- [ ] Verify all features shown
- [ ] Add timestamps (optional)
- [ ] Export in HD

---

## Demo Prompts (Copy-Paste Ready)

```
fast runner with jump
```

```
Make a hard temple run style game with jump, dash, obstacles, and coin pickups
```

```
runner with enemies and weapons
```

```
Create a quick running game with jumping ability
```

```
Easy platformer with coin collection
```

```
Arena game with dash and lane switching
```

---

## Success Metrics

Demo is successful if you show:
- ✅ Text input → Schema compilation
- ✅ Intent extraction display
- ✅ JSON preview
- ✅ Engine execution
- ✅ Real-time telemetry
- ✅ Error handling
- ✅ Consistency/determinism

---

## Time Breakdown

| Section | Duration | Cumulative |
|---------|----------|------------|
| Introduction | 0:30 | 0:30 |
| Simple Example | 1:00 | 1:30 |
| Complex Example | 1:30 | 3:00 |
| Error Handling | 1:00 | 4:00 |
| Consistency | 1:00 | 5:00 |
| Quick Examples | 0:30 | 5:30 |
| Live Telemetry | 1:00 | 6:30 |
| Wrap-up | 0:30 | 7:00 |

**Total:** 7 minutes

---

## Post-Demo

### **Questions to Anticipate**

**Q: What if I want feature X?**  
**A:** Check INTENT_COMPILER_GUIDE.md for supported features. Unsupported features are rejected with clear explanations.

**Q: Is it deterministic?**  
**A:** Yes! Same input always produces same output. See consistency tests.

**Q: How fast is it?**  
**A:** Compilation: <5ms, Full flow: <100ms

**Q: Can it handle abuse?**  
**A:** Yes! 41 abuse tests, 100% pass rate. See abuse_test_report.md

---

**Status:** ✅ Ready for Demo  
**Prepared by:** Rudra Parmeshwar  
**Date:** 2025-02-13
