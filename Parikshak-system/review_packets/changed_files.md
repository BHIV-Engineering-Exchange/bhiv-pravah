# Changed Files List — Convergence Sprint

The following files have been modified or created to fulfill the ecosystem convergence sprint objectives:

| File Pattern / Path | Purpose | Key Changes |
|---|---|---|
| **[NEW]** `task_selector/review_packet_helper.py` | Canonical Review Packet helper | Centralized generation of 14-section review packets and Markdown output synchronization. |
| **[NEW]** `task_selector/architectural_registry.py` | BCAB/BCAES taxonomy registry | Stores canonical programs, products, services, domains, and capabilities; validates task bounds. |
| **[NEW]** `tests/test_architectural_governance.py` | Integration tests | Verifies registry validations and the human-approval gated task assignment pipeline. |
| **[MODIFY]** `task_selector/review_orchestrator.py` | Review orchestration | Intercepts submissions to validate architectural registry bounds, query progression history, apply repeat-failure score penalties, and disable auto-assignment. |
| **[MODIFY]** `api/lifecycle.py` | FastAPI Lifecycle endpoints | Maps detailed next task packets and the 14 engineering review sections into API response contracts. |
| **[MODIFY]** `api/review_routes.py` | FastAPI Review routing | Invokes review packet generation and SQL assignment insertion during governor approvals or modifications. |
| **[MODIFY]** `api/production.py` | FastAPI Production routing | Invokes review packet generation and SQL assignment updates during human override approvals. |
| **[MODIFY]** `evaluation_engine/learning_history_engine.py` | Progression analysis | Computes sequential repeat failures and promotion readiness flags based on historical performance. |
| **[MODIFY]** `evaluation_engine/execution_pipeline.py` | Execution pipeline | Integrates progression history and detailed review packet generation for automated runs. |
| **[MODIFY]** `canonical_db/integration.py` | Downstream adapters | Defines the SQL database assignment insertion method upon human approval propagation. |
| **[MODIFY]** `db/bhiv_task_details.py` | Task detail database | Enriches static and dynamic next task packets with `non_goals` and `phase_breakdown` arrays. |
| **[MODIFY]** `frontend/src/pages/Dashboard.js` | Frontend Console page | Redesigns the layout into a 10-panel High-Fidelity Executive Command Center. |
