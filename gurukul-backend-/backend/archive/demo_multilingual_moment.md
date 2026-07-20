# Multilingual Moment - Approved Interaction

**Owner:** Soham Kotkar  
**Date:** February 2026  
**Status:** LOCKED - ONE TAKE ONLY

---

## Critical Rule

**This happens ONCE. No repetition.**

---

## Approved Multilingual Flow

### The Sequence (Single Shot)

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Arabic Question                                    │
│  Input:  ما هي الرياضيات؟                                   │
│  Output: [Full Arabic explanation of mathematics]           │
│  Wait:   3 seconds for response                             │
├─────────────────────────────────────────────────────────────┤
│  STEP 2: Switch to English                                  │
│  Input:  Now explain the same concept in English            │
│  Output: [English explanation, same context]                │
│  Wait:   3 seconds for response                             │
├─────────────────────────────────────────────────────────────┤
│  STEP 3: Switch to Hindi                                    │
│  Input:  अब इसे हिंदी में समझाओ                              │
│  Output: [Hindi explanation, same context]                  │
│  Wait:   3 seconds for response                             │
├─────────────────────────────────────────────────────────────┤
│  STEP 4: Play Hindi Audio                                   │
│  Action: Click speaker icon                                 │
│  Output: [Hindi TTS plays clearly]                          │
│  Wait:   Audio completes                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Exact Prompts (Copy-Paste Ready)

### Prompt 1 (Arabic)
```
ما هي الرياضيات؟
```

### Prompt 2 (English Switch)
```
Now explain the same concept in English
```

### Prompt 3 (Hindi Switch)
```
अब इसे हिंदी में समझाओ
```

---

## Expected Outputs

### Arabic Response (Sample)
```
الرياضيات هي علم يدرس الأرقام والأشكال والأنماط. 
تساعدنا على فهم العالم من حولنا وحل المشكلات...
```

### English Response (Sample)
```
Mathematics is the study of numbers, shapes, and patterns.
It helps us understand the world around us and solve problems...
```

### Hindi Response (Sample)
```
गणित संख्याओं, आकृतियों और पैटर्न का अध्ययन है।
यह हमें अपने आसपास की दुनिया को समझने और समस्याओं को हल करने में मदद करता है...
```

---

## Test Results (Pre-Recording Validation)

| Test # | Date | Arabic | English | Hindi | TTS | Status |
|--------|------|--------|---------|-------|-----|--------|
| 1 | Feb 2026 | ✅ | ✅ | ✅ | ✅ | PASS |
| 2 | Feb 2026 | ✅ | ✅ | ✅ | ✅ | PASS |
| 3 | Feb 2026 | ✅ | ✅ | ✅ | ✅ | PASS |

**Consistency: 100%**

---

## Technical Requirements

### Chat Session
- Same session throughout (no page reload)
- Context must be maintained
- No clearing chat history between switches

### Language Detection
- Input language auto-detected
- Output matches input language
- No English leakage in Arabic/Hindi

### TTS
- Hindi audio selected automatically
- Volume normalized
- No buffering delays

---

## Framing Approval

### Yaseen's Checklist
- [ ] Arabic text readable on screen
- [ ] Response area visible
- [ ] Audio icon visible
- [ ] Smooth transitions between languages

### Camera Notes
- Wide shot for Arabic (RTL text)
- Focus on response area
- Audio waveform visible during TTS

---

## Abort Conditions

### Stop Recording If:
- Arabic response contains English words
- Context is lost between switches  
- TTS fails to play
- Response takes > 5 seconds
- Any visible error

### Recovery:
- Cut immediately
- Clear chat
- Wait 30 seconds
- Start fresh from Arabic prompt

---

## Sign-Off

| Role | Name | Approval |
|------|------|----------|
| System Lead | Soham | ✅ Approved |
| Narrative | Yaseen | ⬜ Pending |
| TTS Check | Noopur | ✅ Verified |

---

**ONE APPROVED MULTILINGUAL INTERACTION ✅**

**Shared with Yaseen for framing approval.**

