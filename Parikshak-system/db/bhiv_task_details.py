"""
BHIV Task Details Database - Parikshak v6.0
Stores full specifications for task assignments.
"""
from typing import Dict, Any, List

BHIV_TASK_DETAILS: Dict[str, Dict[str, Any]] = {
    "T-GOV-001": {
        "title": "Deterministic Governance Evaluation Gateway",
        "purpose": "Verify codebase structural compliance and validate metadata configurations through a deterministic gateway to protect downstream environments.",
        "read_this_first": "DO NOT run arbitrary executions. Ensure that all review state changes are written directly through the atomic replay persistent storage, and trace integrity is confirmed before mutation.",
        "scope": "FASTAPI request pipeline, OCC lock checks, and the initial review validation rules.",
        "responsibility": "Junior Review Operator",
        "integration_block": {
            "primary": "Niyantran Task Registry",
            "audit": "Gov-OS Event Ledger",
            "evidence": "Bucket Storage",
            "observer": "Saarthi Progress Portal"
        },
        "learning_kit": [
            "FastAPI Middleware Architecture",
            "Deterministic State Machines",
            "Append-only Event Sourcing"
        ],
        "execution_phases": [
            "Validate inbound request schema",
            "Read repository structural metrics",
            "Apply binary checks and emit governance event"
        ],
        "deliverables": [
            "FastAPI router endpoint definition",
            "Unit tests covering schema validation cases",
            "Audit event propagation proof"
        ],
        "review_packet_requirements": [
            "Trace path directory contents log",
            "Cryptographic signature tokens"
        ],
        "acceptance_criteria": [
            "FastAPI returns status 200 on schema match",
            "Invalid module ID returns schema_violation fail",
            "Trace record written atomically to the Gov-OS SQLite backend"
        ],
        "expected_runtime": "2-3 hours",
        "required_screenshots": [
            "Swagger docs layout",
            "Gov-OS transaction logs"
        ],
        "required_code_packets": [
            "api/review_routes.py",
            "security/middleware.py"
        ],
        "testing_requirements": [
            "pytest tests/test_validation.py"
        ],
        "professional_closing": "Deliver with care. Direct all queries to the BHIV Engineering Command Office."
    },
    "T-GOV-002": {
        "title": "Dynamic Task Adaptability and Graph Enforcement System",
        "purpose": "Implement strict deterministic graph traversal rules for candidate next-task routing without alternative mappings.",
        "read_this_first": "TRAVERSAL MUST BE DETERMINISTIC. All edge matching logic must result in direct mapped corrective or advancement nodes. Mock data and heuristics are prohibited.",
        "scope": "Graph edge validation, cycle checks, and state emissions inside task_selector.",
        "responsibility": "System Integrator",
        "integration_block": {
            "primary": "Niyantran Graph Engine",
            "audit": "Gov-OS Ledger",
            "evidence": "Bucket Store",
            "observer": "Saarthi"
        },
        "learning_kit": [
            "Graph traversal algorithms",
            "Deterministic Finite Automata",
            "OCC Lock Patterns"
        ],
        "execution_phases": [
            "Intake state validation",
            "Graph traversal evaluation",
            "Next Task record persistence"
        ],
        "deliverables": [
            "task_graph_engine.py updates",
            "Graph traversal test vectors"
        ],
        "review_packet_requirements": [
            "Traversal trace logs",
            "Deterministic seed values"
        ],
        "acceptance_criteria": [
            "Traversal produces exact next task matching Niyantran task graph specifications",
            "Missing edge mappings trigger a Hard Reject response"
        ],
        "expected_runtime": "3-4 hours",
        "required_screenshots": [
            "Traversal trace logs screenshot",
            "State transitions list screenshot"
        ],
        "required_code_packets": [
            "task_selector/task_graph_engine.py",
            "task_selector/final_convergence.py"
        ],
        "testing_requirements": [
            "pytest tests/test_determinism_proof.py"
        ],
        "professional_closing": "Respect the boundaries. Direct escalation requests to senior operators."
    },
    "T-COR-001": {
        "title": "Relational Storage Core and Persistence Layer",
        "purpose": "Deploy primary database storage schemas and maintain dual-write event synchronization across SQLite and JSON fallbacks.",
        "read_this_first": "NO RAW QUERIES. All database mutations must happen via SQL Alchemy session bindings with strict type enforcement.",
        "scope": "SQLAlchemy models, persistent storage transactions, and database migration routines.",
        "responsibility": "Core Database Engineer",
        "integration_block": {
            "primary": "SQLite DB Layer",
            "audit": "Gov-OS Ledger",
            "evidence": "Bucket Staging File System"
        },
        "learning_kit": [
            "SQLAlchemy ORM Relationships",
            "JSON Serialization and Deserialization",
            "Database Schema Migration Strategies"
        ],
        "execution_phases": [
            "Define ORM schema model configurations",
            "Implement dual-write thread locks",
            "Configure transactional fallbacks"
        ],
        "deliverables": [
            "db/models.py structural updates",
            "db/persistent_storage.py lock updates"
        ],
        "review_packet_requirements": [
            "SQL schema definition logs",
            "Dual write file sync validation logs"
        ],
        "acceptance_criteria": [
            "Writes are synchronized across SQLite and product_state.json",
            "Concurrent modifications trigger OCC Lock exceptions"
        ],
        "expected_runtime": "4-5 hours",
        "required_screenshots": [
            "SQLite database structure view",
            "JSON file update logs"
        ],
        "required_code_packets": [
            "db/models.py",
            "db/persistent_storage.py"
        ],
        "testing_requirements": [
            "pytest tests/test_persistence.py"
        ],
        "professional_closing": "Maintain absolute integrity. Contact structural governors on database drift."
    }
}

def get_bhiv_task_details(task_id: str, default_dharma: str = "", default_signals: List[str] = []) -> Dict[str, Any]:
    """
    Retrieve full detailed BHIV task specifications for a task ID.
    Generates dynamic details if the task ID is not explicitly mapped, ensuring no title-only tasks.
    """
    res = None
    if task_id in BHIV_TASK_DETAILS:
        res = dict(BHIV_TASK_DETAILS[task_id])
    else:
        # Generate dynamically based on task ID pattern
        title = f"Task Assignment: {task_id}"
        purpose = default_dharma or f"Ensure proper compliance and capability mapping for subsystem operations."
        
        # Try parsing subsystem/product from ID
        product = "BHIV Ecosystem"
        subsystem = "Universal Subsystem"
        if "COR" in task_id:
            title = f"Core System Engineering and Validation: {task_id}"
            product = "Niyantran Core"
            subsystem = "Storage Layer"
        elif "SEC" in task_id:
            title = f"Security Vulnerability Hardening: {task_id}"
            product = "Gov-OS Security"
            subsystem = "Authorization Gateway"
        elif "SIG" in task_id:
            title = f"Operational Signal Harvesting: {task_id}"
            product = "Parikshak Signal Engine"
            subsystem = "Metrics Harvester"
        elif "ASN" in task_id:
            title = f"Rule Engine Logic Hardening: {task_id}"
            product = "Parikshak Rule Engine"
            subsystem = "PAC Gatekeeper"
        elif "DEC" in task_id:
            title = f"Decision Pipeline Verification: {task_id}"
            product = "Parikshak Decision Engine"
            subsystem = "Approvals Gateway"
        elif "HIL" in task_id:
            title = f"Human-in-Loop Escalation Routing: {task_id}"
            product = "Saarthi Interaction Portal"
            subsystem = "Oversight Console"
        elif "TST" in task_id:
            title = f"QA Test Suite and Repeatability Audit: {task_id}"
            product = "Niyantran Testing"
            subsystem = "QA Automation Suite"
        elif "VAA" in task_id:
            title = f"Voice Synthesizer Stream Stability: {task_id}"
            product = "Vaani TTS"
            subsystem = "Audio Streamer"
            
        signals_list = default_signals or ["integrity_check_passed", "metrics_logged"]
        
        res = {
            "title": title,
            "purpose": purpose,
            "read_this_first": "Review the blueprint requirements before making any modifications. Keep all changes clean, reentrant, and cryptographically verified.",
            "scope": f"Operational rules matching {task_id} boundaries.",
            "responsibility": "Lead Backend Integrator",
            "integration_block": {
                "primary": product,
                "subsystem": subsystem,
                "audit": "Gov-OS",
                "evidence": "Bucket Storage",
                "observer": "Saarthi"
            },
            "learning_kit": [
                f"BHIV {product} Standards Document",
                "Ecosystem Integration Boundaries",
                "TANTRA Compliance Checklists"
            ],
            "execution_phases": [
                "Initialize verification components",
                "Implement corrective patches for signals: " + ", ".join(signals_list),
                "Validate state updates inside persistent storage"
            ],
            "deliverables": [
                f"Subsystem updates for {task_id}",
                "Verification logs demonstrating compliance"
            ],
            "review_packet_requirements": [
                "Subsystem capability proof",
                "Trace integrity logs"
            ],
            "acceptance_criteria": [
                f"All completion signals: {', '.join(signals_list)} must evaluate to true",
                "No regression detected in execution path"
            ],
            "expected_runtime": "2-4 hours",
            "required_screenshots": [
                f"Subsystem execution state screenshot",
                "Trace verification logs screenshot"
            ],
            "required_code_packets": [
                "task_selector/task_graph_engine.py"
            ],
            "testing_requirements": [
                "pytest tests/test_operational_resilience.py"
            ],
            "professional_closing": f"Deliver promptly. For support, escalate through Gov-OS channel with trace reference."
        }

    # Ensure canonical fields are present
    res["non_goals"] = res.get("non_goals", [
        "No new AI features.",
        "No UI redesign without architectural purpose.",
        "No duplicate review engines.",
        "No shortcut implementations."
    ])
    res["phase_breakdown"] = res.get("phase_breakdown", res.get("execution_phases", []))
    return res
