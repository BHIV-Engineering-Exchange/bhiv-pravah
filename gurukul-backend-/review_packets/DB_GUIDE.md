# DATABASE GUIDE
## Gurukul Data Layer — SQL + MongoDB

---

## 1. OVERVIEW

Gurukul uses **two databases**:

| Database | What It Stores | Where Config Lives |
|----------|---------------|-------------------|
| PostgreSQL (prod) / SQLite (dev) | Users, lessons, flashcards, quizzes, reflections, progress | `DATABASE_URL` in `.env` |
| MongoDB | Karma tracker, TTS cache, Q-tables for RL | `MONGO_URI` in `.env` / `karma_config.py` |

---

## 2. SQL DATABASE

### How it connects
File: `backend/app/core/database.py`

- Reads `DATABASE_URL` from environment
- If not set → falls back to `sqlite:///./gurukul.db` (file in `backend/` directory)
- Uses SQLAlchemy with connection pooling (pool_size=10, max_overflow=20)
- Tables are auto-created on startup via `Base.metadata.create_all(engine)`

### Tables

#### `tenants`
```
id (PK, UUID)
name          — e.g. "Gurukul Main"
type          — INSTITUTION | FAMILY
created_at
```
Every user must belong to a tenant. Default tenant "Gurukul Main" is auto-created on first registration.

---

#### `users`
```
id (PK, UUID)
email (unique, indexed)
hashed_password     — bcrypt hash (nullable for OAuth users)
full_name
role               — ADMIN | TEACHER | PARENT | STUDENT
tenant_id (FK → tenants)
cohort_id (FK → cohorts, nullable)
parent_id (FK → users, self-reference, nullable)
is_active (bool, default True)
assessment_completed (bool, default False)
created_at
ems_token          — stored EMS JWT (nullable)
ems_token_expires_at
```
**CRITICAL:** Only STUDENT role can log in to Gurukul. Other roles must use EMS portal.

---

#### `cohorts`
```
id (PK, UUID)
name              — e.g. "Grade 10-A"
tenant_id (FK → tenants)
created_at
```
Groups of students within a tenant.

---

#### `teacher_student_assignments`
```
id (PK, UUID)
teacher_id (FK → users)
student_id (FK → users)
cohort_id (FK → cohorts, nullable)
subject (nullable)
created_at
UNIQUE(teacher_id, student_id, cohort_id, subject)
```

---

#### `profiles`
```
id (PK, UUID)
user_id (FK → users, unique)
data (JSON)        — flexible bag: grade, subjects, learning_style, etc.
```

---

#### `lessons`
```
id (PK, UUID)
user_id (FK → users)
title
subject
topic
description
content (Text)     — full lesson notes
status             — active | archived | draft
created_at
updated_at
```

---

#### `summaries`
```
id (PK, UUID)
user_id (FK → users, nullable)
title
content (Text)
source
source_type        — e.g. "pdf", "text", "url"
created_at
metadata (JSON)
```

---

#### `flashcards`
```
id (PK, UUID)
user_id (FK → users, nullable)
question (Text)
answer (Text)
question_type      — conceptual | factual | application
days_until_review  — spaced repetition counter
confidence (Float, 0.0-1.0)
created_at
```

---

#### `test_results`
```
id (PK, UUID)
user_id (FK → users)
subject
topic
difficulty         — easy | medium | hard
num_questions
questions (JSON)   — full question objects with options + correct answers
user_answers (JSON)
score
total_questions
percentage (Float)
time_taken (nullable, seconds)
created_at
synced_to_ems (bool)
ems_sync_id (nullable)
```

---

#### `subject_data`
```
id (PK, UUID)
user_id (FK → users)
subject
topic
notes (Text)       — generated lesson notes
provider           — groq | ollama
youtube_recommendations (JSON)
created_at
synced_to_ems (bool)
ems_sync_id (nullable)
```

---

#### `reflections`
```
id (PK, UUID)
user_id (FK → users)
content (Text)
mood_score (Int, nullable, 1-10)
created_at
```

---

#### `learning_tracks`
```
id (PK, UUID)
title
description (Text)
tenant_id (FK → tenants, nullable)
created_at
```

---

#### `milestones`
```
id (PK, UUID)
track_id (FK → learning_tracks)
title
description (Text)
order_index (Int)
```

---

#### `student_progress`
```
id (PK, UUID)
user_id (FK → users)
milestone_id (FK → milestones)
status             — NOT_STARTED | IN_PROGRESS | COMPLETED
evidence (Text)    — link to artifact
reflection_notes (Text)
completed_at
updated_at
```

---

#### PRANA Integrity Tables (append-only)
Defined in `app/models/prana_models.py`:
- `prana_packets` — immutable log of all PRANA events
- `review_output_versions` — versioned review outputs
- `next_task_versions` — versioned next task states

These tables **must never be manually edited**. They enforce append-only invariants.

---

### Relationships Map

```
Tenant (1) ──── (N) User
Tenant (1) ──── (N) Cohort
Cohort (1) ──── (N) User
User (parent) (1) ──── (N) User (child)
User (1) ──── (1) Profile
User (1) ──── (N) Lesson
User (1) ──── (N) Summary
User (1) ──── (N) Flashcard
User (1) ──── (N) Reflection
User (1) ──── (N) TestResult
User (1) ──── (N) SubjectData
User (1) ──── (N) StudentProgress
TeacherStudentAssignment (M:N) Teacher ↔ Student
```

---

## 3. MONGODB DATABASE

### How it connects
File: `backend/app/core/karma_database.py`  
Config: `backend/app/core/karma_config.py`

- Reads `MONGO_URI` from environment (e.g. `mongodb://localhost:27017/gurukul_karma`)
- Lazy connection — only connects when first accessed
- Connection verified with `ping` on startup

### Collections

#### `users` (MongoDB)
Karma user records — separate from SQL users.
```json
{
  "user_id": "uuid",
  "karma_balance": 250,
  "lifetime_earned": 1000,
  "created_at": "...",
  "last_active": "..."
}
```

#### `transactions`
Karma transaction log.
```json
{
  "user_id": "uuid",
  "action_type": "quiz_completed",
  "points": 50,
  "balance_after": 300,
  "timestamp": "...",
  "metadata": {}
}
```

#### `q_table`
Q-values for RL-based TTS adaptation.

#### `appeals`
Karma appeal records.

#### `atonements`
Karma atonement submissions.

#### `death_events`
Karma "death" (reset) events.

#### `karma_events`
General karma event log.

#### `rnanubandhan_relationships`
Student-to-student karma relationship graph.

#### `tts_cache`
TTS audio cache (keyed by SHA256 of text+language).
```json
{
  "text_hash": "abc123...",
  "text": "Hello world",
  "language": "en",
  "audio_data": "<binary>",
  "engine": "vaani",
  "created_at": "..."
}
```

---

## 4. SESSION HANDLING

### SQL Sessions
- `SessionLocal` is a SQLAlchemy session factory
- Each request gets its own session via `Depends(get_db)`
- Session is closed in `finally` block (no leaks)
- Transactions roll back automatically on exception

### MongoDB Sessions
- MongoDB client is a singleton (`_client`)
- Thread-safe lazy initialization
- Auto-reconnects if connection is lost (ping check on each use)
- No explicit session management needed for simple queries

### In-Memory State (CRITICAL)
The following data lives **only in RAM** and is **lost on restart**:
- `_chat_history` in `chat.py` — all conversation histories
- PRANA runtime state
- Service watchdog counters

**For production:** chat history should be moved to PostgreSQL. There is already a `summaries` table that can store sessions.

---

## 5. WHAT BREAKS IF DB FAILS

### SQL DB Fails
| Impact | Severity |
|--------|----------|
| Login/Register completely broken | CRITICAL |
| All protected endpoints return 500 | CRITICAL |
| Flashcards, quizzes, lessons unavailable | HIGH |
| EMS sync fails | MEDIUM |
| Only `/` health check still works | — |

### MongoDB Fails
| Impact | Severity |
|--------|----------|
| Karma tracker completely broken | HIGH |
| TTS cache miss on every request (still works, just slower) | LOW |
| Karma analytics unavailable | MEDIUM |
| Chat, auth, flashcards still work | — |

### Recovery Steps (SQL)
1. Check `DATABASE_URL` is correct in `.env`
2. `cd backend && python3 -c "from app.core.database import engine; engine.connect()"`
3. If PostgreSQL: check if DB server is running, firewall rules, credentials
4. If SQLite: check if `gurukul.db` file exists and is readable
5. Restart backend — it has 5-retry logic with exponential backoff

### Recovery Steps (MongoDB)
1. Check `MONGO_URI` is correct in `.env` / `karma_config.py`
2. Verify MongoDB server is running: `mongosh --eval "db.runCommand({ping: 1})"`
3. Check credentials and network access
4. Backend will start without MongoDB (karma features disabled)

---

## 6. DATABASE MIGRATION

There are **no migration files** (no Alembic). Tables are created fresh from SQLAlchemy models on every startup via `Base.metadata.create_all()`. This means:
- Adding a new column: add it to the model, restart backend → column appears (SQLite only adds, never removes)
- Removing a column: requires manual SQL or db wipe
- For PostgreSQL production: **do not rely on create_all** for schema changes — write ALTER TABLE statements manually
