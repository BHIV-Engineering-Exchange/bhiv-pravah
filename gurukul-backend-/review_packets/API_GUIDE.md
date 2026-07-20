# API GUIDE
## Complete API Reference — Gurukul Backend

**Base URL (local):** `http://localhost:3000`  
**Base URL (prod):** `https://gurukul-frontend-738j.onrender.com` (frontend) / backend URL from Render  
**Docs:** `GET /docs` (Swagger UI)  
**Auth:** All protected endpoints require `Authorization: Bearer <token>`

---

## AUTH ENDPOINTS — `/api/v1/auth`

### POST `/api/v1/auth/register`
**Purpose:** Register a new student account.

**Input:**
```json
{
  "email": "student@example.com",
  "password": "secure123",
  "full_name": "Rohan Sharma",
  "role": "STUDENT"
}
```

**Output (201):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "student@example.com",
    "full_name": "Rohan Sharma",
    "role": "STUDENT",
    "assessment_completed": false
  }
}
```

**Failure cases:**
- 400: Email already registered
- 400: Password too short (<6) or too long (>100)
- 403: Role is not STUDENT (only students can register)

**Dependencies:** SQL DB

---

### POST `/api/v1/auth/login`
**Purpose:** Login and get JWT token.

**Input:**
```json
{
  "email": "student@example.com",
  "password": "secure123"
}
```

**Output (200):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "student@example.com",
    "full_name": "Rohan Sharma",
    "role": "STUDENT",
    "assessment_completed": false
  }
}
```

**Failure cases:**
- 401: Wrong email or password
- 400: Inactive user
- 403: Non-STUDENT role (must use EMS portal)

**Side effects:** Triggers background Vaani XTTS model download  
**Dependencies:** SQL DB, bcrypt

---

### GET `/api/v1/auth/me`
**Purpose:** Get current user info (requires auth).

**Output (200):**
```json
{
  "id": "uuid",
  "email": "student@example.com",
  "full_name": "Rohan Sharma",
  "role": "STUDENT",
  "is_active": true,
  "assessment_completed": false,
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### PUT `/api/v1/auth/update-profile`
**Purpose:** Update user's full name.

**Input:** `{"full_name": "New Name"}`  
**Output:** Updated UserResponse

---

### POST `/api/v1/auth/complete-assessment`
**Purpose:** Mark the onboarding assessment as done.  
**Output:** Updated UserResponse with `assessment_completed: true`

---

### DELETE `/api/v1/auth/delete-account`
**Purpose:** Delete account + all data (profile, summaries, flashcards, reflections, progress).  
**Output:** `{"message": "...", "success": true}`

---

## CHAT ENDPOINTS — `/api/v1/chat`

### POST `/api/v1/chat`
**Purpose:** Chat with the AI tutor. Uses RAG (knowledge base) + Groq.

**Input:**
```json
{
  "message": "Explain recursion in Python",
  "conversation_id": "uuid-optional",
  "provider": "auto",
  "use_rag": true
}
```

**Output (200):**
```json
{
  "response": "Recursion is...",
  "conversation_id": "uuid",
  "knowledge_base_used": true,
  "groq_used": true,
  "context_length": 1200,
  "fallback_used": false,
  "kb_error": null,
  "groq_error": null,
  "history_messages_used": 4
}
```

**Failure cases:**
- 401: No/invalid token
- 500: Groq API failure (returns error message as response text)

**Dependencies:** Groq API (GROQ_API_KEY), Vector Store (optional RAG), SQL DB

---

### GET `/api/v1/chat/history/{conversation_id}`
**Purpose:** Retrieve message history for a conversation.

**Output:**
```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "found": true
}
```
Note: History is in-memory. Resets on server restart.

---

### DELETE `/api/v1/chat/history/{conversation_id}`
**Purpose:** Clear a conversation's history.

---

### POST `/api/v1/chat/knowledge`
**Purpose:** Add text to the RAG knowledge base.

**Input:** `{"text": "Python is a programming language...", "metadata": {}}`  
**Output:** `{"status": "learned", "chunks_added": 3, "total_chunks": 42, "backend": "chromadb"}`

---

## TTS ENDPOINTS — `/api/v1/tts`

### POST `/api/v1/tts/speak`
**Purpose:** Convert text to speech (WAV audio). Uses Vaani engine.

**Input:**
```json
{"text": "Hello, welcome to Gurukul!", "language": "en"}
```

**Output:** Binary audio (WAV), `Content-Type: audio/wav`

**Failure:** 500 if all TTS engines fail

---

### POST `/api/v1/tts/vaani`
**Purpose:** Same as /speak but explicitly routes to Vaani engine.

---

### GET `/api/v1/tts/voices`
**Purpose:** List available TTS voices.

**Output:**
```json
{
  "voices": [{"name": "Vaani Teacher", "id": "vaani_teacher", "languages": ["en","hi","ar","es","fr","ja"], "gender": "Female"}],
  "total": 1
}
```

---

## AGENT ENDPOINTS — `/api/v1/agent`

### POST `/api/v1/agent/tts`
**Purpose:** 3-tier TTS with MongoDB cache. Best endpoint for production TTS.

**Input:**
```json
{"text": "Welcome to class", "language": "en"}
```

**Output:** Binary audio (MP3), headers: `X-TTS-Engine: vaani|openai|gtts|cache`

**Fallback chain:**
1. Vaani (local engine, port 8008)
2. OpenAI TTS (if OPENAI_API_KEY set)
3. gTTS (free, always works)
4. Cache (MongoDB, by text hash)

---

### GET `/api/v1/agent/download-audio?audio_id={hash}`
**Purpose:** Download cached audio by SHA256 hash.

---

## VOICE/STT ENDPOINTS — `/api/v1/voice`

### POST `/api/v1/voice/listen`
**Purpose:** Transcribe audio file to text.

**Input:** `multipart/form-data`
- `audio`: audio file (WAV, MP3, OGG, WebM, M4A)
- `language`: language code or "auto"

**Output:**
```json
{
  "text": "Hello, how are you?",
  "language": "en",
  "confidence": 0.95,
  "engine": "groq-whisper",
  "duration_ms": 320
}
```

---

### POST `/api/v1/voice/converse`
**Purpose:** Full voice conversation: STT → LLM → TTS. Returns audio response.

---

### GET `/api/v1/voice/stt/status`
**Purpose:** Check STT provider health.

---

### GET `/api/v1/voice/languages`
**Purpose:** List supported STT languages.

---

## LEARNING ENDPOINTS — `/api/v1/learning`

### POST `/api/v1/learning/generate`
**Purpose:** Generate AI lesson notes for a subject/topic.

**Input:**
```json
{"subject": "Mathematics", "topic": "Quadratic Equations", "grade": "10"}
```

**Output:**
```json
{
  "notes": "## Introduction\n...",
  "subject": "Mathematics",
  "topic": "Quadratic Equations",
  "provider": "groq",
  "youtube_recommendations": [...]
}
```

---

## FLASHCARD ENDPOINTS — `/api/v1/flashcards`

### POST `/api/v1/flashcards/generate`
**Purpose:** AI-generate flashcards from a topic.

**Input:** `{"subject": "Chemistry", "topic": "Periodic Table", "count": 5}`

---

### GET `/api/v1/flashcards`
**Purpose:** Get user's flashcards.

---

### POST `/api/v1/flashcards/{id}/review`
**Purpose:** Submit flashcard review (updates spaced repetition schedule).

**Input:** `{"confidence": 4}` (1-5 scale)

---

## QUIZ ENDPOINTS — `/api/v1/quiz`

### POST `/api/v1/quiz/generate`
**Purpose:** Generate a quiz from a topic.

**Input:**
```json
{"subject": "History", "topic": "World War II", "difficulty": "medium", "num_questions": 5}
```

---

### POST `/api/v1/quiz/submit`
**Purpose:** Submit quiz answers, get scored result.

**Input:** `{"quiz_id": "uuid", "answers": {"q1": "A", "q2": "C"}}`

---

## SOUL ENDPOINTS — `/api/v1/soul`

### POST `/api/v1/soul/reflect`
**Purpose:** Save a student reflection/journal entry.

**Input:** `{"content": "Today I learned...", "mood_score": 8}`

---

### GET `/api/v1/soul/reflections`
**Purpose:** Get all reflections for current user.

---

## EMS ENDPOINTS — `/api/v1/ems`

### GET `/api/v1/ems/students`
**Purpose:** Get student list from EMS (admin only).

### POST `/api/v1/ems/sync`
**Purpose:** Push test results and progress to EMS.

---

## KARMA TRACKER ENDPOINTS — `/api/v1/karma`

Full karma system with sub-routers:

| Route | Purpose |
|-------|---------|
| `GET /api/v1/karma/balance/{user_id}` | Get karma balance |
| `POST /api/v1/karma/log-action` | Log a karma-earning action |
| `POST /api/v1/karma/redeem` | Redeem karma points |
| `GET /api/v1/karma/stats/{user_id}` | Karma statistics |
| `GET /api/v1/analytics/...` | Karma analytics |
| `POST /api/v1/karma/appeal` | Appeal a karma decision |
| `POST /api/v1/karma/atonement` | Submit atonement for karma loss |
| `POST /api/v1/karma/lifecycle/...` | Karma lifecycle management |
| `POST /api/v1/karma/death` | Karma death events |
| `POST /api/v1/karma/event` | General karma events |

**Note:** Karma system uses MongoDB (karma_database), not SQL.

---

## SYSTEM ENDPOINTS

### GET `/`
**Purpose:** Root health check.  
**Output:** `{"message": "Gurukul Backend API v2 is running", "docs": "/docs"}`

### GET `/system/metrics`
**Purpose:** Request counts, latency stats, AI/voice latency.

### GET `/api/v1/tenant-info`
**Purpose:** Debug multi-tenant resolution.

---

## END-TO-END FLOW DIAGRAMS

### Login Flow
```
POST /api/v1/auth/login
  → Lookup user by email in SQL
  → Verify bcrypt hash
  → Check role == STUDENT
  → Create JWT (sub=email, 7 day expiry)
  → Background: trigger Vaani XTTS download
  → Return {access_token, user}
```

### Chat Flow
```
POST /api/v1/chat
  → JWT auth → get User from SQL
  → Get RAG context (vector store, top 3 chunks)
  → Build system prompt (with or without context)
  → Add conversation history (last 10 messages)
  → POST to Groq API (llama-3.3-70b-versatile)
  → Save messages to _chat_history (in-memory)
  → Emit signal to Pravah
  → Emit memory to Bucket
  → Return {response, conversation_id, ...}
```

### Voice Flow (TTS)
```
POST /api/v1/agent/tts
  → Hash text+language (SHA256)
  → Check MongoDB tts_cache
    → HIT: return cached audio
  → TRY Vaani (POST localhost:8008/voice/speak)
    → FAIL: TRY OpenAI TTS
      → FAIL: TRY gTTS (free)
  → Store in MongoDB tts_cache
  → Return audio bytes + X-TTS-Engine header
```

### Voice Flow (STT)
```
POST /api/v1/voice/listen
  → Validate MIME type
  → Read audio bytes
  → speech_provider.transcribe()
    → TRY Groq Whisper API
    → FAIL: TRY faster-whisper (local)
  → Return {text, language, confidence, engine}
```

### Agent Flow (Edu Mentor)
```
POST /api/v1/agent/edu-mentor
  → Auth user
  → call_groq_api(subject, topic) or call_ollama_api() as fallback
  → Return educational notes
```
