# DEBUG GUIDE
## "Something Broke" Playbook for Gurukul Backend

---

## HOW TO READ THIS GUIDE

For each issue:
1. Check the **Symptoms** — does it match what you see?
2. Read the **Root Cause** — what is actually wrong
3. Follow the **Fix Steps** exactly in order

---

## ISSUE 1: BACKEND NOT STARTING

### Symptoms
- `uvicorn` exits immediately or hangs
- No output on port 3000
- Logs show `[FAIL]` lines

### Root Causes & Fixes

**A) Import error on startup**
```
[Main] [FAIL] Error importing FastAPI/core modules: ...
```
Fix:
```bash
cd backend
pip install -r requirements.txt  # reinstall all deps
python -c "from app.main import app"  # test import manually
```

**B) Port already in use**
```
ERROR: [Errno 98] Address already in use
```
Fix:
```bash
lsof -i :3000  # find what's using port 3000
kill -9 <PID>
```

**C) Missing .env / bad config**
```
pydantic_settings.env_settings.EnvSettingsError
```
Fix: Make sure `backend/.env` exists with at least:
```dotenv
GROQ_API_KEY=your_key
JWT_SECRET_KEY=your_secret
DATABASE_URL=your_db_url  # or leave blank for SQLite
```

**D) Startup watchdog timeout (20s)**
```
[Startup] [FAIL] FATAL: Gurukul startup timed out after 20 seconds
```
This happens when router imports are too slow (heavy ML models).
Fix:
- Check that torch/transformers/chromadb are NOT in requirements.txt (they are disabled)
- Check if MongoDB is slow to connect: set `MONGO_SERVER_SELECTION_TIMEOUT_MS=2000`
- Backend still starts, just some routes may not be registered yet. Wait 30s and retry.

**E) Auth router failed to load (CRITICAL)**
```
[Startup] [FAIL] CRITICAL: Failed to import auth router
```
Fix:
```bash
cd backend
python -c "from app.routers import auth; print('OK')"
# Check traceback for missing import
pip install bcrypt python-jose sqlalchemy
```

---

## ISSUE 2: DATABASE CONNECTION FAILURE

### Symptoms
- All endpoints return 500
- Login returns 500 or "Internal server error"
- Logs: `[Database] Connection attempt N failed`

### Root Cause: DATABASE_URL is wrong or DB server is down

### Fix Steps

**For SQLite (dev):**
1. Check `gurukul.db` exists in the `backend/` directory
2. Check file permissions: `ls -la backend/gurukul.db`
3. If missing, just restart — SQLite is created automatically

**For PostgreSQL (prod):**
1. Test connection directly:
   ```bash
   psql "postgresql://user:password@host:5432/gurukul_db" -c "SELECT 1"
   ```
2. Check firewall: port 5432 must be open from backend host
3. Check DB user has CREATE TABLE permissions
4. Check connection string format: `postgresql://user:password@host:port/dbname`

**Force reconnect:**
```bash
# Restart backend — it will retry DB connection automatically (5 retries)
pkill uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

**For MongoDB:**
1. Test: `mongosh "mongodb://localhost:27017/gurukul_karma" --eval "db.runCommand({ping:1})"`
2. If it fails, check `mongod` is running: `sudo service mongod status`
3. Check `MONGO_URI` in `.env` matches actual MongoDB host/credentials
4. MongoDB failure does NOT kill the whole backend — karma features just stop working

---

## ISSUE 3: TTS FAILURE

### Symptoms
- `/api/v1/agent/tts` returns 503 with "All TTS engines failed"
- `/api/v1/tts/speak` returns 500
- Frontend has no audio

### Root Cause: All 3 TTS tiers failed (Vaani + OpenAI + gTTS)

### Fix Steps

**Check which tier is failing:**
```bash
# Test Vaani
curl http://localhost:8008/health

# Test gTTS (should always work unless no internet)
python3 -c "from gtts import gTTS; g=gTTS('hello', lang='en'); g.save('/tmp/test.mp3'); print('gTTS OK')"
```

**Vaani is down:**
```bash
cd vaani-engine
python main.py  # Start Vaani manually
# Check VAANI_API_URL in .env matches port Vaani is running on
```

**gTTS fails (no internet):**
- gTTS needs internet access to Google Translate
- Check network connectivity from backend host
- If behind proxy: set http_proxy env variable

**OpenAI TTS fails:**
- Check `OPENAI_API_KEY` is valid
- Check OpenAI account has TTS credits

**MongoDB cache is broken:**
- TTS still works without cache — error will just be in logs as "Cache lookup skipped"
- Check MongoDB connection (see Issue 2)

---

## ISSUE 4: AUTH ISSUES

### Symptoms
- Login returns 401 even with correct password
- "Could not validate credentials" on protected endpoints
- Token works then suddenly stops

### Root Causes & Fixes

**A) Wrong JWT_SECRET_KEY after restart**
```
JWTError: Signature verification failed
```
Fix: Tokens issued with old key are invalid after key change. Users must log in again.
**Never change JWT_SECRET_KEY in production without logging everyone out.**

**B) Token expired**
Default expiry is 7 days (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080`).
Fix: User must log in again. No refresh token mechanism currently exists.

**C) User not found in DB**
Happens if DB was wiped but tokens weren't invalidated.
Fix: User must register again.

**D) Role mismatch**
```
403: Only students can access Gurukul
```
This is expected — only STUDENT role can use Gurukul. ADMIN/TEACHER must use EMS at port 8000.

**E) `is_active=False`**
```
400: Inactive user
```
Fix (admin action):
```sql
UPDATE users SET is_active = true WHERE email = 'user@example.com';
```

---

## ISSUE 5: API TIMEOUT / SLOW RESPONSES

### Symptoms
- Requests hang for 30+ seconds then fail
- Chat endpoint is very slow
- Logs show Groq timeout

### Root Causes & Fixes

**A) Groq API is slow or down**
```bash
# Test Groq directly
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "hello"}]}'
```
Check Groq status page. If Groq is down, chat will fail. There's currently no fallback LLM that's always available unless Ollama is running locally.

**B) Ollama not running (LLM fallback)**
```
[LLM] Groq Failed. Falling back to Ollama...
Connection refused at localhost:11434
```
Fix: Either start Ollama or accept that chat is unavailable until Groq recovers.

**C) Vector store slow**
RAG context retrieval times out if ChromaDB is loading a large collection.
Fix: Set `use_rag: false` in chat request temporarily, or disable vector store.

**D) High load / rate limiting**
Backend has rate limiting middleware. Check if you're hitting the limit.
Look for `429 Too Many Requests` in responses.

**E) Check system metrics:**
```bash
curl http://localhost:3000/system/metrics
```
Look at `avg_latency_ms` — if > 5000ms, something is wrong upstream.

---

## ISSUE 6: CHAT HISTORY LOST

### Symptoms
- Conversation doesn't remember previous messages
- History cleared on its own

### Root Cause
Chat history is in-memory (`_chat_history` dict in `chat.py`). **Any backend restart wipes it.**

### Fix
This is a known limitation, not a bug. For production persistence:
1. Chat history would need to be stored in PostgreSQL `summaries` table
2. Currently not implemented — restart = lost history

**Workaround:** Use stable `conversation_id` (save it in frontend) so history is grouped correctly within a session.

---

## ISSUE 7: CORS ERRORS

### Symptoms
- Browser shows: `Access to fetch at ... has been blocked by CORS policy`
- Requests from frontend fail with network error

### Root Cause
The frontend origin is not in the allowed origins list in `main.py`.

### Fix
Add your frontend URL to `allow_origins` in `backend/app/main.py`:
```python
allow_origins=[
    "http://localhost:5173",
    "http://your-new-origin.com",   # ADD THIS
    ...
]
```
Restart backend.

---

## ISSUE 8: KARMA TRACKER BROKEN

### Symptoms
- `/api/v1/karma/...` returns 500
- "MongoDB collection is not available"

### Root Cause: MongoDB not connected

### Fix
1. Check MongoDB is running: `sudo service mongod status`
2. Check `MONGO_URI` in `.env`
3. Restart backend — MongoDB connection is retried
4. If MongoDB is permanently unavailable, karma features are non-functional but the rest of the app works

---

## GENERAL DEBUG TOOLS

### View live logs
```bash
# If running directly
uvicorn app.main:app --host 0.0.0.0 --port 3000 2>&1 | tee app.log

# If Docker
docker compose logs -f gurukul-backend
```

### Check registered routes
```bash
cd backend
python list_routes.py
```

### Health check
```bash
curl http://localhost:3000/
curl http://localhost:3000/system/metrics
```

### Test auth manually
```bash
# Register
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","role":"STUDENT"}'

# Login
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

### Check Swagger docs
Open `http://localhost:3000/docs` — if it loads, the backend is working.  
If it fails, check logs for OpenAPI generation errors.

---

## STARTUP LOG MEANING

| Log Line | Meaning |
|----------|---------|
| `[OK] FastAPI app initialized` | App object created |
| `[OK] Auth router registered` | Login/register endpoints live |
| `[OK] SQL database tables initialized` | Tables created/verified |
| `[WARN] MongoDB init warning` | MongoDB unavailable, karma disabled |
| `[WARN] chat failed:` | Chat router failed, chat endpoints broken |
| `[OK] ServiceWatchdog started` | Background health monitoring active |
| `[OK] Startup event complete!` | All systems up |
