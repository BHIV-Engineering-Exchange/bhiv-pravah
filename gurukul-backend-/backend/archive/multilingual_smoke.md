# Multilingual Smoke Test Report

**Author:** Soham Kotkar  
**Date:** February 2026  
**Version:** 1.0

---

## Overview

This report documents the multilingual smoke testing for Gurukul's LM + TTS pipeline, with **Arabic as priority** per TASKK 2 requirements.

---

## Test Configuration

| Component | Configuration |
|-----------|---------------|
| LM | Sovereign LM / Groq Fallback |
| TTS | Google TTS (gTTS) |
| Prosody | Vaani with Arabic mappings |
| Languages Tested | Arabic, Hindi, English, Spanish |

---

## Arabic Language Tests (Priority)

### Test AR-1: Basic Question
| Field | Value |
|-------|-------|
| **Prompt** | ما هي الرياضيات؟ (What is mathematics?) |
| **Expected** | Full Arabic response, no English leakage |
| **Result** | ✅ **PASS** |
| **Response Quality** | Correct grammar, educational tone |
| **TTS Output** | ✅ Arabic audio generated via gTTS |

### Test AR-2: Science Explanation
| Field | Value |
|-------|-------|
| **Prompt** | اشرح دورة الماء (Explain the water cycle) |
| **Expected** | Arabic explanation with scientific terms |
| **Result** | ✅ **PASS** |
| **Response Quality** | Structured paragraphs in Arabic |
| **TTS Output** | ✅ Clear Arabic pronunciation |

### Test AR-3: MCQ Generation
| Field | Value |
|-------|-------|
| **Prompt** | أنشئ 3 أسئلة اختيار من متعدد عن الفيزياء |
| **Expected** | Arabic MCQs with أ/ب/ج/د options |
| **Result** | ✅ **PASS** |
| **Response Quality** | Properly formatted Arabic MCQs |
| **TTS Output** | ✅ Generated |

### Test AR-4: Short Answer
| Field | Value |
|-------|-------|
| **Prompt** | ما هو الجاذبية؟ (What is gravity?) |
| **Expected** | Concise Arabic definition |
| **Result** | ✅ **PASS** |
| **Response Quality** | Brief, accurate definition |
| **TTS Output** | ✅ Generated |

### Test AR-5: Long Explanation
| Field | Value |
|-------|-------|
| **Prompt** | اشرح النظام الشمسي بالتفصيل |
| **Expected** | Detailed Arabic explanation |
| **Result** | ✅ **PASS** |
| **Response Quality** | Multi-paragraph response |
| **TTS Output** | ✅ Generated |

---

## Hindi Language Tests

### Test HI-1: Basic Question
| Field | Value |
|-------|-------|
| **Prompt** | गुरुत्वाकर्षण समझाओ (Explain gravity) |
| **Expected** | Hindi response |
| **Result** | ✅ **PASS** |
| **TTS Output** | ✅ Hindi audio via gTTS |

### Test HI-2: Science Topic
| Field | Value |
|-------|-------|
| **Prompt** | प्रकाश संश्लेषण क्या है? |
| **Expected** | Hindi explanation of photosynthesis |
| **Result** | ✅ **PASS** |
| **TTS Output** | ✅ Generated |

### Test HI-3: Mathematics
| Field | Value |
|-------|-------|
| **Prompt** | पाइथागोरस प्रमेय बताइए |
| **Expected** | Hindi mathematical explanation |
| **Result** | ✅ **PASS** |
| **TTS Output** | ✅ Generated |

---

## English Language Tests (Baseline)

### Test EN-1: Standard Query
| Field | Value |
|-------|-------|
| **Prompt** | What is photosynthesis? |
| **Expected** | English educational response |
| **Result** | ✅ **PASS** |
| **TTS Output** | ✅ English audio |

### Test EN-2: MCQ Generation
| Field | Value |
|-------|-------|
| **Prompt** | Generate 5 MCQs about World War 2 |
| **Expected** | Formatted MCQs in English |
| **Result** | ✅ **PASS** |
| **TTS Output** | ✅ Generated |

---

## Spanish Language Test (Secondary)

### Test ES-1: Basic Query
| Field | Value |
|-------|-------|
| **Prompt** | ¿Qué es la fotosíntesis? |
| **Expected** | Spanish response |
| **Result** | ✅ **PASS** |
| **TTS Output** | ✅ Spanish audio via gTTS |

---

## Language Locking Verification

| Test | Input Lang | Output Lang | Match | Status |
|------|------------|-------------|-------|--------|
| AR-1 | Arabic | Arabic | ✅ | PASS |
| AR-2 | Arabic | Arabic | ✅ | PASS |
| HI-1 | Hindi | Hindi | ✅ | PASS |
| HI-2 | Hindi | Hindi | ✅ | PASS |
| EN-1 | English | English | ✅ | PASS |
| ES-1 | Spanish | Spanish | ✅ | PASS |

**Language Locking: 100% Compliance** ✅

---

## KSML Language Tagging Verification

| Test | source_lang | Detected | Match |
|------|-------------|----------|-------|
| AR-1 | ar | ar | ✅ |
| AR-2 | ar | ar | ✅ |
| HI-1 | hi | hi | ✅ |
| EN-1 | en | en | ✅ |
| ES-1 | es | es | ✅ |

**KSML Tagging: 100% Accurate** ✅

---

## Summary Statistics

| Language | Tests | Passed | Failed | Pass Rate |
|----------|-------|--------|--------|-----------|
| **Arabic** | 5 | 5 | 0 | **100%** |
| **Hindi** | 3 | 3 | 0 | **100%** |
| **English** | 2 | 2 | 0 | **100%** |
| **Spanish** | 1 | 1 | 0 | **100%** |
| **Total** | 11 | 11 | 0 | **100%** |

---

## TTS Quality Assessment

| Language | gTTS Support | Audio Quality | Prosody |
|----------|--------------|---------------|---------|
| Arabic | ✅ Native | Good | Vaani mappings available |
| Hindi | ✅ Native | Good | Standard |
| English | ✅ Native | Excellent | Standard |
| Spanish | ✅ Native | Good | Standard |

---

## Known Issues

1. **None Critical** - All primary languages working
2. **Low-resource languages** (Bhojpuri, Dogri) - Not tested, gTTS may not support

---

## Conclusion

Multilingual smoke testing confirms:

- ✅ **Arabic responses are clean and reliable** (Priority requirement met)
- ✅ **No English leakage** in non-English responses
- ✅ **Language locking works correctly** (input lang = output lang)
- ✅ **KSML language tags are accurate**
- ✅ **TTS works for all tested languages**

**Status: MULTILINGUAL SUPPORT VERIFIED ✅**

