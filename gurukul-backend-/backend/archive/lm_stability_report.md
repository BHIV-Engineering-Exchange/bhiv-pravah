# LM Stability Report

**Author:** Soham Kotkar  
**Date:** February 2026  
**Version:** 1.0

---

## Overview

This report documents the stability testing of Gurukul's Language Model (LM) pipeline, covering the Input → LM → KSML → Output flow.

---

## Test Environment

| Component | Details |
|-----------|---------|
| LM Core | Sovereign LM (Fine-tuned Llama 3.2 3B with LoRA) |
| Fallback | Groq API (llama-3.3-70b-versatile) |
| KSML Processor | `ksml_processor.py` |
| Endpoint | `/api/v1/sovereign/infer` |

---

## Test Results: 10 Curriculum-Style Questions

### Question 1: Basic Science
| Field | Value |
|-------|-------|
| **Input** | "What is photosynthesis?" |
| **Language** | English |
| **Expected** | Clear explanation of photosynthesis process with examples |
| **Actual** | ✅ PASS - Structured response with definition, process, and examples |
| **KSML Labels** | `has_definitions: true`, `educational_level: beginner` |

### Question 2: Mathematics
| Field | Value |
|-------|-------|
| **Input** | "Explain the Pythagorean theorem" |
| **Language** | English |
| **Expected** | Formula + explanation + example |
| **Actual** | ✅ PASS - a² + b² = c² explained with triangle example |
| **KSML Labels** | `has_examples: true`, `educational_level: intermediate` |

### Question 3: History
| Field | Value |
|-------|-------|
| **Input** | "Who was Mahatma Gandhi?" |
| **Language** | English |
| **Expected** | Biographical information, key achievements |
| **Actual** | ✅ PASS - Comprehensive response covering life and contributions |
| **KSML Labels** | `topics: ["Gandhi", "India"]`, `educational_level: beginner` |

### Question 4: Hindi Language Test
| Field | Value |
|-------|-------|
| **Input** | "गुरुत्वाकर्षण क्या है?" |
| **Language** | Hindi |
| **Expected** | Response in Hindi explaining gravity |
| **Actual** | ✅ PASS - Hindi response with proper grammar |
| **KSML Labels** | `language: hi`, `has_definitions: true` |

### Question 5: Arabic Language Test
| Field | Value |
|-------|-------|
| **Input** | "ما هي الرياضيات؟" |
| **Language** | Arabic |
| **Expected** | Response in Arabic explaining mathematics |
| **Actual** | ✅ PASS - Arabic response generated |
| **KSML Labels** | `language: ar`, `educational_level: beginner` |

### Question 6: MCQ Generation
| Field | Value |
|-------|-------|
| **Input** | "Generate 5 MCQs on the solar system" |
| **Language** | English |
| **Expected** | 5 numbered questions with A/B/C/D options |
| **Actual** | ✅ PASS - Properly formatted MCQs |
| **KSML Labels** | `has_questions: true`, `structure.has_numbered_lists: true` |

### Question 7: Short Answer
| Field | Value |
|-------|-------|
| **Input** | "Define democracy in one sentence" |
| **Language** | English |
| **Expected** | Concise definition ≤ 2 lines |
| **Actual** | ✅ PASS - Single sentence definition |
| **KSML Labels** | `has_definitions: true`, `sentence_count: 1` |

### Question 8: Explanation Question
| Field | Value |
|-------|-------|
| **Input** | "Explain how rainbows are formed" |
| **Language** | English |
| **Expected** | Structured paragraphs with scientific explanation |
| **Actual** | ✅ PASS - Multi-paragraph explanation with light refraction |
| **KSML Labels** | `paragraph_count: 3`, `has_examples: true` |

### Question 9: Follow-up Context
| Field | Value |
|-------|-------|
| **Input** | "Tell me more about its colors" (after rainbow question) |
| **Language** | English |
| **Expected** | Context-aware response about VIBGYOR |
| **Actual** | ⚠️ PARTIAL - Response generated but context linking needs improvement |
| **KSML Labels** | `educational_level: intermediate` |

### Question 10: Very Short Question
| Field | Value |
|-------|-------|
| **Input** | "2+2?" |
| **Language** | English |
| **Expected** | "4" or brief answer |
| **Actual** | ✅ PASS - Correct answer provided |
| **KSML Labels** | `sentence_count: 1` |

---

## Summary Statistics

| Metric | Result |
|--------|--------|
| **Total Tests** | 10 |
| **Passed** | 9 |
| **Partial** | 1 |
| **Failed** | 0 |
| **Pass Rate** | 90% |

---

## Known Limitations

1. **Context Retention**: Follow-up questions may lose context without explicit session management
2. **Groq Fallback**: System still falls back to Groq API if local model fails (acceptable for demo)
3. **Long Responses**: Very long explanations (>500 words) may be truncated

---

## Recommendations

1. ✅ LM pipeline is **stable and demo-ready**
2. ⚠️ Consider disabling Groq fallback for production (per task requirement)
3. ✅ KSML labels are consistently generated
4. ✅ Multilingual support working for Hindi and Arabic

---

## Conclusion

The LM stability tests confirm that the Gurukul Language Model pipeline is functioning correctly for educational queries. The system reliably generates structured, contextually appropriate responses with proper KSML annotations.

**Status: DEMO READY ✅**

