# 📐 Evaluation Logic & Scoring Engine (v3.0)

> This document describes the **current** scoring system (v3.0). The earlier rule-based system (v1) that scored based on text length and keyword presence has been fully replaced.

---

## Overview

The evaluation engine determines how well a submitted GitHub repository fulfills the requirements defined across all submission inputs:

- `task_title` — What needs to be built
- `task_description` — How it should be built
- `github_repo_link` — The actual implementation
- `task_pdf_document` (optional) — Supplementary documentation

---

## Scoring Dimensions (Total: 100 Points)

### 1. Requirement Match — 40 Points *(Primary Driver)*

This is the most important dimension. It measures how closely the repository implementation satisfies the requirements extracted from the task inputs.

**Sub-components:**

| Sub-metric | Weight | How it's computed |
|------------|--------|-------------------|
| `feature_match_ratio` | 60% | What fraction of the expected features were found in repo files/components |
| `tech_stack_match` | 20% | What fraction of the expected technologies appear in the repo's file extensions and naming |
| `architecture_match` | 20% | Whether the repo's directory structure matches the expected architecture pattern |

**Formula:**

```
req_match_ratio = (feature_match * 0.6) + (tech_stack_match * 0.2) + (architecture_match * 0.2)
requirement_match_score = req_match_ratio × 40
```

**Alignment label:**

| req_match_ratio | Label |
|-----------------|-------|
| > 0.8 | `high` |
| 0.5 – 0.8 | `moderate` |
| < 0.5 | `low` |

---

### 2. Repository Completeness — 20 Points

Measures whether the repository has enough files relative to the task's complexity.

**Complexity thresholds:**

| Complexity | Min files for full score |
|------------|--------------------------|
| `low` | 3 files |
| `medium` | 8 files |
| `high` | 20 files |

**Formula:**

```
completeness_ratio = min(total_files / threshold, 1.0)
completeness_score = completeness_ratio × 20
```

---

### 3. Architecture Quality — 20 Points

Examines whether the repository follows recognized software architecture patterns.

**Signals checked:**

| Signal | Points | Description |
|--------|--------|-------------|
| `has_layers` | 0.4 | ≥ 3 top-level directories matching standard layer names (api, service, model, etc.) |
| `modular` | 0.3 | Any subdirectory structure (not a single flat folder) |
| `interface_usage` | 0.3 | Files containing "interface" or "abstract" in their path |

**Formula:**

```
architecture_ratio = sum of signals (max 1.0)
architecture_score = architecture_ratio × 20
```

---

### 4. Code Quality — 10 Points

Examines the quality signals present in the repository.

**Signals:**

| Signal | Points | Description |
|--------|--------|-------------|
| README depth | 0–0.6 | Score 0/1/2/3 based on README file size (absent/small/medium/large ×1000 bytes) |
| Documentation density | 0.4 | `.md` files / total code files ratio > 0.1 |

**Formula:**

```
quality_ratio = (readme_score / 3.0 × 0.6) + (0.4 if density > 0.1)
quality_score = quality_ratio × 10
```

---

### 5. PDF Documentation Alignment — 10 Points

Only applies when a PDF document is submitted. Evaluates whether the documentation is substantive.

**Signals:**

| Signal | Points | Condition |
|--------|--------|-----------|
| Text depth | 0.4 | PDF text length > 2000 chars |
| Text depth (partial) | 0.2 | PDF text length 500–2000 chars |
| Architecture description | 0.3 | Architecture section found in PDF |
| Feature listing | 0.3 | ≥ 3 documented features in PDF |

**Formula:**

```
doc_ratio = sum of signals (max 1.0)
documentation_score = doc_ratio × 10
```

---

## Full Score Formula

```
total_score = requirement_match_score   (0–40)
            + completeness_score         (0–20)
            + architecture_score         (0–20)
            + quality_score              (0–10)
            + documentation_score        (0–10)
            ──────────────────────────────────
            = 0 to 100
```

---

## Status Mapping

| Score | Status |
|-------|--------|
| ≥ 80 | ✅ `pass` |
| 50–79 | ⚠️ `borderline` |
| < 50 | ❌ `fail` |

---

## Missing Feature Detection

Any feature listed in the `expected_features` array (Step 1 output) that could **not** be matched to any component in the repository analysis becomes a **missing feature**.

These appear in:

- `failure_reasons` (top 3, shown to user)
- `missing_features` (full list, stored in `ReviewRecord`)
- `improvement_hints` (each prefixed with `"Improve: "`)

---

## Determinism Guarantee

The same `task_title`, `task_description`, `github_repo_link`, and `pdf_text` inputs **always produce the same score**. There are no random elements, LLM calls, or time-based components in the scoring equation.

> The only non-deterministic factor: if the GitHub repository changes between evaluations (new files added), the repo signals will differ — which is expected and correct behaviour.
