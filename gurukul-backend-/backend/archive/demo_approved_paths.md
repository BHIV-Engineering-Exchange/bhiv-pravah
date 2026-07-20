# Approved Demo Paths - System Freeze

**Owner:** Soham Kotkar  
**Date:** February 2026  
**Status:** LOCKED FOR RECORDING

---

## System Freeze Confirmation ✅

The system is now in a **known-good state**. No logic changes permitted after this document is finalized.

---

## Safe Flows (APPROVED)

### Flow 1: Login & Dashboard Entry
```
Route: /sign-in → /dashboard
Status: ✅ SAFE
Expected: Clean login, dashboard loads with user data
Latency: < 2 seconds
```

### Flow 2: Subject Selection
```
Route: /subjects → /lectures/{subject}
Status: ✅ SAFE
Expected: Subject list loads, lessons display correctly
Latency: < 1.5 seconds
```

### Flow 3: Chat / Ask Doubt
```
Route: /chatbot
Status: ✅ SAFE
Expected: AI responds in same language as question
Latency: < 3 seconds
```

### Flow 4: Quiz Generation & Assessment
```
Route: /test → Generate Quiz → Submit
Status: ✅ SAFE
Expected: MCQs generated, score displayed after submission
Latency: < 3 seconds for generation
```

### Flow 5: Text-to-Speech (Vaani)
```
Endpoint: /api/v1/tts/speak
Status: ✅ SAFE
Expected: Audio plays without glitches
Latency: < 2 seconds
```

### Flow 6: Multilingual Switch
```
Flow: Arabic → English → Hindi
Status: ✅ SAFE
Expected: Same context maintained, language switches cleanly
Latency: < 3 seconds per switch
```

---

## Stable Prompts (PRE-TESTED)

| Prompt | Language | Expected Behavior |
|--------|----------|-------------------|
| "What is photosynthesis?" | English | Educational explanation |
| "ما هي الرياضيات؟" | Arabic | Arabic response, no English |
| "गुरुत्वाकर्षण समझाओ" | Hindi | Hindi explanation |
| "Generate 5 MCQs on solar system" | English | Formatted MCQs |
| "Explain gravity for class 5" | English | Simple, age-appropriate |

---

## Disabled Features (DO NOT TOUCH)

| Feature | Reason | Status |
|---------|--------|--------|
| Admin Dashboard | Complex, not needed for demo | 🔴 DISABLED |
| Teacher Dashboard | Incomplete UI | 🔴 DISABLED |
| Parent Dashboard | Not tested | 🔴 DISABLED |
| Avatar Customization | Experimental | 🔴 DISABLED |
| Document Summarizer | Memory issues | 🔴 DISABLED |
| Agent Simulator | Unstable | 🔴 DISABLED |
| Advanced Settings | Not needed | 🔴 DISABLED |

---

## Predictable Outputs (GUARANTEED)

### Chat Responses
- Always educational tone
- Always in requested language
- Never hallucinated facts
- Max response length: 500 words

### Quiz Generation
- Always 5-10 questions
- Always A/B/C/D format
- Always includes correct answer
- Always subject-appropriate difficulty

### TTS Output
- Always plays within 2 seconds
- No audio glitches
- Proper pronunciation for Arabic/Hindi/English

---

## Emergency Procedures

### If Something Fails During Recording:
1. **STOP** - Do not continue
2. **RESET** - Refresh the page
3. **RETRY** - Use approved flow only
4. **REPORT** - Note the failure for post-recording fix

### Recovery Routes:
- Any error → Redirect to `/home`
- Chat fails → Show "Please try again"
- Quiz fails → Show empty state gracefully

---

## Final Checklist Before Recording

- [x] All approved flows tested
- [x] All disabled features confirmed hidden
- [x] Multilingual prompts pre-tested
- [x] TTS audio verified
- [x] Latency within acceptable range
- [x] No console errors in production build
- [x] Graceful degradation working

---

**SYSTEM FREEZE STATUS: LOCKED ✅**

**Shared with Yaseen for recording coordination.**

