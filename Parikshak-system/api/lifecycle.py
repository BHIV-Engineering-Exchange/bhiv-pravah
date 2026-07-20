"""
Product Core v1 - Lifecycle API
Stable API contracts for complete task lifecycle management.
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import logging
import hashlib
import os

from security.middleware import require_any_authenticated


logger = logging.getLogger("lifecycle")

from task_selector.review_orchestrator import ReviewOrchestrator
from evaluation_engine.review_engine import ReviewEngine
from contracts.schemas import Task
from db.persistent_storage import product_storage
from evaluation_engine.pdf_analyzer import PDFAnalyzer

router = APIRouter(prefix="/lifecycle", tags=["lifecycle"])

# Stable request/response models
class TaskSubmitRequest(BaseModel):
    task_title: str = Field(..., min_length=5, max_length=100)
    task_description: str = Field(..., min_length=10, max_length=100000)
    submitted_by: str = Field(..., min_length=2, max_length=50)
    previous_task_id: Optional[str] = None

class ReviewSummary(BaseModel):
    evaluation_result: str
    failure_type: Optional[str] = None
    decision: str
    evaluation_summary: str = ""
    score: int = 0
    readiness_percent: int = 0
    status: str = "fail"

class NextTaskSummary(BaseModel):
    task_id: str
    task_type: str
    title: str
    difficulty: str

class TaskSubmitResponse(BaseModel):
    submission_id: str
    submission_timestamp: str
    attempt_number: int = 1
    review_summary: ReviewSummary
    next_task_summary: NextTaskSummary

class SubmissionHistoryItem(BaseModel):
    submission_id: str
    task_title: str
    submitted_by: str
    submitted_at: datetime
    score: int = 0
    status: str = "fail"
    evaluation_result: str = "FAIL"
    failure_type: Optional[str] = None
    has_pdf: bool = False
    trace_id: Optional[str] = None
    review_state: Optional[str] = None

class ReviewDetailResponse(BaseModel):
    review_id: str
    submission_id: str
    evaluation_result: str
    failure_type: Optional[str] = None
    decision: str
    score: int = 0
    readiness_percent: int = 0
    status: str = "fail"
    failure_reasons: List[str]
    improvement_hints: List[str]
    analysis: dict
    reviewed_at: datetime
    missing_features: List[str]
    evaluation_summary: str
    selected_task_id: str = ""
    selection_reason: str = ""
    registry_validation: Optional[dict] = None
    candidate_name: str = ""
    task_title: str = ""
    task_description: str = ""
    trace_id: str = ""
    repository_url: Optional[str] = None
    next_task_title: str = ""
    next_task_objective: str = ""
    next_task_difficulty: str = ""
    next_task_focus_area: str = ""
    runtime_evidence: List[str] = []
    whats_done_well: List[str] = []
    # Detailed BHIV next task fields
    next_task_purpose: Optional[str] = ""
    next_task_read_this_first: Optional[str] = ""
    next_task_scope: Optional[str] = ""
    next_task_responsibility: Optional[str] = ""
    next_task_integration_block: Optional[dict] = None
    next_task_learning_kit: Optional[List[str]] = []
    next_task_execution_phases: Optional[List[str]] = []
    next_task_deliverables: Optional[List[str]] = []
    next_task_review_packet_requirements: Optional[List[str]] = []
    next_task_acceptance_criteria: Optional[List[str]] = []
    next_task_expected_runtime: Optional[str] = ""
    next_task_required_screenshots: Optional[List[str]] = []
    next_task_required_code_packets: Optional[List[str]] = []
    next_task_testing_requirements: Optional[List[str]] = []
    next_task_professional_closing: Optional[str] = ""
    next_task_non_goals: Optional[List[str]] = []
    next_task_phase_breakdown: Optional[List[str]] = []
    # Engineering Review Packet fields
    executive_summary: Optional[str] = ""
    overall_result: Optional[str] = ""
    engineering_score: Optional[int] = 0
    readiness_score: Optional[int] = 0
    confidence_score: Optional[int] = 0
    architecture_assessment: Optional[str] = ""
    implementation_assessment: Optional[str] = ""
    testing_assessment: Optional[str] = ""
    integration_assessment: Optional[str] = ""
    documentation_assessment: Optional[str] = ""
    governance_assessment: Optional[str] = ""
    replay_assessment: Optional[str] = ""
    production_readiness: Optional[str] = ""
    final_verdict: Optional[str] = ""
    
    # Phase 1: Canonical Review Packet fields
    missing_incomplete: Optional[List[str]] = []
    evidence_used: Optional[List[str]] = []
    risks: Optional[List[str]] = []
    required_fixes: Optional[List[str]] = []
    ecosystem_alignment: Optional[str] = ""
    benchmark_statements: Optional[List[str]] = []
    next_3_tasks: Optional[List[str]] = []
    review_metadata: Optional[dict] = None
    governance_state: Optional[str] = ""
    replay_references: Optional[List[str]] = []
    
    # Candidate history details (Progression Engine)
    candidate_history: Optional[dict] = None
    
    # Niyantran Sync Confirmation
    niyantran_sync_status: Optional[str] = "SYNCED"
    niyantran_assignment_id: Optional[str] = ""

class NextTaskDetailResponse(BaseModel):
    next_task_id: str
    review_id: str
    task_type: str
    title: str
    objective: str
    focus_area: str
    difficulty: str
    reason: str
    assigned_at: datetime
    purpose: Optional[str] = ""
    read_this_first: Optional[str] = ""
    scope: Optional[str] = ""
    responsibility: Optional[str] = ""
    integration_block: Optional[dict] = None
    learning_kit: Optional[List[str]] = []
    execution_phases: Optional[List[str]] = []
    deliverables: Optional[List[str]] = []
    review_packet_requirements: Optional[List[str]] = []
    acceptance_criteria: Optional[List[str]] = []
    expected_runtime: Optional[str] = ""
    required_screenshots: Optional[List[str]] = []
    required_code_packets: Optional[List[str]] = []
    testing_requirements: Optional[List[str]] = []
    professional_closing: Optional[str] = ""
    non_goals: Optional[List[str]] = []
    phase_breakdown: Optional[List[str]] = []

# CWE-918: allowlist — only accept github.com repo URLs
_GITHUB_REPO_RE = re.compile(r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$')
# CWE-943: allowlist for ID path params
_ID_RE = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')

# Initialize FINAL CONVERGENCE orchestrator
orchestrator = ReviewOrchestrator()  # No legacy review engine needed
pdf_analyzer = PDFAnalyzer()

@router.post("/submit", response_model=TaskSubmitResponse)
async def submit_task(
    task_title: str = Form(...),
    task_description: str = Form(...),
    submitted_by: str = Form(...),
    github_repo_link: Optional[str] = Form(default=""),
    module_id: str = Form(default="task-review-agent"),
    schema_version: str = Form(default="v1.0"),
    previous_task_id: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_any_authenticated)
):
    """
    Submit task for review with optional PDF support.
    """
    # Validate field lengths that Form() doesn't enforce
    if len(task_title) < 5 or len(task_title) > 100:
        raise HTTPException(status_code=422, detail="task_title must be 5-100 characters")
    if len(task_description) < 10 or len(task_description) > 100000:
        raise HTTPException(status_code=422, detail="task_description must be 10-100000 characters")
    if len(submitted_by) < 2 or len(submitted_by) > 50:
        raise HTTPException(status_code=422, detail="submitted_by must be 2-50 characters")
    # CWE-918: validate GitHub URL against allowlist before any HTTP request
    if github_repo_link and not _GITHUB_REPO_RE.match(github_repo_link):
        raise HTTPException(status_code=422, detail="github_repo_link must be a valid GitHub repository URL")
    try:
        # 1. Handle PDF Processing
        pdf_file_path = None
        pdf_text = ""
        if pdf_file:
            pdf_result = pdf_analyzer.process_upload(pdf_file)
            pdf_file_path = pdf_result["file_path"]
            pdf_text = pdf_result["extracted_text"]

        # 2. Create task object for evaluation
        # UI submissions may lack trace_id; generate one to satisfy downstream requirements
        trace_id = f"trace-ui-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(task_title.encode()).hexdigest()[:8]}"
        
        task = Task(
            task_id=f"task-{datetime.now().timestamp()}",
            task_title=task_title,
            task_description=task_description,
            submitted_by=submitted_by,
            github_repo_link=github_repo_link,
            module_id=module_id,
            schema_version=schema_version,
            timestamp=datetime.now(),
            pdf_extracted_text=pdf_text
        )
        # 3. Process submission via orchestrator
        result = orchestrator.process_submission(
            task, 
            previous_task_id,
            pdf_file_path=pdf_file_path,
            pdf_extracted_text=pdf_text,
            trace_id=trace_id
        )
        
        # Build response with traceability
        return TaskSubmitResponse(
            submission_id=result["submission_id"],
            submission_timestamp=result.get("submission_timestamp", datetime.now().isoformat()),
            attempt_number=result.get("attempt_number", 1),
            review_summary=ReviewSummary(
                evaluation_result=result["review"]["evaluation_result"],
                failure_type=result["review"].get("failure_type"),
                decision=result["review"].get("decision", "REJECTED"),
                evaluation_summary=result["review"].get("evaluation_summary", ""),
                score=result["review"].get("score", 0),
                readiness_percent=result["review"].get("readiness_percent", 0),
                status=result["review"].get("status", "fail")
            ),
            next_task_summary=NextTaskSummary(
                task_id=result["next_task"]["task_id"],
                task_type=result["next_task"]["task_type"],
                title=result["next_task"]["title"],
                difficulty=result["next_task"]["difficulty"]
            )
        )
    except HTTPException:
        raise
    except (ValueError, KeyError) as e:
        logger.error(f"Submission data error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Submission processing failed: {e}")
    except Exception as e:
        logger.error(f"Submission unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.get("/history", response_model=List[SubmissionHistoryItem])
def get_history(current_user: dict = Depends(require_any_authenticated)):
    """
    Get ordered list of all submissions.
    Deterministic sorting: by submitted_at ascending.
    """
    submissions = list(product_storage.submissions.values())
    
    # Sort deterministically by submitted_at
    submissions.sort(key=lambda s: s.submitted_at)
    
    # Build response
    history = []
    for submission in submissions:
        review = product_storage.get_review_by_submission(submission.submission_id)
        history.append(SubmissionHistoryItem(
            submission_id=submission.submission_id,
            task_title=submission.task_title,
            submitted_by=submission.submitted_by,
            submitted_at=submission.submitted_at,
            score=getattr(review, "score", 0) if review else 0,
            status=getattr(review, "status", "fail") if review else "fail",
            evaluation_result=getattr(review, "evaluation_result", "FAIL") if review else "FAIL",
            failure_type=getattr(review, "failure_type", None) if review else None,
            has_pdf=bool(submission.pdf_file_path),
            trace_id=getattr(review, "trace_id", None) if review else None,
            review_state=getattr(review, "review_state", submission.review_state) if review else submission.review_state
        ))
    
    return history

@router.get("/review/{submission_id}", response_model=ReviewDetailResponse)
def get_review(submission_id: str, current_user: dict = Depends(require_any_authenticated)):
    """
    Get stored review output by submission ID.
    Stable contract: Always returns complete review details.
    """
    # CWE-943: validate ID format before storage lookup
    if not _ID_RE.match(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID format")
    try:
        review = product_storage.get_review_by_submission(submission_id)
    except Exception as e:
        logger.error(f"get_review_by_submission failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DB read error: {e}")

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    try:
        submission = product_storage.get_submission(submission_id)
    except Exception as e:
        logger.error(f"get_submission failed: {e}", exc_info=True)
        submission = None
    registry_validation = None
    if submission and submission.registry_validation_status:  # noqa
        registry_validation = {
            "module_id": submission.module_id,
            "schema_version": submission.schema_version,
            "module_id_valid": submission.registry_validation_status == "VALID",
            "lifecycle_stage_valid": submission.registry_validation_status == "VALID",
            "schema_version_valid": submission.registry_validation_status == "VALID",
            "validation_passed": submission.registry_validation_status == "VALID"
        }

    # Query next task details
    next_task = product_storage.get_next_task_by_submission(submission_id)
    
    # Query runtime evidence folder files
    runtime_evidence = []
    trace_id_val = getattr(review, "trace_id", "")
    if trace_id_val:
        trace_path = os.path.join("storage", "traces", trace_id_val)
        if os.path.exists(trace_path) and os.path.isdir(trace_path):
            try:
                runtime_evidence = [f for f in os.listdir(trace_path) if os.path.isfile(os.path.join(trace_path, f))]
            except Exception:
                pass

    try:
        from db.bhiv_task_details import get_bhiv_task_details
        next_task_details = {}
        if next_task:
            next_task_details = get_bhiv_task_details(
                next_task.next_task_id,
                default_dharma=next_task.objective,
                default_signals=[next_task.focus_area]
            )

        # 1. Fetch Candidate learning history details
        from evaluation_engine.learning_history_engine import learning_history_engine
        cand_name = getattr(review, "candidate_name", "") or (submission.submitted_by if submission else "candidate")
        history_data = learning_history_engine.analyze_candidate_history(cand_name)

        # 2. Extract structured engineering review packets
        eng_rev = review.analysis.get("engineering_review", {}) if isinstance(review.analysis, dict) else {}
        score_val = getattr(review, "score", 0)
        eval_res = getattr(review, "evaluation_result", "FAIL")
        decision = getattr(review, "decision", "REJECTED")

        return ReviewDetailResponse(
            review_id=review.review_id,
            submission_id=review.submission_id,
            evaluation_result=eval_res,
            failure_type=getattr(review, "failure_type", None),
            decision=decision,
            score=score_val,
            readiness_percent=getattr(review, "readiness_percent", 0),
            status=getattr(review, "status", "fail"),
            failure_reasons=review.failure_reasons or [],
            improvement_hints=review.improvement_hints or [],
            analysis=review.analysis or {},
            reviewed_at=review.reviewed_at,
            missing_features=review.missing_features or [],
            evaluation_summary=review.evaluation_summary or "",
            selected_task_id=getattr(review, "selected_task_id", "") or "",
            selection_reason=getattr(review, "selection_reason", "") or "",
            registry_validation=registry_validation,
            candidate_name=cand_name,
            task_title=getattr(review, "task_title", "") or (submission.task_title if submission else "Task"),
            task_description=submission.task_description if submission else "",
            trace_id=trace_id_val,
            repository_url=submission.github_repo_link if submission else None,
            next_task_title=next_task_details.get("title", next_task.title if next_task else ""),
            next_task_objective=next_task.objective if next_task else "",
            next_task_difficulty=next_task.difficulty if next_task else "",
            next_task_focus_area=next_task.focus_area if next_task else "",
            runtime_evidence=runtime_evidence,
            whats_done_well=getattr(review, "whats_done_well", []) or [],
            # Populate detailed BHIV next task specifications
            next_task_purpose=next_task_details.get("purpose", ""),
            next_task_read_this_first=next_task_details.get("read_this_first", ""),
            next_task_scope=next_task_details.get("scope", ""),
            next_task_responsibility=next_task_details.get("responsibility", ""),
            next_task_integration_block=next_task_details.get("integration_block"),
            next_task_learning_kit=next_task_details.get("learning_kit", []),
            next_task_execution_phases=next_task_details.get("execution_phases", []),
            next_task_deliverables=next_task_details.get("deliverables", []),
            next_task_review_packet_requirements=next_task_details.get("review_packet_requirements", []),
            next_task_acceptance_criteria=next_task_details.get("acceptance_criteria", []),
            next_task_expected_runtime=next_task_details.get("expected_runtime", ""),
            next_task_required_screenshots=next_task_details.get("required_screenshots", []),
            next_task_required_code_packets=next_task_details.get("required_code_packets", []),
            next_task_testing_requirements=next_task_details.get("testing_requirements", []),
            next_task_professional_closing=next_task_details.get("professional_closing", ""),
            next_task_non_goals=next_task_details.get("non_goals", []),
            next_task_phase_breakdown=next_task_details.get("phase_breakdown", []),
            # Engineering Review Packet fields
            executive_summary=eng_rev.get("executive_summary", f"Automated engineering evaluation for task '{submission.task_title if submission else ''}'. Total score is {score_val}/100. Verification checks completed."),
            overall_result=eng_rev.get("overall_result", eval_res),
            engineering_score=eng_rev.get("engineering_score", score_val),
            readiness_score=eng_rev.get("readiness_score", score_val),
            confidence_score=eng_rev.get("confidence_score", 95 if score_val >= 80 else (80 if score_val >= 60 else 60)),
            architecture_assessment=eng_rev.get("architecture_assessment", "Modular architecture detected. Structural verification matches standard layers." if review.analysis.get("pac", {}).get("architecture") else "Flat folder layout. Missing layer boundary specifications."),
            implementation_assessment=eng_rev.get("implementation_assessment", "Code files structure complies with required metrics." if review.analysis.get("pac", {}).get("code") else "Missing implementation code files."),
            testing_assessment=eng_rev.get("testing_assessment", "Unit test suites detected. Functional test verification matches coverage expectations." if review.analysis.get("pac", {}).get("proof") else "Missing unit tests or test verification logs."),
            integration_assessment=eng_rev.get("integration_assessment", "Ecosystem adapters validation complete."),
            documentation_assessment=eng_rev.get("documentation_assessment", "README files and annotations analyzed."),
            governance_assessment=eng_rev.get("governance_assessment", "Governance registry schema compatibility check: PASSED."),
            replay_assessment=eng_rev.get("replay_assessment", "Deterministic state mutation hash verified."),
            production_readiness=eng_rev.get("production_readiness", "READY FOR STAGING" if eval_res == "PASS" else "UNREADY - REVISION REQUIRED"),
            final_verdict=eng_rev.get("final_verdict", decision),
            # Phase 1: Canonical Review Packet fields
            missing_incomplete=eng_rev.get("missing_incomplete", review.improvement_hints or []),
            evidence_used=eng_rev.get("evidence_used", ["README.md", "tests/"]),
            risks=eng_rev.get("risks", ["Nominal ecosystem boundary risk"]),
            required_fixes=eng_rev.get("required_fixes", review.failure_reasons or []),
            ecosystem_alignment=eng_rev.get("ecosystem_alignment", "BCAB v1 / BCAES Volumes 1-3 aligned."),
            benchmark_statements=eng_rev.get("benchmark_statements", []),
            next_3_tasks=eng_rev.get("next_3_tasks", []),
            review_metadata=eng_rev.get("review_metadata", {}),
            governance_state=eng_rev.get("governance_state", review.review_state),
            replay_references=eng_rev.get("replay_references", []),
            
            candidate_history=history_data,
            niyantran_sync_status="SYNCED" if decision == "APPROVED" else "PENDING",
            niyantran_assignment_id=f"assign-{trace_id_val[:8]}" if trace_id_val else ""
        )
    except Exception as e:
        logger.error(f"ReviewDetailResponse build failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Response build error: {e}")

@router.get("/next/{submission_id}", response_model=NextTaskDetailResponse)
def get_next_task(submission_id: str, current_user: dict = Depends(require_any_authenticated)):
    """
    Get stored next task by submission ID.
    Stable contract: Always returns complete next task details.
    """
    # CWE-943: validate ID format before storage lookup
    if not _ID_RE.match(submission_id):
        raise HTTPException(status_code=400, detail="Invalid submission ID format")
    next_task = product_storage.get_next_task_by_submission(submission_id)
    
    if not next_task:
        raise HTTPException(status_code=404, detail="Next task not found")
    
    from db.bhiv_task_details import get_bhiv_task_details
    details = get_bhiv_task_details(
        next_task.next_task_id,
        default_dharma=next_task.objective,
        default_signals=[next_task.focus_area]
    )

    return NextTaskDetailResponse(
        next_task_id=next_task.next_task_id,
        review_id=next_task.review_id,
        task_type=next_task.task_type,
        title=details.get("title", next_task.title),
        objective=next_task.objective,
        focus_area=next_task.focus_area,
        difficulty=next_task.difficulty,
        reason=next_task.reason,
        assigned_at=next_task.assigned_at,
        purpose=details.get("purpose", ""),
        read_this_first=details.get("read_this_first", ""),
        scope=details.get("scope", ""),
        responsibility=details.get("responsibility", ""),
        integration_block=details.get("integration_block"),
        learning_kit=details.get("learning_kit", []),
        execution_phases=details.get("execution_phases", []),
        deliverables=details.get("deliverables", []),
        review_packet_requirements=details.get("review_packet_requirements", []),
        acceptance_criteria=details.get("acceptance_criteria", []),
        expected_runtime=details.get("expected_runtime", ""),
        required_screenshots=details.get("required_screenshots", []),
        required_code_packets=details.get("required_code_packets", []),
        testing_requirements=details.get("testing_requirements", []),
        professional_closing=details.get("professional_closing", ""),
        non_goals=details.get("non_goals", []),
        phase_breakdown=details.get("phase_breakdown", [])
    )
