# Product Core v1 - Storage Layer Documentation

**Version**: 1.2.0  
**Implementation**: `app/models/persistent_storage.py`  
**Storage Type**: In-Memory (Dict-based)

---

## Storage Architecture

```
ProductStorage
├── submissions: Dict[str, TaskSubmission]
├── reviews: Dict[str, ReviewRecord]
└── next_tasks: Dict[str, NextTaskRecord]
```

---

## Table 1: TaskSubmission

### Purpose
Immutable record of task submission with lifecycle tracking.

### Fields

| Field | Type | Required | Description | Lifecycle Role |
|-------|------|----------|-------------|----------------|
| submission_id | str | Yes | Unique identifier (format: `sub-{uuid}`) | Primary key |
| task_id | str | Yes | Reference to original task | External reference |
| task_title | str | Yes | Task title (5-100 chars) | Display |
| task_description | str | Yes | Task description (10-100000 chars) | Review input |
| submitted_by | str | Yes | Submitter name (2-50 chars) | Attribution |
| submitted_at | datetime | Yes | Submission timestamp | Ordering |
| status | TaskStatus | Yes | Lifecycle status (default: SUBMITTED) | State tracking |
| previous_task_id | str | No | Reference to previous task | Lifecycle chain |

### Data Types
```python
submission_id: str          # "sub-a1b2c3d4e5f6"
task_id: str                # "task-123"
task_title: str             # "Build Authentication System"
task_description: str       # "Objective: Implement..."
submitted_by: str           # "Developer Name"
submitted_at: datetime      # datetime(2026, 2, 5, 10, 0, 0)
status: TaskStatus          # "submitted" (enum value)
previous_task_id: str|None  # "prev-task-001" or None
```

### Lifecycle Role
- **Entry Point**: First entity created in submission flow
- **Links To**: ReviewRecord (via submission_id)
- **Tracks**: Submission history and task progression
- **Immutable**: Once created, never modified

### Validation
```python
task_title: min_length=5, max_length=100
task_description: min_length=10, max_length=100000
submitted_by: min_length=2, max_length=50
status: Enum(ASSIGNED, SUBMITTED, REVIEWED)
```

---

## Table 2: ReviewRecord

### Purpose
Immutable record of review output with complete analysis.

### Fields

| Field | Type | Required | Description | Lifecycle Role |
|-------|------|----------|-------------|----------------|
| review_id | str | Yes | Unique identifier (format: `rev-{uuid}`) | Primary key |
| submission_id | str | Yes | Links to TaskSubmission | Foreign key |
| score | int | Yes | Total score (0-100) | Quality metric |
| readiness_percent | int | Yes | Readiness percentage (0-100) | Readiness metric |
| status | str | Yes | Review status (pass/borderline/fail) | Classification |
| failure_reasons | list[str] | Yes | List of failure reasons | Feedback |
| improvement_hints | list[str] | Yes | List of improvement suggestions | Guidance |
| analysis | Dict[str, int] | Yes | Component scores | Detailed breakdown |
| reviewed_at | datetime | Yes | Review timestamp | Audit trail |
| evaluation_time_ms | int | Yes | Processing time | Performance metric |

### Data Types
```python
review_id: str                    # "rev-a1b2c3d4e5f6"
submission_id: str                # "sub-a1b2c3d4e5f6"
score: int                        # 75 (0-100)
readiness_percent: int            # 70 (0-100)
status: str                       # "borderline"
failure_reasons: list[str]        # ["Missing tests", "Low commit count"]
improvement_hints: list[str]      # ["Add unit tests", "Increase commits"]
analysis: Dict[str, int]          # {"technical_quality": 80, "clarity": 70, ...}
reviewed_at: datetime             # datetime(2026, 2, 5, 10, 0, 1)
evaluation_time_ms: int           # 120
```

### Lifecycle Role
- **Created After**: ReviewEngine evaluation
- **Links From**: TaskSubmission (via submission_id)
- **Links To**: NextTaskRecord (via review_id)
- **Provides**: Quality assessment and feedback
- **Immutable**: Once created, never modified

### Validation
```python
score: ge=0, le=100
readiness_percent: ge=0, le=100
status: pattern="^(pass|borderline|fail)$"
analysis: Dict with keys: technical_quality, clarity, discipline_signals
```

### Analysis Structure
```python
{
  "technical_quality": int (0-100),    # Repo/technical metrics
  "clarity": int (0-100),              # Description quality
  "discipline_signals": int (0-100)    # PDF/documentation quality
}
```

---

## Table 3: NextTaskRecord

### Purpose
Immutable record of next task assignment with reasoning.

### Fields

| Field | Type | Required | Description | Lifecycle Role |
|-------|------|----------|-------------|----------------|
| next_task_id | str | Yes | Unique identifier (format: `next-{uuid}`) | Primary key |
| review_id | str | Yes | Links to ReviewRecord | Foreign key |
| previous_submission_id | str | Yes | Links to TaskSubmission | Lifecycle chain |
| task_type | str | Yes | Assignment type (correction/reinforcement/advancement) | Classification |
| title | str | Yes | Task title (min 5 chars) | Display |
| objective | str | Yes | Task objective (min 10 chars) | Goal |
| focus_area | str | Yes | Focus area (min 3 chars) | Category |
| difficulty | str | Yes | Difficulty level (beginner/intermediate/advanced) | Level |
| reason | str | Yes | Assignment reason | Explanation |
| assigned_at | datetime | Yes | Assignment timestamp | Audit trail |

### Data Types
```python
next_task_id: str              # "next-a1b2c3d4e5f6"
review_id: str                 # "rev-a1b2c3d4e5f6"
previous_submission_id: str    # "sub-a1b2c3d4e5f6"
task_type: str                 # "reinforcement"
title: str                     # "Intermediate Task Structuring"
objective: str                 # "Build well-defined tasks..."
focus_area: str                # "Technical Documentation"
difficulty: str                # "intermediate"
reason: str                    # "Score in borderline range..."
assigned_at: datetime          # datetime(2026, 2, 5, 10, 0, 2)
```

### Lifecycle Role
- **Created After**: NextTaskGenerator assignment
- **Links From**: ReviewRecord (via review_id)
- **Links From**: TaskSubmission (via previous_submission_id)
- **Provides**: Next step guidance
- **Immutable**: Once created, never modified

### Validation
```python
task_type: pattern="^(correction|reinforcement|advancement)$"
title: min_length=5
objective: min_length=10
focus_area: min_length=3
difficulty: pattern="^(beginner|intermediate|advanced)$"
```

---

## Relationships

```
TaskSubmission (1) ──────> (1) ReviewRecord
     │                           │
     │                           │
     └──────────────────> (1) NextTaskRecord
```

### Relationship Details

1. **TaskSubmission → ReviewRecord**
   - Type: One-to-One
   - Key: submission_id
   - Query: `get_review_by_submission(submission_id)`

2. **ReviewRecord → NextTaskRecord**
   - Type: One-to-One
   - Key: review_id
   - Stored in: NextTaskRecord.review_id

3. **TaskSubmission → NextTaskRecord**
   - Type: One-to-One
   - Key: previous_submission_id
   - Query: `get_next_task_by_submission(submission_id)`

---

## Storage Operations

### Create Operations
```python
# Store submission
product_storage.store_submission(submission: TaskSubmission) -> None

# Store review
product_storage.store_review(review: ReviewRecord) -> None

# Store next task
product_storage.store_next_task(next_task: NextTaskRecord) -> None
```

### Read Operations
```python
# Get by ID
product_storage.get_submission(submission_id: str) -> Optional[TaskSubmission]
product_storage.get_review(review_id: str) -> Optional[ReviewRecord]
product_storage.get_next_task(next_task_id: str) -> Optional[NextTaskRecord]

# Get by relationship
product_storage.get_review_by_submission(submission_id: str) -> Optional[ReviewRecord]
product_storage.get_next_task_by_submission(submission_id: str) -> Optional[NextTaskRecord]

# Get lifecycle
product_storage.get_lifecycle(submission_id: str) -> Optional[Dict[str, Any]]
```

### Utility Operations
```python
# Clear all (testing only)
product_storage.clear_all() -> None
```

---

## Lifecycle Query

### get_lifecycle(submission_id)
Returns complete lifecycle for a submission.

**Returns**:
```python
{
  "submission": TaskSubmission,      # Full submission object
  "review": ReviewRecord,            # Full review object (or None)
  "next_task": NextTaskRecord,       # Full next task object (or None)
  "status": str,                     # Current status
  "previous_task_id": str|None       # Previous task reference
}
```

**Use Case**: Retrieve complete history for a submission

---

## Storage Characteristics

### In-Memory Implementation
- **Type**: Python Dict
- **Thread Safety**: NO (single-threaded only)
- **Persistence**: NO (data lost on restart)
- **Performance**: O(1) for get/set operations

### Capacity Management
- **Limit**: 1000 submissions (configurable)
- **Eviction**: FIFO (oldest first)
- **Implementation**: OrderedDict with size limit

### Production Considerations
- **Replace with**: PostgreSQL, MongoDB, or similar
- **Migration Path**: Implement same interface
- **No Code Changes**: Storage interface remains same

---

## Data Integrity

### Constraints
1. **Primary Keys**: Must be unique (enforced by dict)
2. **Foreign Keys**: Not enforced (application-level)
3. **Immutability**: Enforced by not providing update methods
4. **Validation**: Enforced by Pydantic models

### Orphan Prevention
- Application ensures submission exists before storing review
- Application ensures review exists before storing next task
- Verified in stability tests (0 orphaned records)

---

## Migration Guide

### From In-Memory to Database

**Step 1**: Implement storage interface
```python
class DatabaseStorage:
    def store_submission(self, submission: TaskSubmission) -> None:
        # INSERT INTO submissions ...
        
    def get_submission(self, submission_id: str) -> Optional[TaskSubmission]:
        # SELECT * FROM submissions WHERE id = ...
```

**Step 2**: Replace global instance
```python
# Old: product_storage = ProductStorage()
# New: product_storage = DatabaseStorage()
```

**Step 3**: No other code changes required
- Orchestrator uses same interface
- API uses same interface
- Tests use same interface

---

**Document Status**: COMPLETE  
**Matches Implementation**: YES  
**All Fields Documented**: YES  
**Lifecycle Roles Defined**: YES
