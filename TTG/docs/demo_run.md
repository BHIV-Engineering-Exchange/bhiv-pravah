# Demo Script - Real-Time Micro-Bridge Dashboard

## Demo Flow

### 1. Introduction
"This is the Real-Time Micro-Bridge Dashboard - a secure system for text-to-game generation with live telemetry."

**Show:** Dashboard overview, key panels

---

### 2. Text-to-Game Generation
**Action:** 
- Type: "Create a fast runner game"
- Click "Start Generation"

**Say:** "I'll enter a prompt. The system converts this to a structured game schema and generates jobs."

**Expected:** Success message, 7 jobs appear in queue

---

### 3. Job Queue Processing
**Say:** "The system generates BUILD_SCENE, LOAD_ASSETS, SPAWN_ENTITY jobs, and START_LOOP. These dispatch to the engine."

**Show:** Jobs transitioning: queued → dispatched → running → completed

---

### 4. Live Game Telemetry
**Say:** "Once the game starts, we receive real-time telemetry: FPS, score, lives, and duration."

**Show:** 
- Score increasing
- FPS at 55-60 (green)
- Lives: 3 hearts
- Duration counting

---

### 5. Game Over
**Say:** "When the player loses all lives, the game ends with final score."

**Show:**
- Lives decrease to 0
- Status: "ENDED"
- Game Over message with final score

---

### 6. Production Features
**Say:** "The system includes JWT authentication, HMAC signatures, failure guards, and cloud deployment configs. Production ready."

---

## Success Criteria
- ✅ Text converts to game schema
- ✅ Jobs dispatch successfully
- ✅ Telemetry updates in real-time
- ✅ Game over displays correctly
- ✅ No console errors
