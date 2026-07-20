# API Samples — Ecosystem Integration Payloads

This document details the API request and response formats for the intake validator, canonical review packets, and assignment dispatches.

## 1. Intake Submission Request (`POST /api/v1/lifecycle/submit`)
```json
{
  "task_id": "NT-COR-B-001",
  "task_title": "Foundational Implementation Correction",
  "task_description": "Build a basic REST API with at least 3 endpoints, a README, and a working GitHub repository.",
  "submitted_by": "Ishan Shirode",
  "github_repo_link": "https://github.com/tester/repo",
  "module_id": "task-review-agent",
  "schema_version": "v1.0"
}
```

## 2. Review Detail Response (`GET /api/v1/lifecycle/review/{submission_id}`)
```json
{
  "review_id": "rev-sub-4e92a818c39e-2938e21a",
  "submission_id": "sub-4e92a818c39e-2938e21a",
  "evaluation_result": "PASS",
  "decision": "APPROVED",
  "score": 84,
  "executive_summary": "Automated engineering evaluation completed for task 'Foundational Implementation Correction'. Overall score is 84/100. Previous task baseline verified against registry rules. Candidate history indicates a maturity level of 'Senior Engineer' with a progression trend of 'Stable Progress'.",
  "production_readiness": "READY FOR PRODUCTION STAGING",
  "whats_done_well": [
    "Core file checks passed successfully.",
    "Modular layout is compliant with registry constraints."
  ],
  "required_fixes": [
    "No mandatory fixes required."
  ],
  "missing_incomplete": [],
  "evidence_used": [
    "README.md",
    "tests/",
    "api/lifecycle.py",
    "task_selector/review_orchestrator.py"
  ],
  "risks": [
    "Nominal ecosystem boundary risk"
  ],
  "ecosystem_alignment": "BCAB v1 / BCAES Volumes 1-3 aligned.",
  "benchmark_statements": [
    "Performance metrics match expected standards for maturity level 'Senior Engineer'."
  ],
  "next_3_tasks": [
    "Implement next task: NT-REI-B-001",
    "Perform full unit test execution suite",
    "Generate cryptographic release envelope"
  ],
  "timeline_commentary": "Submission checked within expected timeframes. Current velocity is 3.8 points per task.",
  "governance_state": "PENDING_REVIEW",
  "replay_references": [
    "Monotonic sequence check successful for trace: trace-auto-8716281a"
  ],
  "next_task_id": "NT-REI-B-001",
  "next_task_title": "REST API Reinforcement Task",
  "next_task_non_goals": [
    "No new AI features.",
    "No UI redesign without architectural purpose.",
    "No duplicate review engines.",
    "No shortcut implementations."
  ],
  "next_task_phase_breakdown": [
    "Initialize verification components",
    "Implement corrective patches for signals",
    "Validate state updates inside persistent storage"
  ]
}
```
