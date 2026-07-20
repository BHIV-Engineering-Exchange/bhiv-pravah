# API Contract with HR Platform

**Version:** 1.0
**Status:** Draft
**Last Updated:** 2025-12-04

## Overview
This document defines the interface between the HR Intelligence Engine ("AI Brain") and the Core HR Platform. The AI Brain exposes REST API endpoints to receive candidate data for decision-making and feedback for reinforcement learning.

## Base URL
`http://<ai-service-host>:5000`

## Endpoints

### 1. Make Decision
**Endpoint:** `POST /ai/decide`
**Description:** Requests an AI-driven hiring decision for a candidate based on their profile and job description.

**Request Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "candidate": {
    "id": "cand_123",
    "name": "John Doe",
    "email": "john@example.com",
    "skills": ["Python", "FastAPI", "React"],
    "experience_years": 5,
    "resume_text": "Experienced full-stack developer..."
  },
  "job": {
    "id": "job_456",
    "title": "Senior Backend Engineer",
    "required_skills": ["Python", "Django", "AWS"],
    "min_experience": 4
  },
  "history": {
    "previous_interactions": []
  }
}
```

**Response Body:**
```json
{
  "match_score": 0.85,
  "rl_adjusted_score": 0.88,
  "decision": "shortlist",
  "explanation": "Strong match on Python skills and experience. Positive sentiment from resume.",
  "metadata": {
    "model_version": "v1.0",
    "timestamp": "2025-12-04T10:00:00Z"
  }
}
```

**Possible Decisions:**
- `shortlist`: High confidence match.
- `reject`: Low confidence match.
- `interview`: Good potential, needs human assessment.
- `followup`: Missing information or ambiguous case.

---

### 2. Submit Feedback
**Endpoint:** `POST /ai/feedback`
**Description:** Provides feedback on the AI's decision to train the Reinforcement Learning model.

**Request Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "candidate_id": "cand_123",
  "job_id": "job_456",
  "decision_taken": "shortlist",
  "outcome": "good",
  "comments": "Candidate performed well in technical round."
}
```

**Outcome Values:**
- `good`: The decision led to a positive result (e.g., hired, good interview).
- `bad`: The decision led to a negative result (e.g., rejected after interview, ghosted).
- `uncertain`: Outcome is not yet clear or neutral.

**Response Body:**
```json
{
  "status": "success",
  "message": "Feedback received and RL model updated.",
  "reward_value": 1.0
}
```

## Error Handling
- **400 Bad Request:** Malformed JSON or missing required fields.
- **422 Validation Error:** Data types do not match expected schema.
- **500 Internal Server Error:** System failure.
