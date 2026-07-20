# Demo ACT → System Mapping

**Owner:** Soham Kotkar  
**Coordinator:** Yaseen (Narrative Director)  
**Date:** February 2026  
**Status:** LOCKED FOR RECORDING

---

## Overview

This document maps each cinematic act to specific system actions for clean recording.

---

## Act I — System Entry (2 minutes)

### Narrative Goal
Introduce Gurukul as a purposeful learning platform

### System Actions
| Step | Action | Route/Endpoint | Expected Result |
|------|--------|----------------|-----------------|
| 1.1 | Show landing page | `/home` | Hero section loads |
| 1.2 | Highlight features | Scroll | Feature grid visible |
| 1.3 | Click "Get Started" | → `/sign-in` | Login form appears |
| 1.4 | Login as student | POST `/api/v1/auth/login` | Dashboard loads |

### Recording Notes
- Keep mouse movements smooth
- Pause 2 seconds on each feature card
- Login credentials pre-filled

---

## Act II — Learning Flow (4 minutes)

### Narrative Goal
Show the guided learning journey

### System Actions
| Step | Action | Route/Endpoint | Expected Result |
|------|--------|----------------|-----------------|
| 2.1 | View dashboard | `/dashboard` | "Next Step" card visible |
| 2.2 | Select subject | Click → `/subjects` | Subject list loads |
| 2.3 | Choose Science | Click → `/lectures/science` | Lesson list appears |
| 2.4 | Open lesson | Click lesson | Content displays |
| 2.5 | Ask a doubt | `/chatbot` | Chat interface opens |
| 2.6 | Type question | "What is photosynthesis?" | AI response appears |
| 2.7 | Play audio | Click speaker icon | TTS plays response |

### Recording Notes
- Use pre-tested question: "What is photosynthesis?"
- Wait for full AI response before audio
- Audio should play completely

---

## Act III — Language Switch (3 minutes) ⭐ CRITICAL

### Narrative Goal
Demonstrate multilingual intelligence

### System Actions
| Step | Action | Input | Expected Output |
|------|--------|-------|-----------------|
| 3.1 | Ask in Arabic | "ما هي الرياضيات؟" | Arabic response |
| 3.2 | Switch to English | "Now explain in English" | English response |
| 3.3 | Switch to Hindi | "अब हिंदी में बताओ" | Hindi response |
| 3.4 | Play Hindi audio | Click speaker | Hindi TTS plays |

### Pre-Tested Prompt Sequence
```
Step 1: ما هي الرياضيات؟
Step 2: Now explain the same in English
Step 3: अब इसे हिंदी में समझाओ
```

### Recording Notes
- **THIS HAPPENS ONCE** - No retries on camera
- Same chat session, no reloads
- Wait for each response to complete
- Yaseen frames approval required before recording

---

## Act IV — Assessment (3 minutes)

### Narrative Goal
Show quiz generation and scoring

### System Actions
| Step | Action | Route/Endpoint | Expected Result |
|------|--------|----------------|-----------------|
| 4.1 | Navigate to test | `/test` | Quiz interface loads |
| 4.2 | Generate quiz | "Generate 5 MCQs on solar system" | MCQs appear |
| 4.3 | Answer questions | Click options | Selections highlight |
| 4.4 | Submit quiz | Click Submit | Score displays |
| 4.5 | Show results | Auto | Correct/incorrect marked |

### Recording Notes
- Use pre-tested topic: "solar system"
- Answer mix of correct/incorrect for realistic demo
- Score should be ~60-80%

---

## Act V — Closure (2 minutes)

### Narrative Goal
Summarize the platform's value

### System Actions
| Step | Action | Route/Endpoint | Expected Result |
|------|--------|----------------|-----------------|
| 5.1 | Return to dashboard | `/dashboard` | Progress updated |
| 5.2 | Show journey progress | Scroll | Visual progress bar |
| 5.3 | Highlight key stats | Hover | Tooltips appear |
| 5.4 | End on home | `/home` | Clean closing shot |

### Recording Notes
- Smooth return to dashboard
- Brief pause on progress visualization
- End with Gurukul logo visible

---

## Locked Recording Order

```
1. Act I   - System Entry      [2 min]
2. Act II  - Learning Flow     [4 min]
3. Act III - Language Switch   [3 min] ⭐
4. Act IV  - Assessment        [3 min]
5. Act V   - Closure           [2 min]
─────────────────────────────────────────
Total Runtime: ~14 minutes
```

---

## Coordination Protocol

### Before Each Act
- Yaseen gives "Ready" signal
- Soham confirms system state
- 3-second countdown

### During Recording
- Soham follows Yaseen's pacing
- No improvisation
- No feature exploration

### If Something Goes Wrong
1. Yaseen says "Cut"
2. Soham resets to act start
3. 30-second buffer
4. Resume from act beginning

---

## Emergency Resets

| Act | Reset Route | Recovery Time |
|-----|-------------|---------------|
| I | `/home` | 5 seconds |
| II | `/dashboard` | 5 seconds |
| III | `/chatbot` (new session) | 10 seconds |
| IV | `/test` | 5 seconds |
| V | `/dashboard` | 5 seconds |

---

**MAPPING STATUS: LOCKED ✅**

**No surprises during capture.**

