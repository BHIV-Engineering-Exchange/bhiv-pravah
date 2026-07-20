# ARTHA — Complete Local Setup Guide

This folder contains everything you need to run Artha locally from scratch.
No Docker required. Pure manual setup — terminal by terminal.

---

## Files in this folder

| File | Purpose |
|------|---------|
| `LOCAL_SETUP.md` | This file — full step-by-step guide |
| `backend.env.template` | Copy-paste ready backend `.env` for local dev |
| `frontend.env.template` | Copy-paste ready frontend `.env` for local dev |
| `verify_setup.md` | How to verify every service is running correctly |
| `troubleshooting.md` | Common errors and exact fixes |

---

## What you will run

```
Terminal 1 — MongoDB (local)     → mongodb://localhost:27017
Terminal 2 — Backend API         → http://localhost:5000
Terminal 3 — Frontend (Vite)     → http://localhost:5173
Terminal 4 — Redis (optional)    → localhost:6379
```

---

## Prerequisites — Install these first

### 1. Node.js 18+

Download from https://nodejs.org/en/download  
Choose the LTS version (18.x or 20.x).

Verify:
```cmd
node --version
```
Expected: `v18.x.x` or higher

```cmd
npm --version
```
Expected: `9.x.x` or higher

---

### 2. MongoDB Community Server (local)

Download from https://www.mongodb.com/try/download/community  
Choose version **7.0**, Windows, MSI installer.

During install:
- Check "Install MongoDB as a Service"
- Check "Install MongoDB Compass" (optional GUI)

After install, MongoDB runs automatically as a Windows service.

Verify MongoDB is running:
```cmd
mongosh --eval "db.runCommand({ connectionStatus: 1 })"
```
Expected output contains: `"ok" : 1`

If not running, start it manually:
```cmd
net start MongoDB
```

Your local MongoDB URI will be:
```
mongodb://localhost:27017/artha
```

---

### 3. Git

Download from https://git-scm.com/download/win  
Use default settings during install.

Verify:
```cmd
git --version
```

---

### 4. Redis (Optional — app works without it)

Redis is used for caching only. The app gracefully skips it if not configured.

**Option A — Skip Redis entirely** (recommended for first run)  
Leave `REDIS_HOST` and `REDIS_URL` blank in your `.env`. The backend will log:
```
Redis not configured, skipping Redis connection
```
Everything works normally.

**Option B — Install Redis on Windows**  
Download Memurai (Redis-compatible for Windows):  
https://www.memurai.com/get-memurai  
Install and it runs as a Windows service on port 6379.

---

## Step 1 — Clone the repository

Open a terminal (Command Prompt or PowerShell):

```cmd
cd C:\Users\YourName\Projects
git clone https://github.com/blackholeinfiverse54-creator/Artha_Update_T29.git
cd Artha_Update_T29
```

Your project root is now:
```
C:\Users\YourName\Projects\Artha_Update_T29\
```

---

## Step 2 — Create the backend `.env` file

Navigate to the backend folder:
```cmd
cd backend
```

Create the `.env` file by copying the template:
```cmd
copy .env.example .env
```

Now open `.env` in any text editor (Notepad, VS Code, etc.) and fill in these values:

```env
# ── Server ────────────────────────────────────────────────────────────────────
NODE_ENV=development
PORT=5000
API_VERSION=v1
LOG_LEVEL=debug

# ── Database ──────────────────────────────────────────────────────────────────
# Local MongoDB (no auth required for local dev)
MONGODB_URI=mongodb://localhost:27017/artha
MONGODB_TEST_URI=mongodb://localhost:27017/artha_test

# ── JWT ───────────────────────────────────────────────────────────────────────
# Must be at least 32 characters. Use any random string.
# Example generator: open browser console → crypto.randomUUID()
JWT_SECRET=artha-local-dev-jwt-secret-change-this-32chars
JWT_EXPIRES_IN=7d

# ── URLs ──────────────────────────────────────────────────────────────────────
APP_URL=http://localhost:5000
FRONTEND_URL=http://localhost:5173
CORS_ORIGIN=http://localhost:5173

# ── Security ──────────────────────────────────────────────────────────────────
# Used for ledger HMAC hash chain. Any random string works for local dev.
HMAC_SECRET=artha-local-hmac-secret-for-ledger-chain

RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX=1000

# ── Redis (leave blank to skip — app works without it) ────────────────────────
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=

# ── SETU Integration (leave as-is for local dev) ─────────────────────────────
SETU_ENABLED=false
SETU_BASE_URL=https://setu.example.com
SETU_API_KEY=
SETU_TIMEOUT_MS=5000

# ── InsightCore (leave as-is for local dev) ───────────────────────────────────
INSIGHTCORE_ENDPOINT=http://localhost:8000/telemetry
INSIGHTCORE_ENABLED=false

# ── File Storage ──────────────────────────────────────────────────────────────
STORAGE_TYPE=local
```

Save the file.

> **Important:** `JWT_SECRET` and `HMAC_SECRET` must each be at least 32 characters.
> For local dev, the example values above work fine.
> Never use these values in production.

---

## Step 3 — Create the frontend `.env` file

Go back to the project root, then into the frontend folder:
```cmd
cd ..
cd frontend
```

Create the `.env` file:
```cmd
copy .env.example .env
```

If `.env.example` does not exist in frontend, create `.env` manually with this content:

```env
VITE_API_URL=http://localhost:5000/api/v1
```

That is the only variable the frontend needs for local development.

Save the file.

---

## Step 4 — Install backend dependencies

```cmd
cd ..\backend
npm install
```

This installs all packages from `package.json` including:
- express, mongoose, jsonwebtoken, bcryptjs
- decimal.js, helmet, express-rate-limit
- winston, multer, pdfkit, xlsx
- nodemon (dev)

Expected output ends with something like:
```
added 312 packages in 45s
```

---

## Step 5 — Install frontend dependencies

```cmd
cd ..\frontend
npm install
```

This installs:
- react, react-dom, react-router-dom
- axios, zustand, @tanstack/react-query
- recharts, tailwindcss, lucide-react
- vite (dev)

Expected output ends with:
```
added 287 packages in 30s
```

---

## Step 6 — Verify MongoDB is running

Open a new terminal and run:
```cmd
mongosh
```

You should see the MongoDB shell prompt:
```
test>
```

Type this to confirm the connection:
```js
db.runCommand({ ping: 1 })
```
Expected: `{ ok: 1 }`

Type `exit` to leave the shell.

---

## Step 7 — Seed the database

The database needs initial data: 33 Chart of Accounts, sample invoices,
sample expenses, and TDS entries.

Make sure you are in the backend folder:
```cmd
cd C:\Users\YourName\Projects\Artha_Update_T29\backend
```

Run the main seed:
```cmd
node scripts/seed.js
```

Expected output:
```
MongoDB Connected: localhost
Seeding Chart of Accounts...
Created 33 accounts
Seeding sample invoices...
Seeding sample expenses...
Database seeded successfully
```

Run the TDS seed:
```cmd
node scripts/seed-tds.js
```

Expected output:
```
TDS entries seeded: 6 entries for Q4 FY2025-26
```

---

## Step 8 — Start the backend

Open a **new terminal window** (keep it open — this is Terminal 2).

```cmd
cd C:\Users\YourName\Projects\Artha_Update_T29\backend
npm run dev
```

Expected output:
```
[nodemon] starting `node src/server.js`
MongoDB Connected: localhost
⚠️  Not running as replica set - transactions disabled
Redis not configured, skipping Redis connection
Server running on port 5000
SPA (public app): http://localhost:5173
API public URL: http://localhost:5000
```

> The "transactions disabled" warning is normal for local MongoDB without a replica set.
> All features work — only multi-step operations lose ACID rollback on failure.

The backend is now running at: **http://localhost:5000**

---

## Step 9 — Start the frontend

Open another **new terminal window** (Terminal 3).

```cmd
cd C:\Users\YourName\Projects\Artha_Update_T29\frontend
npm run dev
```

Expected output:
```
  VITE v5.x.x  ready in 800ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

The frontend is now running at: **http://localhost:5173**

---

## Step 10 — Open the application

Open your browser and go to:
```
http://localhost:5173
```

You will see the Artha login page.

### Create your first account

Click **Sign Up** and fill in:
- Name: `Admin User`
- Email: `admin@artha.local`
- Password: `admin123`

> New accounts default to `viewer` role. To get full access, you need to
> manually update the role in MongoDB. See Step 11.

---

## Step 11 — Set admin role (one-time)

Open a terminal and connect to MongoDB:
```cmd
mongosh
```

Switch to the artha database and update your user:
```js
use artha
db.users.updateOne(
  { email: "admin@artha.local" },
  { $set: { role: "admin" } }
)
```

Expected: `{ acknowledged: true, matchedCount: 1, modifiedCount: 1 }`

Type `exit` to leave the shell.

Now log out and log back in at http://localhost:5173.
You will have full admin access.

---

## Step 12 — Configure Company Settings (required for GST)

Before creating invoices with GST, you must set up company settings.

1. Go to **Settings → Company** in the sidebar
2. Fill in:
   - Company Name: `Your Company Name`
   - GSTIN: `27AABCU9603R1ZX` (use a valid format for testing)
   - State: `MH` (or your state code)
   - Address fields
3. Click Save

> Without company settings, sending invoices will throw:
> `Company state is required for GST`

---

## Step 13 — Verify integrity

In the backend terminal, run:
```cmd
node scripts/verify-integrity.js
```

Expected output:
```
✓ All sent invoices have journal entries
✓ All paid invoices have payment entries
✓ Accounting equation: Debits = Credits
✓ Account balances match journal entries
✓ GST calculations match invoice data
✓ Reports pull from real-time data
```

---

## Running summary — what to start each time

Every time you want to run Artha locally, open 3 terminals:

**Terminal 1 — Verify MongoDB is running**
```cmd
net start MongoDB
```
(Skip if already running as a service)

**Terminal 2 — Backend**
```cmd
cd C:\Users\YourName\Projects\Artha_Update_T29\backend
npm run dev
```

**Terminal 3 — Frontend**
```cmd
cd C:\Users\YourName\Projects\Artha_Update_T29\frontend
npm run dev
```

Then open: **http://localhost:5173**

---

## Access URLs

| Service | URL |
|---------|-----|
| Frontend (React app) | http://localhost:5173 |
| Backend API | http://localhost:5000 |
| API Health check | http://localhost:5000/health |
| API test endpoint | http://localhost:5000/api/test |
| MongoDB (local) | mongodb://localhost:27017/artha |

---

## API quick test (optional)

Test the backend is responding without logging in:
```cmd
curl http://localhost:5000/health
```

Expected:
```json
{ "success": true, "status": "healthy" }
```

Test login via API:
```cmd
curl -X POST http://localhost:5000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@artha.local\",\"password\":\"admin123\"}"
```

Expected:
```json
{ "success": true, "data": { "token": "eyJ...", "user": { ... } } }
```
