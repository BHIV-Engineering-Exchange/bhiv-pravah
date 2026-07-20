import pytest
from datetime import datetime
from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from contracts.schemas import Task
from db.persistent_storage import product_storage
from task_selector.architectural_registry import validate_task_architecture

class TestArchitecturalGovernance:
    def setup_method(self):
        self.orchestrator = ReviewOrchestrator(review_engine=ReviewEngine())
        product_storage.clear_all()

    def test_canonical_taxonomy_valid(self):
        """Valid taxonomy combinations should pass validation without error."""
        # parikshak: evaluation_engine, governance, task_review
        validate_task_architecture(
            program="BHIV",
            product="parikshak",
            platform_service="evaluation_engine",
            domain="governance",
            capability="task_review"
        )
        # niyantran: task_orchestration, execution, graph_traversal
        validate_task_architecture(
            program="TANTRA",
            product="niyantran",
            platform_service="task_orchestration",
            domain="execution",
            capability="graph_traversal"
        )

    def test_authority_drift_program_rejected(self):
        """Authority Drift: Declaring the wrong program should raise ValueError."""
        with pytest.raises(ValueError, match="Authority Drift detected"):
            validate_task_architecture(
                program="BHIV",  # Should be TANTRA
                product="niyantran",
                platform_service="task_orchestration",
                domain="execution",
                capability="graph_traversal"
            )

    def test_architectural_misclassification_service_rejected(self):
        """Architectural Misclassification: Wrong service should raise ValueError."""
        with pytest.raises(ValueError, match="Architectural Misclassification"):
            validate_task_architecture(
                program="BHIV",
                product="parikshak",
                platform_service="task_orchestration",  # Should be evaluation_engine
                domain="governance",
                capability="task_review"
            )

    def test_authority_drift_capability_rejected(self):
        """Authority Drift: Declaring capability not owned by the product should raise ValueError."""
        with pytest.raises(ValueError, match="Authority Drift"):
            validate_task_architecture(
                program="BHIV",
                product="parikshak",
                platform_service="evaluation_engine",
                domain="governance",
                capability="graph_traversal"  # Owned by niyantran
            )

    def test_orchestrator_governed_pipeline_no_auto_assignment(self):
        """
        Governed Pipeline: Submitting a valid task should NOT trigger
        Niyantran assignment automatically. It should remain PENDING_REVIEW.
        """
        task = Task(
            task_id="T-GOV-001",  # Valid task id in niyantran_tasks.json
            task_title="Sri Satya Completeness Check Validation",
            task_description="Implement check validation for Sri Satya completeness metrics.",
            submitted_by="Governance Tester",
            timestamp=datetime.now(),
            module_id="task-review-agent",
            schema_version="v1.0",
            github_repo_link="https://github.com/tester/repo"
        )

        result = self.orchestrator.process_submission(task)

        # 1. Review is created but remains in PENDING_REVIEW state
        assert "submission_id" in result
        review = product_storage.get_review(result["review_id"])
        assert review is not None
        assert review.review_state == "PENDING_REVIEW"

        # 2. No assignment is written to the SQL assignments table yet
        from db.db_config import SessionLocal
        from db.models import AssignmentModel
        db = SessionLocal()
        try:
            assignment = db.query(AssignmentModel).filter(AssignmentModel.previous_submission_id == result["submission_id"]).first()
            assert assignment is None, "Assignment should not be generated automatically before human approval!"
        finally:
            db.close()
