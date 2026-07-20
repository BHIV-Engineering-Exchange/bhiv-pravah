# ENV SETUP GUIDE
## Environment Variables, Dependencies, Ports, Services

---

## 1. .env TEMPLATE (Copy to `backend/.env`)

```dotenv
# ─────────────────────────────────────────────────
# GURUKUL BACKEND — ENVIRONMENT CONFIGURATION
# Copy this file to backend/.env and fill in values
# ─────────────────────────────────────────────────

# ── Server ──────────────────────────────────────
HOST=0.0.0.0
PORT=3000
ENV=dev

# ── SQL Database ─────────────────────────────────
# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost:5432/gurukul_db
# SQLite (local dev — leave DATABASE_URL blank to use this automatically)
# No setting needed — backend falls back to sqlite:///./gurukul.db

# ── MongoDB (Karma Tracker) ───────────────────────
MONGO_URI=mongodb://localhost:27017/gurukul_karma
# OR MongoDB Atlas:
# MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/gurukul_karma

# ── Redis (PRANA Queue — optional) ───────────────
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_USERNAME=

# ── JWT Auth ──────────────────────────────────────
JWT_SECRET_KEY=change-this-to-a-long-random-secret-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# ── Groq (LLM + Whisper STT) ─────────────────────
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_API_ENDPOINT=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL_NAME=llama-3.3-70b-versatile

# ── OpenAI (Optional TTS fallback) ───────────────
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── Google Gemini (Optional) ─────────────────────
GEMINI_API_KEY=

# ── YouTube API (Learning recommendations) ───────
YOUTUBE_API_KEY=

# ── Vaani (Sovereign TTS engine) ─────────────────
VAANI_API_URL=http://localhost:8008

# ── Ollama (Local LLM fallback) ──────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_PRIMARY=llama2

# ── EMS Integration ───────────────────────────────
EMS_API_BASE_URL=http://localhost:8000
EMS_API_KEY=
EMS_ADMIN_EMAIL=
EMS_ADMIN_PASSWORD=
EMS_DEFAULT_SCHOOL_ID=
EMS_AUTO_CREATE_STUDENTS=false

# ── TANTRA Integration (optional telemetry) ───────
PRAVAH_URL=                          # e.g. https://pravah.tantra.io/ingest
BUCKET_URL=                          # e.g. https://bucket.tantra.io/write
TANTRA_API_KEY=                      # Shared secret
TANTRA_DEBUG_LOG=false               # Set true to write to runtime_events.json

# ── Vector Store (RAG — disabled in prod to save memory) ──
VECTOR_STORE_BACKEND=chromadb        # chromadb | faiss | qdrant
VECTOR_STORE_PATH=./knowledge_store
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_COLLECTION=knowledge_base

# ── Multi-Tenant (disabled by default) ───────────
MULTI_TENANT_ENABLED=false
CENTRAL_DATABASE_URL=                # Only needed if MULTI_TENANT_ENABLED=true
TENANT_BASE_DOMAIN=gurukul.blackholeinfiverse.com

# ── Feature Flags ─────────────────────────────────
PDF_SUPPORT=true
DOC_SUMMARIZER_SUPPORT=false
PDF_SUMMARIZER_SUPPORT=false

# ── Demo Seeding (CI/testing only) ────────────────
AUTO_SEED_DEMO=false
```

---

## 2. REQUIRED vs OPTIONAL VARIABLES

### REQUIRED (backend won't work without these)
| Variable | Why Required |
|----------|-------------|
| `GROQ_API_KEY` | Chat, STT, LLM generation all fail without it |
| `JWT_SECRET_KEY` | Auth completely broken without this (default is insecure placeholder) |
| `DATABASE_URL` | Use PostgreSQL in prod; SQLite auto-used in dev |

### HIGHLY RECOMMENDED
| Variable | Why |
|----------|-----|
| `MONGO_URI` | Karma tracker won't work without it |
| `VAANI_API_URL` | TTS tier 1 unavailable, falls back to OpenAI/gTTS |

### OPTIONAL
| Variable | Effect if Missing |
|----------|-----------------|
| `OPENAI_API_KEY` | TTS tier 2 unavailable (uses gTTS instead) |
| `PRAVAH_URL` | TANTRA signals silently dropped |
| `BUCKET_URL` | Memory events silently dropped |
| `YOUTUBE_API_KEY` | No YouTube recommendations in lesson notes |
| `REDIS_HOST/PORT` | PRANA queue falls back to in-memory |
| `EMS_API_BASE_URL` | EMS sync features unavailable |

---

## 3. EXTERNAL SERVICES

| Service | URL | What Uses It | Cost |
|---------|-----|-------------|------|
| Groq API | api.groq.com | Chat LLM + Whisper STT | Free tier available |
| OpenAI API | api.openai.com | TTS fallback (optional) | Paid |
| Google Gemini | generativelanguage.googleapis.com | Optional LLM | Free tier |
| YouTube Data API | googleapis.com | Learning video recommendations | Free quota |
| gTTS | translate.google.com | TTS tier 3 fallback | Free (no key) |
| Render | render.com | Cloud hosting | Paid |

---

## 4. REQUIRED SERVICES (LOCAL / DOCKER)

| Service | Port | Required? | Install |
|---------|------|-----------|---------|
| PostgreSQL | 5432 | Yes (prod) | `apt install postgresql` or Docker |
| MongoDB | 27017 | Yes (karma) | `apt install mongodb` or Docker |
| Redis | 6379 | Optional | `apt install redis-server` |
| Vaani Engine | 8008 | Recommended | `cd vaani-engine && python main.py` |
| Ollama | 11434 | Optional (LLM fallback) | ollama.ai |

---

## 5. PYTHON DEPENDENCIES

From `backend/requirements.txt`:

**Core:**
- `fastapi==0.111.0` — Web framework
- `uvicorn[standard]==0.30.1` — ASGI server
- `pydantic==2.7.4` + `pydantic-settings==2.3.1` — Validation & settings
- `sqlalchemy==2.0.31` — ORM
- `psycopg2-binary==2.9.9` — PostgreSQL driver
- `python-jose[cryptography]==3.3.0` — JWT
- `bcrypt` + `passlib[bcrypt]` — Password hashing

**AI/ML:**
- `groq==0.30.0` — Groq Python SDK
- `google-generativeai==0.8.3` — Gemini SDK
- `openai>=1.0.0` — OpenAI SDK
- `gTTS==2.5.1` + `pyttsx3==2.90` — TTS engines
- `faster-whisper>=1.0.0` — Local STT

**Storage:**
- `pymongo==4.7.3` — MongoDB driver
- `redis==5.0.6` — Redis client

**Utils:**
- `requests==2.32.3` — HTTP client
- `httpx==0.27.0` — Async HTTP client
- `python-multipart` — File upload support
- `aiohttp==3.9.5` — Async HTTP

**DISABLED (too heavy for 512MB Render):**
- `torch`, `transformers`, `sentence-transformers` — Vector store embedding models
- `chromadb`, `qdrant-client` — Vector databases

---

## 6. PORTS SUMMARY

| Service | Port | Protocol |
|---------|------|----------|
| Gurukul Backend | 3000 | HTTP |
| EMS Backend | 8000 | HTTP |
| Gurukul Frontend (dev) | 5173 | HTTP |
| EMS Frontend (dev) | 3001 | HTTP |
| Vaani Engine | 8008 | HTTP |
| PostgreSQL | 5432 | TCP |
| MongoDB | 27017 | TCP |
| Redis | 6379 | TCP |
| Ollama | 11434 | HTTP |

---

## 7. STARTUP SEQUENCE

Correct order to start services locally:

```bash
# 1. Start PostgreSQL (if using)
sudo service postgresql start

# 2. Start MongoDB
sudo service mongod start

# 3. Start Redis (optional)
sudo service redis-server start

# 4. Start Vaani Engine (optional, for TTS tier 1)
cd vaani-engine
pip install -r requirements.txt
python main.py &

# 5. Start Gurukul Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # edit with your values
uvicorn app.main:app --host 0.0.0.0 --port 3000

# 6. Start Frontend (dev)
cd Frontend
npm install
npm run dev
```

Or use the provided script:
```bash
bash backend/start_gurukul_services.sh
```

Or Docker:
```bash
cd docker
docker compose up --build
```

---

## 8. PRODUCTION (RENDER) SETUP

1. Create PostgreSQL database on Render → copy connection string to `DATABASE_URL`
2. Set all env vars in Render dashboard (Settings → Environment)
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Health check path: `/`
6. **Do NOT commit `.env` to git**

CORS origins already include `https://gurukul-frontend-738j.onrender.com` and `https://gurukul.blackholeinfiverse.com`.
