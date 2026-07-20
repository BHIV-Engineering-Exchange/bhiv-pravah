# Product Core v1 - Quick Reference

## 🚀 Quick Start

### Basic Usage
```python
from app.services.product_orchestrator import ProductOrchestrator
from app.services.review_engine import ReviewEngine
from app.models.schemas import Task
from datetime import datetime

# Initialize
orchestrator = ProductOrchestrator(review_engine=ReviewEngine())

# Create task
task = Task(
    task_id="task-001",
    task_title="Your Task Title",
    task_description="Your task description with objectives and requirements.",
    submitted_by="Developer Name",
    timestamp=datetime.now()
)

# Process (deterministic)
result = orchestrator.process_submission(task)

# Access results
print(f"Score: {result['review']['score']}/100")
print(f"Status: {result['review']['status']}")
print(f"Next: {result['next_task']['title']}")
```

---

## 📦 Storage Access

### Retrieve Records
```python
from app.models.persistent_storage import product_storage

# Get submission
submission = product_storage.get_submission(result['submission_id'])
print(f"Submitted by: {submission.submitted_by}")
print(f"Status: {submission.status}")

# Get review
review = product_storage.get_review(result['review_id'])
print(f"Score: {review.score}")
print(f"Evaluated at: {review.reviewed_at}")

# Get next task
next_task = product_storage.get_next_task(result['next_task_id'])
print(f"Difficulty: {next_task.difficulty}")

# Find review by submission
review = product_storage.get_review_by_submission(result['submission_id'])
```

### Clear Storage (Testing)
```python
product_storage.clear_all()
```

---

## 📊 Response Structure

### Complete Response
```python
{
    "submission_id": "sub-abc123def456",
    "review_id": "rev-abc123def456",
    "next_task_id": "next-abc123def456",
    "review": {
        "score": 85,
        "readiness_percent": 85,
        "status": "pass",
        "failure_reasons": [],
        "improvement_hints": ["Keep up the good work"],
        "analysis": {
            "technical_quality": 90,
            "clarity": 85,
            "discipline_signals": 80
        }
    },
    "next_task": {
        "title": "Advanced System Design Challenge",
        "objective": "Design a distributed system...",
        "focus_area": "Architecture & Scalability",
        "difficulty": "advanced"
    }
}
```

---

## 🎯 Score Bands

| Score | Status | Next Task Difficulty |
|-------|--------|---------------------|
| 80-100 | pass | advanced |
| 50-79 | borderline | intermediate |
| 0-49 | fail | beginner |

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/test_persistent_storage.py -v
pytest tests/test_product_orchestrator.py -v
pytest tests/test_product_determinism.py -v
```

### Run Specific Test
```bash
pytest tests/test_product_determinism.py::test_determinism_100_iterations -v -s
```

---

## 🔍 Storage Models

### TaskSubmission
```python
TaskSubmission(
    submission_id="sub-...",      # Explicit ID
    task_id="task-...",            # Reference to original
    task_title="...",              # Task title
    task_description="...",        # Task description
    submitted_by="...",            # Submitter name
    submitted_at=datetime.now(),   # Explicit timestamp
    status=TaskStatus.SUBMITTED    # assigned/submitted/reviewed
)
```

### ReviewRecord
```python
ReviewRecord(
    review_id="rev-...",           # Explicit ID
    submission_id="sub-...",       # Links to submission
    score=85,                      # 0-100
    readiness_percent=85,          # 0-100
    status="pass",                 # pass/borderline/fail
    failure_reasons=[],            # List of issues
    improvement_hints=[],          # List of suggestions
    analysis={...},                # Quality metrics
    reviewed_at=datetime.now(),    # Explicit timestamp
    evaluation_time_ms=120         # Processing time
)
```

### NextTaskRecord
```python
NextTaskRecord(
    next_task_id="next-...",       # Explicit ID
    review_id="rev-...",           # Links to review
    title="...",                   # Task title
    objective="...",               # Task objective
    focus_area="...",              # Focus area
    difficulty="advanced",         # beginner/intermediate/advanced
    generated_at=datetime.now()    # Explicit timestamp
)
```

---

## ⚡ Key Features

### Deterministic Execution
- Same input → Same output (always)
- Fixed evaluation time: 120ms
- Score-based next task generation
- No randomness in logic

### Explicit Design
- All IDs are explicit parameters
- All timestamps are explicit
- No auto-generation magic
- Clear relationships

### Observable
- All operations store records
- Complete audit trail
- Relationship tracking
- Query by ID or relationship

### Testable
- 19 tests, 100% passing
- Determinism verified (100 iterations)
- Error handling tested
- Contract stability verified

---

## 🛠️ Error Handling

### Automatic Fallback
```python
# If review engine fails, returns:
{
    "review": {
        "score": 0,
        "status": "fail",
        "failure_reasons": ["Review engine error"],
        ...
    }
}
```

### Storage Always Works
- Submission stored even if review fails
- Review stored even if next task fails
- No exceptions propagated to caller

---

## 📝 Best Practices

1. **Always use explicit timestamps**
   ```python
   timestamp=datetime.now()  # Good
   ```

2. **Check result status**
   ```python
   if result['review']['status'] == 'pass':
       # Handle pass case
   ```

3. **Access storage after processing**
   ```python
   result = orchestrator.process_submission(task)
   submission = product_storage.get_submission(result['submission_id'])
   ```

4. **Clear storage in tests**
   ```python
   @pytest.fixture(autouse=True)
   def clear_storage():
       product_storage.clear_all()
       yield
       product_storage.clear_all()
   ```

---

## 📚 Documentation

- `PRODUCT_CORE_V1.md` - Branch documentation
- `PRODUCT_CORE_SUMMARY.md` - Implementation summary
- `INTEGRATION_VERIFICATION.md` - Test results and verification
- `PRODUCT_CORE_QUICK_REFERENCE.md` - This file

---

## 🔗 Related Files

**Core Implementation**:
- `app/models/persistent_storage.py` - Storage models
- `app/services/product_orchestrator.py` - Orchestrator service

**Tests**:
- `tests/test_persistent_storage.py` - Storage tests
- `tests/test_product_orchestrator.py` - Orchestrator tests
- `tests/test_product_determinism.py` - Determinism tests

**Interfaces** (unchanged):
- `app/core/interfaces/review_engine_interface.py`
- `app/models/schemas.py`

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2026-02-05
