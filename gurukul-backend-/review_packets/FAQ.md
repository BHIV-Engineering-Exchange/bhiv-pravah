# FAQ
## 40 Questions Every New Developer Needs Answered

---

### SECTION 1: ARCHITECTURE

**Q1. What is Gurukul at a high level?**
Gurukul is a FastAPI backend that powers an AI tutoring app for students. It handles login, chat with an LLM (Groq), text-to-speech, speech-to-text, flashcards, quizzes, and a karma/reward system. There's also a separate EMS (school admin) system that runs alongside it.

---

**Q2. How many separate services are there?**
Five main services:
1. **Gurukul Backend** (port 3000) — the main API this document covers
2. **EMS Backend** (port 8000) — school admin system, separate FastAPI app
3. **Gurukul Frontend** (port 5173 dev) — React/Vite student UI
4. **EMS Frontend** (port 3001 dev) — React/Vite admin UI
5. **Vaani Engine** (port 8008) — sovereign TTS microservice

Plus: PostgreSQL, MongoDB, and optionally Redis.

---

**Q3. What is the entry point to the backend?**
`backend/app/main.py`. It creates the FastAPI app, adds middleware (CORS, rate limiting, trace ID), and loads all routers during the startup event. Run it with:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

---

**Q4. Why are routers loaded in the startup event instead of at the top of main.py?**
To make the server bind to its port as fast as possible (critical on Render which has a startup timeout). The auth router loads first (synchronously, 30s timeout), then all other routers load in the background without blocking.

---

**Q5. What databases does Gurukul use and why two?**
- **PostgreSQL/SQLite**: Stores users, lessons, flashcards, quizzes, reflections — structured relational data
- **MongoDB**: Stores karma tracker data, TTS cache — chosen for flexible document structure and the Q-table for RL

They're separate concerns. The app works without MongoDB (karma features just fail). It does NOT work without SQL.

---

### SECTION 2: AUTH

**Q6. How does login work?**
1. POST `/api/v1/auth/login` with email + password
2. Backend finds user in SQL DB by email
3. bcrypt.checkpw() verifies the password against the stored hash
4. If valid and role == STUDENT, creates a JWT token (HS256, 7-day expiry)
5. Returns token + user info

---

**Q7. Where is the user stored?**
In the `users` table of the SQL database. The User model is in `backend/app/models/all_models.py`. Key fields: `email` (unique), `hashed_password`, `role`, `tenant_id`, `is_active`.

---

**Q8. How does JWT auth work on protected endpoints?**
Each protected route has `Depends(get_current_user)` (from `app/routers/auth.py`). This:
1. Extracts the Bearer token from `Authorization` header
2. Decodes it using `JWT_SECRET_KEY` with python-jose
3. Gets `sub` (email) from the payload
4. Queries SQL for the user
5. Returns the User object

If the token is missing, expired, or invalid → 401.

---

**Q9. Can teachers or admins log in to Gurukul?**
No. Only STUDENT role can use Gurukul. Teachers and admins must use the EMS portal at port 8000. This is enforced in both `/register` and `/login`.

---

**Q10. How do I add admin functionality to the backend?**
The `require_role` helper exists in `auth.py`. Example:
```python
@router.get("/admin-only")
async def admin_route(user: User = Depends(require_role("ADMIN"))):
    ...
```
ADMIN role can bypass any role check. But currently only STUDENT accounts can be created via the API — you'd need to manually insert ADMIN users in the DB.

---

### SECTION 3: CHAT & LLM

**Q11. How does a chat message reach the LLM?**
1. POST `/api/v1/chat` with `{message, conversation_id, use_rag}`
2. JWT auth → get current user
3. Vector store lookup (if `use_rag=true`)
4. Build message array: system prompt + history + current message
5. Call Groq API: `client.chat.completions.create(model="llama-3.3-70b-versatile", ...)`
6. Return response

---

**Q12. What happens if Groq fails?**
The chat router falls back to returning an error message string (not a 500):
```json
{"response": "I'm sorry, I'm having trouble connecting to my brain right now. (Error: ...)"}
```
The LLM service (`services/llm.py`) tries Groq first, then Ollama. But the chat router itself doesn't use `services/llm.py` — it calls Groq directly using the Groq SDK. If Groq fails there, the error is returned as a response string.

---

**Q13. Where is conversation history stored?**
In a Python dict called `_chat_history` at the top of `app/routers/chat.py`. It's keyed by `{user_id}:{conversation_id}`. **It's in-memory and lost on restart.** For production, this needs to move to PostgreSQL.

---

**Q14. What is RAG and how does it work here?**
RAG (Retrieval-Augmented Generation) adds relevant context from the knowledge base to the system prompt before calling the LLM. The flow: query → `get_knowledge_base_context()` → vector store search → top 3 chunks → injected into system prompt. If the vector store is unavailable (common in production due to memory limits), it falls back to plain Groq without context.

---

**Q15. How do I add a new chat endpoint?**
1. Open `backend/app/routers/chat.py`
2. Add a new `@router.post("/your-endpoint")` function
3. Use `Depends(get_current_user)` for auth
4. No registration needed — the router is already mounted at `/api/v1/chat`

---

### SECTION 4: TTS & VOICE

**Q16. How does TTS get triggered?**
Three ways:
1. **Agent endpoint**: `POST /api/v1/agent/tts` — best, has 3-tier fallback + MongoDB cache
2. **TTS router**: `POST /api/v1/tts/speak` — uses Vaani engine
3. **Frontend**: calls agent TTS endpoint, plays returned audio blob

The agent endpoint tries: Vaani → OpenAI → gTTS. It caches results in MongoDB by SHA256(text+language).

---

**Q17. What is Vaani?**
Vaani is Gurukul's "sovereign" (own) TTS engine running as a separate microservice at port 8008 (`vaani-engine/` directory). It provides voice output without external APIs. If Vaani is not running, TTS falls back to OpenAI (if key set) or gTTS (free Google TTS, always available).

---

**Q18. What is the TTS fallback chain?**
1. Vaani local engine (POST localhost:8008/voice/speak)
2. OpenAI TTS API (if OPENAI_API_KEY is set)
3. gTTS (free, needs internet to Google, no API key)

If all three fail → 503 "All TTS engines failed".

---

**Q19. How does STT work?**
POST `/api/v1/voice/listen` with audio file:
1. Validate MIME type (WAV, MP3, OGG, WebM, M4A accepted)
2. Call `speech_provider.transcribe()` in `services/speech_provider.py`
3. Tries Groq Whisper API first (cloud, fast)
4. Falls back to faster-whisper (local, slower but offline)
5. Returns text + detected language + confidence

---

**Q20. What audio formats are supported for STT?**
WAV, MP3, OGG, WebM, M4A, FLAC. The content-type must be an `audio/` MIME type. `application/octet-stream` is also accepted as a generic fallback.

---

### SECTION 5: TANTRA / PRANA / PRAVAH / BUCKET

**Q21. What is TANTRA?**
TANTRA is an external telemetry and memory system that Gurukul integrates with. It has two components:
- **Pravah**: Real-time event signals (like "user sent a chat message", "TTS generated")
- **Bucket**: Append-only memory events with SHA256 hash chain (permanent record)

Both are optional. If `PRAVAH_URL` and `BUCKET_URL` are not set, all events are silently dropped.

---

**Q22. What is PRANA?**
PRANA is Gurukul's internal append-only integrity system. It prevents historical data from being overwritten. `PranaPacket` rows in the SQL DB can never be deleted or modified — only new records can be appended. Violating this throws `AppendOnlyViolationError` (HTTP 409).

---

**Q23. What is trace_id and how does it work?**
Every HTTP request gets a `trace_id` (either from the `x-trace-id` request header or generated as `gurukul-{uuid4}`). It's stored in a Python context variable (`app/core/context.py`) for the duration of the request. The trace_id is:
- Sent back in the `x-trace-id` response header
- Included in all Pravah signals
- Used for debugging and cross-system correlation

---

**Q24. What is the bucket hash chain?**
Every memory event emitted to TANTRA Bucket has:
- `prev_hash`: SHA256 of the previous event
- `current_hash`: SHA256(prev_hash + JSON(current_event))

This creates an immutable chain. If any event is tampered with, the chain is broken. The chain starts from a genesis hash (64 zeros).

---

### SECTION 6: KARMA TRACKER

**Q25. What is the Karma Tracker?**
A MongoDB-backed reward system for students. Students earn karma points by completing quizzes, attending lessons, helping others, etc. They can redeem points for rewards. It includes an appeal system, RL-based normalization, and a "death" (karma reset) mechanism.

---

**Q26. Where is karma data stored?**
In MongoDB, not PostgreSQL. Database name is configured via `karma_config.py` (uses `MONGO_URI` env var). Collections: `users`, `transactions`, `q_table`, `appeals`, `atonements`, `death_events`, `karma_events`, `rnanubandhan_relationships`.

---

**Q27. What is rnanubandhan?**
A karma relationship graph between students — essentially tracking karma "debts" and "credits" between users. The name comes from Sanskrit (karmic relationship/bond).

---

### SECTION 7: EMS INTEGRATION

**Q28. What is EMS and how does it connect to Gurukul?**
EMS (Educational Management System) is a separate FastAPI backend (port 8000) for school admins. Gurukul connects to it to:
1. Auto-create student accounts in EMS when a student registers in Gurukul (if `EMS_AUTO_CREATE_STUDENTS=true`)
2. Sync test results and lesson progress to EMS
3. Pull student/grade info for display

Configured via `EMS_API_BASE_URL`, `EMS_ADMIN_EMAIL`, `EMS_ADMIN_PASSWORD`.

---

**Q29. What happens if EMS is down when a student registers?**
Registration still succeeds. EMS account creation is a background task (`asyncio.create_task`) with a 10-second timeout. If it fails, it logs a warning but doesn't block the registration response. `EMS_AUTO_CREATE_STUDENTS=false` by default.

---

### SECTION 8: OPERATIONS

**Q30. How do I add a new API endpoint?**
1. Find or create the right router file in `backend/app/routers/`
2. Add your `@router.get/post/put/delete("/path")` function
3. Use `Depends(get_current_user)` if auth is needed
4. Use `Depends(get_db)` if SQL is needed
5. Router is already registered at startup — no additional registration needed
6. Restart the backend

---

**Q31. How do I add a new database table?**
1. Open `backend/app/models/all_models.py` (or create a new model file)
2. Add a new class that inherits from `Base`
3. Import the model in `backend/app/models/__init__.py` or `all_models.py`
4. Restart the backend — `Base.metadata.create_all(engine)` runs on startup and creates new tables
5. For PostgreSQL production: also write an ALTER TABLE if modifying existing tables

---

**Q32. How do I debug latency issues?**
1. Check `/system/metrics` — look at `avg_latency_ms`
2. Add `import time; start = time.time()` at the start of a slow endpoint
3. Check Groq latency separately:
   ```bash
   curl -X POST https://api.groq.com/openai/v1/chat/completions -H "Authorization: Bearer $GROQ_API_KEY" -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"hi"}]}' -w "\nTime: %{time_total}s\n"
   ```
4. Check if vector store is causing slow RAG: try `use_rag: false` in chat
5. Check MongoDB connection latency: slow Mongo = slow karma endpoints

---

**Q33. How do I run tests?**
```bash
cd backend
pytest tests/
# Or specific test file
pytest tests/test_auth.py -v
# Or run the BHIV test runner
python bhiv_test_runner.py
```

---

**Q34. What are the system bottlenecks?**
1. **Groq API latency** — chat responses depend entirely on Groq speed (usually 1-3s)
2. **Vector store loading** — ChromaDB can be slow to start if the collection is large
3. **Vaani cold start** — first TTS request after Vaani starts is slow (model loading)
4. **MongoDB cold connection** — first karma request after restart has connection overhead
5. **Chat history is in-memory** — can grow unboundedly; no cleanup mechanism exists

---

**Q35. What must NEVER be changed?**
1. **JWT_SECRET_KEY in production** — changing it invalidates ALL existing sessions
2. **PRANA table rows** — never DELETE or UPDATE `prana_packets`, `review_output_versions`, `next_task_versions`
3. **bcrypt hash format** — don't change how passwords are stored (would break all logins)
4. **`sub` claim in JWT** — auth depends on `sub` = user email; changing this breaks auth
5. **API prefix `/api/v1/auth`** — the frontend is hardcoded to this path

---

**Q36. How is multi-tenant mode different from normal mode?**
Normal mode (`MULTI_TENANT_ENABLED=false`): all users share one DB. Multi-tenant mode: each school (tenant) gets its own isolated database. Tenant is resolved from subdomain or `X-Tenant-ID` header. Currently disabled — only enable if you need per-school data isolation.

---

**Q37. How does the ServiceWatchdog work?**
`services/service_watchdog.py` runs as a background asyncio task. It periodically checks that SQL and MongoDB connections are alive (SQL: `SELECT 1`, MongoDB: `ping`). Results are stored in `system_health` dict visible at `/system/metrics`. If a connection is lost, it logs a warning — it does not restart services.

---

**Q38. What is PravahAdapter.start() doing?**
It starts a background asyncio loop that every 60 seconds:
1. Gathers system metrics (request counts, latency, etc.)
2. POSTs them to `PRAVAH_URL` (if configured)

This is fire-and-forget telemetry. If PRAVAH_URL is not set, nothing happens.

---

**Q39. How do I deploy a change to production?**
1. Push to GitHub
2. Render auto-deploys on push (if configured), or trigger manual deploy
3. Backend restarts — tables auto-created if new columns/tables exist
4. Monitor startup logs in Render dashboard for `[OK]` / `[FAIL]` messages
5. Test with `curl https://your-backend.onrender.com/` and `/docs`

---

**Q40. Where do I look first when something is completely broken?**
1. **Backend logs** — look for `[FAIL]` lines at startup
2. **`GET /`** — if this returns 200, backend is alive
3. **`GET /docs`** — if this loads, all routers registered successfully
4. **`POST /api/v1/auth/login`** — if this works, SQL + auth are fine
5. **`POST /api/v1/chat`** — if this works, Groq is reachable
6. **`GET /system/metrics`** — shows DB connection states and latency stats
