# Security, Audit & Traceability Guide

## Audit Log Schema
```json
{
  "event_id": "evt_12345",
  "timestamp": "2026-01-29T17:00:00Z",
  "client_id": "client_abc",  // Current implementation uses client_id instead of tenant_id
  "user_id": "user_123",
  "action": "candidate_matched",
  "resource_type": "job_application",
  "resource_id": "application_456",
  "old_value": {"status": "submitted"},
  "new_value": {"status": "matched"},
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "ai_decision": {
    "model_used": "phase3_semantic_engine",
    "confidence_score": 0.87,
    "decision_factors": ["skills_match", "experience_match", "values_alignment"],
    "reinforcement_feedback": "positive"
  }
}
```

## AI/RL Audit Requirements
- Log AI model decisions with confidence scores
- Track reinforcement learning feedback loops
- Record AI/RL service interaction for traceability
- Maintain audit trails for AI-assisted decisions
- Log model version and parameters used
- **Current Implementation**: Phase 3 semantic engine with <0.02s response time

## Compliance Requirements
- All actions logged with tenant isolation
- Provenance tracking for data changes
- Error logging for all failures
- Regional compliance (KSA/UAE/India)
- **Current System Status**: MongoDB Atlas migration complete, 111 endpoints operational, production-ready single-tenant system

---

**Created:** January 10, 2026  
**Status:** Template created, needs detailed implementation