# API Integration Guide: Text Risk Scoring Service

This document outlines the API endpoints available for integrating external applications with the Text Risk Scoring Service. The service is hosted at: `https://text-risk-scoring-service.onrender.com`

> [!TIP]
> For the vast majority of use cases where you simply need to send text and receive a risk score, the **`/analyze`** endpoint is the recommended approach.

---

## 1. Basic Text Analysis (Recommended)
Use this endpoint to send raw text from your application and receive a deterministic risk score and category.

**Endpoint:** `POST /analyze`
**URL:** `https://text-risk-scoring-service.onrender.com/analyze`
**Content-Type:** `application/json`

### Request Payload
```json
{
  "text": "The content from your application that needs to be analyzed (1-5000 chars)"
}
```

### Response Payload
```json
{
  "risk_score": 0.8,
  "confidence_score": 0.8,
  "risk_category": "HIGH",
  "trigger_reasons": ["Detected violence keyword: kill"],
  "processed_length": 42,
  "safety_metadata": {
    "is_decision": false,
    "authority": "NONE",
    "actionable": false
  },
  "errors": null
}
```
*Note: Possible risk categories are `LOW`, `MEDIUM`, and `HIGH`.*

---

## 2. Multi-Signal Aggregation
If your system is sending multiple pre-calculated risk signals (like policy violations, text risks, etc.) that need to be aggregated together under the BHIV ecosystem, use this unified aggregation endpoint.

**Endpoint:** `POST /api/v1/aggregate/unified`
**URL:** `https://text-risk-scoring-service.onrender.com/api/v1/aggregate/unified`
**Content-Type:** `application/json`

### Request Payload
```json
{
  "signals": [
    {
      "signal_id": "client-sig-001",
      "signal_type": "TEXT_RISK_SIGNAL",
      "base_risk_score": 0.9,
      "base_confidence_score": 1.0,
      "dgic_envelope": {
        "version": "schema_v1",
        "lineage_hash": "...",
        "envelope_hash": "...",
        "payload": {
          "epistemic_state": "KNOWN",
          "entropy_score": 0.0,
          "contradiction_flag": false
        }
      }
    }
  ]
}
```

---

## 3. Full Agent Invocation (Control Plane Routing)
If your application is acting as a registered source system or agent proposing an action that needs to go through the Sūtradhāra Control Plane and Sarathi Governance ecosystem, use the invoke endpoint.

**Endpoint:** `POST /api/v1/sutradhara/invoke`
**URL:** `https://text-risk-scoring-service.onrender.com/api/v1/sutradhara/invoke`
**Content-Type:** `application/json`

### Request Payload
```json
{
  "actor": "client_system_identifier",
  "proposed_action": "PUBLISH_CONTENT",
  "source_system": "CLIENT_NAME",
  "context_signals": [],
  "dgic_epistemic_state": {
    "epistemic_confidence": 0.9,
    "signal_lineage": ["client_source"],
    "collapse_state": "UNCOLLAPSED",
    "truth_boundary_reference": "N/A"
  }
}
```
