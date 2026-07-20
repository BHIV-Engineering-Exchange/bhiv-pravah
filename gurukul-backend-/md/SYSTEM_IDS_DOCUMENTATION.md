# System IDs Documentation

Complete reference guide for all ID fields used in Gurukul and EMS System.

---

## 📋 Table of Contents

1. [Gurukul System IDs](#gurukul-system-ids)
2. [EMS System IDs](#ems-system-ids)
3. [ID Relationships & Syncing](#id-relationships--syncing)
4. [ID Naming Conventions](#id-naming-conventions)
5. [Database Schema Reference](#database-schema-reference)

---

## 🎓 Gurukul System IDs

### 1. User IDs

**Model**: `User`  
**Table**: `users`  
**ID Field**: `id`  
**Type**: String (UUID)  
**Example**: `"550e8400-e29b-41d4-a716-446655440000"`

**Related Fields**:
- `user_id` - Foreign key used in other tables to reference users
- `tenant_id` - Links user to a tenant/organization
- `cohort_id` - Links student to a class/cohort
- `parent_id` - Links student to parent user

---

### 2. Summary IDs

**Model**: `Summary`  
**Table**: `summaries`  
**ID Field**: `id`  
**Type**: String (UUID)  
**Example**: `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"`

**Fields**:
```python
id = Column(String, primary_key=True, default=generate_uuid)
user_id = Column(String, ForeignKey("users.id"))
title = Column(String)
content = Column(Text)
source = Column(String)
source_type = Column(String)
created_at = Column(DateTime)
```

**API Endpoints**:
- `GET /api/v1/learning/summaries` - Get all summaries
- `POST /api/v1/learning/summaries/save` - Create summary
- Returns: `{"id": "...", "title": "...", "content": "..."}`

**Usage in MyContent**: Displayed as `summary.id`

---

### 3. Flashcard IDs

**Model**: `Flashcard`  
**Table**: `flashcards`  
**ID Field**: `id`  
**Type**: String (UUID)  
**Example**: `"b2c3d4e5-f6a7-8901-bcde-f12345678901"`

**Fields**:
```python
id = Column(String, primary_key=True, default=generate_uuid)
user_id = Column(String, ForeignKey("users.id"))
question = Column(Text)
answer = Column(Text)
question_type = Column(String, default="conceptual")
days_until_review = Column(Integer, default=0)
confidence = Column(Float, default=0.0)
created_at = Column(DateTime)
```

**API Endpoints**:
- `GET /api/v1/flashcards` - Get all flashcards
- `POST /api/v1/flashcards/generate` - Generate flashcards
- Returns: `{"id": "...", "question": "...", "answer": "..."}`

**Usage in MyContent**: Displayed as `flashcard.id`

---

### 4. Test Result IDs

**Model**: `TestResult`  
**Table**: `test_results`  
**ID Field**: `id`  
**Type**: String (UUID)  
**Example**: `"c3d4e5f6-a7b8-9012-cdef-123456789012"`

**Fields**:
```python
id = Column(String, primary_key=True, default=generate_uuid)
user_id = Column(String, ForeignKey("users.id"))
subject = Column(String)
topic = Column(String)
difficulty = Column(String, default="medium")
num_questions = Column(Integer)
questions = Column(JSON)  # All questions with options
user_answers = Column(JSON)  # Student's answers
score = Column(Integer)
total_questions = Column(Integer)
percentage = Column(Float)
time_taken = Column(Integer)
created_at = Column(DateTime)
synced_to_ems = Column(Boolean, default=False)
ems_sync_id = Column(String)  # EMS record ID after sync
```

**API Endpoints**:
- `GET /api/v1/quiz/results` - Get all test results
- `POST /api/v1/quiz/submit` - Submit test
- Returns: `{"id": "...", "subject": "...", "score": 85, "percentage": 85.0}`

**Usage in MyContent**: Displayed as `test_result.id`

---

### 5. Subject Data IDs

**Model**: `SubjectData`  
**Table**: `subject_data`  
**ID Field**: `id`  
**Type**: String (UUID)  
**Example**: `"d4e5f6a7-b8c9-0123-def0-234567890123"`

**Fields**:
```python
id = Column(String, primary_key=True, default=generate_uuid)
user_id = Column(String, ForeignKey("users.id"))
subject = Column(String)
topic = Column(String)
notes = Column(Text)  # Generated educational content
provider = Column(String, default="groq")  # LLM provider
youtube_recommendations = Column(JSON, default=[])
created_at = Column(DateTime)
synced_to_ems = Column(Boolean, default=False)
ems_sync_id = Column(String)  # EMS record ID after sync
```

**API Endpoints**:
- `GET /api/v1/learning/subject-data` - Get all subject data
- `POST /api/v1/learning/explore` - Create subject exploration
- Returns: `{"id": "...", "subject": "...", "topic": "...", "notes": "..."}`

**Usage in MyContent**: Displayed as `subject_data.id`

---

### 6. Other Gurukul Model IDs

#### Profile
- **Model**: `Profile`
- **ID Field**: `id` (UUID)
- **Table**: `profiles`
- **Links to**: `users.id` via `user_id`

#### Reflection
- **Model**: `Reflection`
- **ID Field**: `id` (UUID)
- **Table**: `reflections`
- **Links to**: `users.id` via `user_id`

#### Tenant
- **Model**: `Tenant`
- **ID Field**: `id` (UUID)
- **Table**: `tenants`
- **Purpose**: Organization/institution grouping

#### Cohort
- **Model**: `Cohort`
- **ID Field**: `id` (UUID)
- **Table**: `cohorts`
- **Links to**: `tenants.id` via `tenant_id`

---

## 🏫 EMS System IDs

### 1. User IDs

**Model**: `User`  
**Table**: `users`  
**ID Field**: `id`  
**Type**: Integer  
**Example**: `1`, `42`, `100`

**Related Fields**:
- `school_id` - Links user to a school
- `role` - User role (SUPER_ADMIN, ADMIN, TEACHER, STUDENT, PARENT)

---

### 2. Lesson IDs

**Model**: `Lesson`  
**Table**: `lessons`  
**ID Field**: `id`  
**Type**: Integer  
**Example**: `1`, `25`, `100`

**Fields**:
```python
id = Column(Integer, primary_key=True, index=True)
title = Column(String(255))
description = Column(Text)
class_id = Column(Integer, ForeignKey("classes.id"))
teacher_id = Column(Integer, ForeignKey("users.id"))
school_id = Column(Integer, ForeignKey("schools.id"))
lesson_date = Column(Date)
created_at = Column(DateTime)
```

**API Endpoints**:
- `GET /teacher/lessons` - Get teacher's lessons
- `POST /teacher/lessons` - Create lesson
- `PUT /teacher/lessons/{lesson_id}` - Update lesson
- `DELETE /teacher/lessons/{lesson_id}` - Delete lesson

**Related**: `Lecture` model has `lesson_id` (foreign key to `lessons.id`)

---

### 3. Lecture IDs

**Model**: `Lecture`  
**Table**: `lectures`  
**ID Field**: `id`  
**Type**: Integer  
**Links to**: `lessons.id` via `lesson_id`

**Fields**:
```python
id = Column(Integer, primary_key=True, index=True)
lesson_id = Column(Integer, ForeignKey("lessons.id"))
title = Column(String(255))
content = Column(Text)
lecture_date = Column(Date)
start_time = Column(Time)
end_time = Column(Time)
created_at = Column(DateTime)
```

---

### 4. Student Summary IDs (Synced from Gurukul)

**Model**: `StudentSummary`  
**Table**: `student_summaries`  
**ID Field**: `id`  
**Type**: Integer  
**Gurukul Reference**: `gurukul_id` (String, UUID)

**Fields**:
```python
id = Column(Integer, primary_key=True, index=True)
student_id = Column(Integer, ForeignKey("users.id"))
school_id = Column(Integer, ForeignKey("schools.id"))
gurukul_id = Column(String(255), unique=True, index=True)  # ← Links to Gurukul Summary.id
title = Column(String(500))
content = Column(Text)
source = Column(String(500))
source_type = Column(String(50))
created_at = Column(DateTime)
synced_at = Column(DateTime)
```

**Relationship**: 
- `gurukul_id` = Gurukul `Summary.id`
- `id` = EMS internal ID

---

### 5. Student Flashcard IDs (Synced from Gurukul)

**Model**: `StudentFlashcard`  
**Table**: `student_flashcards`  
**ID Field**: `id`  
**Type**: Integer  
**Gurukul Reference**: `gurukul_id` (String, UUID)

**Fields**:
```python
id = Column(Integer, primary_key=True, index=True)
student_id = Column(Integer, ForeignKey("users.id"))
school_id = Column(Integer, ForeignKey("schools.id"))
gurukul_id = Column(String(255), unique=True, index=True)  # ← Links to Gurukul Flashcard.id
question = Column(Text)
answer = Column(Text)
question_type = Column(String(50))
days_until_review = Column(Integer)
confidence = Column(Float)
created_at = Column(DateTime)
synced_at = Column(DateTime)
```

**Relationship**: 
- `gurukul_id` = Gurukul `Flashcard.id`
- `id` = EMS internal ID

---

### 6. Student Test Result IDs (Synced from Gurukul)

**Model**: `StudentTestResult`  
**Table**: `student_test_results`  
**ID Field**: `id`  
**Type**: Integer  
**Gurukul Reference**: `gurukul_id` (String, UUID)

**Fields**:
```python
id = Column(Integer, primary_key=True, index=True)
student_id = Column(Integer, ForeignKey("users.id"))
school_id = Column(Integer, ForeignKey("schools.id"))
gurukul_id = Column(String(255), unique=True, index=True)  # ← Links to Gurukul TestResult.id
subject = Column(String(255))
topic = Column(String(255))
difficulty = Column(String(50))
num_questions = Column(Integer)
questions = Column(JSON)
user_answers = Column(JSON)
score = Column(Integer)
total_questions = Column(Integer)
percentage = Column(Float)
time_taken = Column(Integer)
created_at = Column(DateTime)
synced_at = Column(DateTime)
```

**Relationship**: 
- `gurukul_id` = Gurukul `TestResult.id`
- `id` = EMS internal ID

---

### 7. Student Subject Data IDs (Synced from Gurukul)

**Model**: `StudentSubjectData`  
**Table**: `student_subject_data`  
**ID Field**: `id`  
**Type**: Integer  
**Gurukul Reference**: `gurukul_id` (String, UUID)

**Fields**:
```python
id = Column(Integer, primary_key=True, index=True)
student_id = Column(Integer, ForeignKey("users.id"))
school_id = Column(Integer, ForeignKey("schools.id"))
gurukul_id = Column(String(255), unique=True, index=True)  # ← Links to Gurukul SubjectData.id
subject = Column(String(255))
topic = Column(String(255))
notes = Column(Text)
provider = Column(String(50), default="groq")
youtube_recommendations = Column(JSON, default=[])
created_at = Column(DateTime)
synced_at = Column(DateTime)
```

**Relationship**: 
- `gurukul_id` = Gurukul `SubjectData.id`
- `id` = EMS internal ID

---

### 8. Other EMS Model IDs

#### School
- **Model**: `School`
- **ID Field**: `id` (Integer)
- **Table**: `schools`

#### Class
- **Model**: `Class`
- **ID Field**: `id` (Integer)
- **Table**: `classes`
- **Links to**: `schools.id`, `subjects.id`, `users.id` (teacher)

#### Subject
- **Model**: `Subject`
- **ID Field**: `id` (Integer)
- **Table**: `subjects`
- **Links to**: `schools.id`

#### Attendance
- **Model**: `Attendance`
- **ID Field**: `id` (Integer)
- **Table**: `attendance`

#### Announcement
- **Model**: `Announcement`
- **ID Field**: `id` (Integer)
- **Table**: `announcements`

---

## 🔗 ID Relationships & Syncing

### Gurukul → EMS Sync Flow

When content is synced from Gurukul to EMS:

1. **Gurukul creates record** with UUID `id`
2. **Sync service** sends `gurukul_id = record.id` to EMS
3. **EMS creates record** with Integer `id`
4. **EMS stores** `gurukul_id` to maintain link

**Example Sync Flow**:
```python
# Gurukul: Summary created
summary = Summary(id="abc-123-uuid", title="Math Notes", ...)

# Sync to EMS
ems_sync.sync_summary(
    gurukul_id=summary.id,  # "abc-123-uuid"
    student_email="student@example.com",
    ...
)

# EMS: StudentSummary created
student_summary = StudentSummary(
    id=1,  # EMS auto-increment ID
    gurukul_id="abc-123-uuid",  # Links back to Gurukul
    title="Math Notes",
    ...
)
```

### ID Mapping Table

| Gurukul Model | Gurukul ID Field | EMS Model | EMS ID Field | EMS gurukul_id Field |
|--------------|------------------|-----------|--------------|---------------------|
| `Summary` | `id` (UUID) | `StudentSummary` | `id` (Integer) | `gurukul_id` (String) |
| `Flashcard` | `id` (UUID) | `StudentFlashcard` | `id` (Integer) | `gurukul_id` (String) |
| `TestResult` | `id` (UUID) | `StudentTestResult` | `id` (Integer) | `gurukul_id` (String) |
| `SubjectData` | `id` (UUID) | `StudentSubjectData` | `id` (Integer) | `gurukul_id` (String) |

---

## 📝 ID Naming Conventions

### Gurukul System
- **Primary Keys**: Always named `id`
- **Type**: String (UUID v4)
- **Format**: `"550e8400-e29b-41d4-a716-446655440000"`
- **Foreign Keys**: Named as `{model}_id` (e.g., `user_id`, `tenant_id`)

### EMS System
- **Primary Keys**: Always named `id`
- **Type**: Integer (auto-increment)
- **Format**: `1`, `2`, `100`, etc.
- **Foreign Keys**: Named as `{model}_id` (e.g., `user_id`, `school_id`, `lesson_id`)
- **Gurukul References**: Named as `gurukul_id` (String, stores UUID)

### Special Cases

#### Lesson ID in EMS
- **Field Name**: `id` (in `lessons` table)
- **Referenced As**: `lesson_id` (in `lectures` table)
- **Type**: Integer
- **Purpose**: Links lectures to their parent lesson

#### Gurukul ID in EMS
- **Field Name**: `gurukul_id`
- **Type**: String (UUID)
- **Purpose**: Maintains link to original Gurukul record
- **Used In**: All student content tables (summaries, flashcards, tests, subject_data)

---

## 🗄️ Database Schema Reference

### Gurukul Database (SQLite/PostgreSQL)

```sql
-- Users
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,  -- UUID
    email VARCHAR UNIQUE,
    user_id VARCHAR REFERENCES users(id),  -- Foreign key
    ...
);

-- Summaries
CREATE TABLE summaries (
    id VARCHAR PRIMARY KEY,  -- UUID
    user_id VARCHAR REFERENCES users(id),
    title VARCHAR,
    content TEXT,
    ...
);

-- Flashcards
CREATE TABLE flashcards (
    id VARCHAR PRIMARY KEY,  -- UUID
    user_id VARCHAR REFERENCES users(id),
    question TEXT,
    answer TEXT,
    ...
);

-- Test Results
CREATE TABLE test_results (
    id VARCHAR PRIMARY KEY,  -- UUID
    user_id VARCHAR REFERENCES users(id),
    subject VARCHAR,
    score INTEGER,
    ems_sync_id VARCHAR,  -- Stores EMS record ID after sync
    ...
);

-- Subject Data
CREATE TABLE subject_data (
    id VARCHAR PRIMARY KEY,  -- UUID
    user_id VARCHAR REFERENCES users(id),
    subject VARCHAR,
    topic VARCHAR,
    notes TEXT,
    ems_sync_id VARCHAR,  -- Stores EMS record ID after sync
    ...
);
```

### EMS Database (PostgreSQL)

```sql
-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,  -- Integer
    email VARCHAR UNIQUE,
    school_id INTEGER REFERENCES schools(id),
    ...
);

-- Lessons
CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,  -- Integer
    title VARCHAR,
    class_id INTEGER REFERENCES classes(id),
    teacher_id INTEGER REFERENCES users(id),
    ...
);

-- Lectures
CREATE TABLE lectures (
    id SERIAL PRIMARY KEY,  -- Integer
    lesson_id INTEGER REFERENCES lessons(id),  -- Links to lesson
    title VARCHAR,
    ...
);

-- Student Summaries (from Gurukul)
CREATE TABLE student_summaries (
    id SERIAL PRIMARY KEY,  -- Integer
    student_id INTEGER REFERENCES users(id),
    gurukul_id VARCHAR UNIQUE,  -- Links to Gurukul Summary.id (UUID)
    title VARCHAR,
    ...
);

-- Student Flashcards (from Gurukul)
CREATE TABLE student_flashcards (
    id SERIAL PRIMARY KEY,  -- Integer
    student_id INTEGER REFERENCES users(id),
    gurukul_id VARCHAR UNIQUE,  -- Links to Gurukul Flashcard.id (UUID)
    question TEXT,
    ...
);

-- Student Test Results (from Gurukul)
CREATE TABLE student_test_results (
    id SERIAL PRIMARY KEY,  -- Integer
    student_id INTEGER REFERENCES users(id),
    gurukul_id VARCHAR UNIQUE,  -- Links to Gurukul TestResult.id (UUID)
    subject VARCHAR,
    ...
);

-- Student Subject Data (from Gurukul)
CREATE TABLE student_subject_data (
    id SERIAL PRIMARY KEY,  -- Integer
    student_id INTEGER REFERENCES users(id),
    gurukul_id VARCHAR UNIQUE,  -- Links to Gurukul SubjectData.id (UUID)
    subject VARCHAR,
    ...
);
```

---

## 🔍 Quick Reference

### Finding IDs in Code

**Gurukul Backend**:
```python
# Summary ID
summary.id  # UUID string

# Flashcard ID
flashcard.id  # UUID string

# Test Result ID
test_result.id  # UUID string

# Subject Data ID
subject_data.id  # UUID string
```

**EMS Backend**:
```python
# Lesson ID
lesson.id  # Integer

# Lecture ID
lecture.id  # Integer
lecture.lesson_id  # Foreign key to lesson

# Student Summary ID
student_summary.id  # Integer (EMS)
student_summary.gurukul_id  # UUID (Gurukul reference)
```

**Frontend (MyContent)**:
```javascript
// All items have 'id' field
item.id  // UUID for Gurukul content
item.type  // 'summary', 'flashcard', 'test', 'subject'
```

---

## 📊 Summary Table

| System | Model | ID Field Name | ID Type | Example Value |
|--------|-------|---------------|---------|---------------|
| **Gurukul** | Summary | `id` | UUID String | `"abc-123-uuid"` |
| **Gurukul** | Flashcard | `id` | UUID String | `"def-456-uuid"` |
| **Gurukul** | TestResult | `id` | UUID String | `"ghi-789-uuid"` |
| **Gurukul** | SubjectData | `id` | UUID String | `"jkl-012-uuid"` |
| **EMS** | Lesson | `id` | Integer | `1` |
| **EMS** | Lecture | `id` | Integer | `5` |
| **EMS** | Lecture | `lesson_id` | Integer (FK) | `1` |
| **EMS** | StudentSummary | `id` | Integer | `10` |
| **EMS** | StudentSummary | `gurukul_id` | UUID String | `"abc-123-uuid"` |
| **EMS** | StudentFlashcard | `id` | Integer | `15` |
| **EMS** | StudentFlashcard | `gurukul_id` | UUID String | `"def-456-uuid"` |
| **EMS** | StudentTestResult | `id` | Integer | `20` |
| **EMS** | StudentTestResult | `gurukul_id` | UUID String | `"ghi-789-uuid"` |
| **EMS** | StudentSubjectData | `id` | Integer | `25` |
| **EMS** | StudentSubjectData | `gurukul_id` | UUID String | `"jkl-012-uuid"` |

---

## ✅ Key Takeaways

1. **All models have `id` as primary key** - This is standard across both systems
2. **Gurukul uses UUID strings** - Better for distributed systems
3. **EMS uses Integer IDs** - Traditional auto-increment
4. **`gurukul_id` links EMS records to Gurukul** - Maintains relationship during sync
5. **`lesson_id` in EMS** - Only for Lecture → Lesson relationship (not related to Gurukul content)
6. **MyContent displays all Gurukul IDs** - Shows `id` for summaries, flashcards, tests, and subject data

---

**Last Updated**: 2025-01-06  
**Version**: 1.0

