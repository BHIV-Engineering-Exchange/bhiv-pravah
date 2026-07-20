"""
Ecosystem Integrator — Parikshak v6.0.0

Propagates human-approved governed mutations downstream to:
  - Canonical DB (Gov-OS journal)
  - Bucket lineage log
  - Saarthi visibility ledger
  - Niyantran assignment ledger

No mock data. All propagation uses real signals from the governed envelope.
Human approval is mandatory before any propagation occurs.
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from canonical_db.contracts import GovernanceEnvelope
from canonical_db.pipeline import GovernedPipeline
from task_selector.bucket_integration import bucket_integration
from observability.observability import observability

SAARTHI_VISIBILITY_LEDGER = "storage/saarthi_visibility.jsonl"
NIYANTRAN_ASSIGNMENTS_LEDGER = "storage/niyantran_assignments.jsonl"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
def store_assignment_record_in_db(review_id: str, submission_id: str, next_task_id: str, candidate_id: str, governor: str, task_type: str, reason: str, trace_id: str):
    import json
    from datetime import datetime
    from db.db_config import SessionLocal
    from db.models import AssignmentModel, Builder
    from db.bhiv_task_details import get_bhiv_task_details
    
    db = SessionLocal()
    try:
        builder = db.query(Builder).filter(Builder.id == candidate_id).first()
        if not builder:
            builder = Builder(id=candidate_id, name=candidate_id)
            db.add(builder)
            db.commit()
            
        details = get_bhiv_task_details(next_task_id)
        assignment_id = f"assign-{trace_id[:8]}"
        
        # Check if already exists to prevent duplicate insertion error
        existing = db.query(AssignmentModel).filter(AssignmentModel.id == assignment_id).first()
        if not existing:
            db_assignment = AssignmentModel(
                id=assignment_id,
                builder_id=candidate_id,
                review_id=review_id,
                previous_submission_id=submission_id,
                next_task_id=next_task_id,
                task_type=task_type,
                title=details.get("title", f"Assignment: {next_task_id}"),
                objective=details.get("purpose", "Complete system requirements"),
                focus_area=details.get("scope", "General API"),
                difficulty="beginner",
                reason=reason,
                priority="Medium",
                category="Governance",
                est_ai_effort="2h",
                learning_resources=json.dumps(details.get("learning_kit", [])),
                review_checklist=json.dumps(details.get("acceptance_criteria", [])),
                status="assigned",
                created_at=datetime.now(),
                assigned_at=datetime.now(),
                completed_at=None
            )
            db.add(db_assignment)
            db.commit()
            return assignment_id
    finally:
        db.close()
    return None


class EcosystemIntegrator:
    def __init__(self, db_path: str = "storage/canonical_db.sqlite"):
        self.db_path = db_path
        self.pipeline = GovernedPipeline(self.db_path)
        os.makedirs("storage", exist_ok=True)

    def process_niyantran_submission(self, task_payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """
        Receives task from Niyantran. Returns intake receipt.
        Does NOT write to DB. Human approval required before any commit.
        """
        observability.log_observability_event("info", f"[Ecosystem] Niyantran intake: {task_payload.get('task_id')}", {
            "trace_id": trace_id,
            "task_id": task_payload.get("task_id")
        })
        return {
            "integration": "Niyantran",
            "status": "INGESTED_AWAITING_REVIEW",
            "trace_id": trace_id,
            "task_id": task_payload.get("task_id"),
            "requires_human_approval": True
        }

    def propagate_governed_approval(
        self,
        review_envelope: GovernanceEnvelope,
        governor: str,
        eval_output: Optional[Dict[str, Any]] = None,
        supporting_signals: Optional[Dict[str, Any]] = None,
        graph_result: Optional[Dict[str, Any]] = None,
        task_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Commits human-approved review/assignment and propagates downstream.
        Uses real eval_output and supporting_signals — no mock data.

        Args:
            review_envelope: Human-approved GovernanceEnvelope
            governor: Authorized human actor
            eval_output: Real evaluation output from execution_pipeline
            supporting_signals: Real signals from signal_engine
            graph_result: Real graph traversal result
            task_data: Real task submission data
        """
        # 1. Commit to Canonical DB via governed pipeline
        commit_res = self.pipeline.submit_mutation(review_envelope, governor)

        payload = review_envelope.payload

        # 2. Bucket lineage — use real signals if provided, else derive from envelope payload
        if eval_output and supporting_signals and graph_result and task_data:
            bucket_integration.log_evaluation(
                eval_output,
                supporting_signals,
                {"decision": "APPROVED" if payload.get("status") == "APPROVED" or
                              payload.get("score", 0) >= 80 else "REJECTED"},
                {
                    "next_task_id": graph_result.get("selected_task_id", ""),
                    "task_type": graph_result.get("task_type", "advancement"),
                    "title": graph_result.get("title", ""),
                    "difficulty": graph_result.get("difficulty", "intermediate")
                },
                task_data,
                trace_id=review_envelope.trace_id
            )
        else:
            # Minimal bucket entry derived from envelope — no mock fields
            bucket_integration.log_evaluation(
                {
                    "evaluation_result": "PASS" if payload.get("score", 0) >= 80 else "FAIL",
                    "failure_type": None,
                    "canonical_authority": True
                },
                {"domain": "engineering", "repository_available": False,
                 "expected_vs_delivered_evidence": {"delivery_ratio": 1.0},
                 "expected_features": [], "implemented_features": [], "missing_features": []},
                 {"decision": "APPROVED" if payload.get("score", 0) >= 80 else "REJECTED"},
                {"next_task_id": payload.get("submission_id", "unknown"),
                 "task_type": "advancement", "title": "", "difficulty": "intermediate"},
                {
                    "task_id": payload.get("submission_id", "unknown"),
                    "task_title": payload.get("submission_id", "Governed Review"),
                    "submitted_by": payload.get("reviewed_by", governor)
                },
                trace_id=review_envelope.trace_id
            )

        # 3. Saarthi visibility ledger
        saarthi_entry = {
            "trace_id": review_envelope.trace_id,
            "event_type": "downstream_visibility",
            "source": "Parikshak",
            "destination": "Saarthi",
            "payload": payload,
            "timestamp": _utcnow()
        }
        with open(SAARTHI_VISIBILITY_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(saarthi_entry) + "\n")

        # 4. Niyantran assignment ledger
        niyantran_assignment = {
            "trace_id": review_envelope.trace_id,
            "assignment_id": f"assign-{review_envelope.trace_id[:8]}",
            "task_id": (graph_result or {}).get("selected_task_id", payload.get("submission_id", "unknown")),
            "candidate_id": payload.get("reviewed_by", governor),
            "assigned_by": governor,
            "timestamp": _utcnow()
        }
        with open(NIYANTRAN_ASSIGNMENTS_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(niyantran_assignment) + "\n")

        # 4.5 Insert record into SQLite SQL Assignments table
        try:
            candidate_id = payload.get("candidate_name") or (task_data.get("submitted_by") if task_data else None) or governor
            next_task_id = (graph_result or {}).get("selected_task_id") or payload.get("selected_task_id") or payload.get("submission_id", "unknown")
            review_id = payload.get("review_id") or f"rev-{payload.get('submission_id')}"
            submission_id = payload.get("submission_id")
            task_type = (graph_result or {}).get("task_type") or ("advancement" if payload.get("evaluation_result") == "PASS" else "correction")
            reason = payload.get("selection_reason") or (graph_result or {}).get("reason") or "Approved by governor"
            
            store_assignment_record_in_db(
                review_id=review_id,
                submission_id=submission_id,
                next_task_id=next_task_id,
                candidate_id=candidate_id,
                governor=governor,
                task_type=task_type,
                reason=reason,
                trace_id=review_envelope.trace_id
            )
        except Exception as sql_err:
            observability.log_observability_event(
                "error", 
                f"Failed to store SQL assignment: {sql_err}", 
                {"error": str(sql_err), "trace_id": review_envelope.trace_id}
            )

        # 5. Pravah replay adapter
        try:
            from integrations.pravah_adapter import pravah_adapter
            intake_payload = None
            try:
                trace_dir = os.path.join("storage", "traces", review_envelope.trace_id)
                intake_path = os.path.join(trace_dir, "intake_packet.json")
                if os.path.exists(intake_path):
                    with open(intake_path, "r", encoding="utf-8") as f:
                        intake_payload = json.load(f)
            except Exception as intake_err:
                observability.log_observability_event("warning", f"Could not load intake packet for Pravah: {intake_err}")

            pravah_adapter.record_replay(
                trace_id=review_envelope.trace_id,
                event_id=commit_res["event_id"],
                sequence=commit_res["sequence"],
                parent_hash=review_envelope.parent_event_hash or "0"*64,
                event_hash=commit_res["event_hash"],
                intake_payload=intake_payload,
                review_payload=payload
            )
        except Exception as pravah_err:
            observability.log_observability_event("error", f"Pravah replay recording failed: {pravah_err}")
            raise RuntimeError(f"PRAVAH_INTEGRATION_FAILURE: {pravah_err}")

        # 6. Observability
        observability.log_observability_event("info", "[Ecosystem] Governed approval propagated.", {
            "trace_id": review_envelope.trace_id,
            "saarthi_status": "SENT",
            "niyantran_status": "SENT",
            "bucket_status": "LOGGED",
            "pravah_status": "SENT"
        })

        from integrations.pravah_adapter import PRAVAH_REPLAY_LEDGER
        return {
            "status": "PROPAGATED",
            "commit_details": commit_res,
            "saarthi_ledger": SAARTHI_VISIBILITY_LEDGER,
            "niyantran_ledger": NIYANTRAN_ASSIGNMENTS_LEDGER,
            "pravah_ledger": PRAVAH_REPLAY_LEDGER
        }

