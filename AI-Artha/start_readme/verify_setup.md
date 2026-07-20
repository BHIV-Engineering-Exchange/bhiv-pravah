# Verify Setup — Artha Local

Run these checks in order after completing LOCAL_SETUP.md.
Each check tells you exactly what a passing result looks like.

---

## Check 1 — Node.js version

```cmd
node --version
```
Pass: `v18.x.x` or `v20.x.x`  
Fail: anything below `v18` → reinstall Node from nodejs.org

---

## Check 2 — MongoDB is running

```cmd
mongosh --eval "db.runCommand({ ping: 1 })" --quiet
```
Pass: `{ ok: 1 }`  
Fail: `MongoNetworkError` → run `net start MongoDB` then retry

---

## Check 3 — Backend .env exists and has required keys

```cmd
cd backend
node -e "require('dotenv').config(); ['MONGODB_URI','JWT_SECRET','HMAC_SECRET'].forEach(k => console.log(k, process.env[k] ? 'OK' : 'MISSING'))"
```
Pass:
```
MONGODB_URI OK
JWT_SECRET OK
HMAC_SECRET OK
```
Fail: `MISSING` → open `backend/.env` and fill in the missing value

---

## Check 4 — Backend starts without errors

```cmd
cd backend
npm run dev
```
Pass — you see ALL of these lines:
```
MongoDB Connected: localhost
Server running on port 5000
```

Fail scenarios:
- `MongoServerError: connect ECONNREFUSED` → MongoDB not running, run `net start MongoDB`
- `Error: JWT_SECRET is required` → `JWT_SECRET` missing in `backend/.env`
- `SyntaxError` → Node version too old, upgrade to 18+
- `Cannot find module` → run `npm install` first

---

## Check 5 — Backend health endpoint responds

Open a new terminal (keep backend running in the other one):
```cmd
curl http://localhost:5000/health
```
Pass:
```json
{"success":true,"status":"healthy","..."}
```

Fail: `curl: (7) Failed to connect` → backend is not running

---

## Check 6 — Frontend .env exists

```cmd
cd frontend
type .env
```
Pass: shows `VITE_API_URL=http://localhost:5000/api/v1`  
Fail: `The system cannot find the file` → create `frontend/.env` from the template

---

## Check 7 — Frontend starts without errors

```cmd
cd frontend
npm run dev
```
Pass:
```
  VITE v5.x.x  ready in xxxms
  ➜  Local:   http://localhost:5173/
```

Fail:
- `Error: Cannot find module` → run `npm install` first
- Port 5173 already in use → close other Vite instances or change port

---

## Check 8 — Frontend loads in browser

Open: http://localhost:5173  
Pass: Artha login page loads with the ARTHA logo  
Fail: blank page or network error → check browser console (F12) for errors

---

## Check 9 — Login works

1. Go to http://localhost:5173/signup
2. Create account: `admin@artha.local` / `admin123`
3. You should be redirected to the dashboard

Pass: Dashboard loads with "Financial Intelligence" view  
Fail: `Invalid email or password` → user was not created, try signup again

---

## Check 10 — Database has seed data

After seeding (Step 7 in LOCAL_SETUP.md), verify in mongosh:
```cmd
mongosh
```
```js
use artha
db.chartofaccounts.countDocuments()
```
Pass: `33`  
Fail: `0` → run `node scripts/seed.js` from the backend folder

```js
db.tdsentry.countDocuments()
```
Pass: `6`  
Fail: `0` → run `node scripts/seed-tds.js` from the backend folder

---

## Check 11 — Ledger chain integrity

```cmd
cd backend
node scripts/verify-integrity.js
```
Pass: all lines show `✓`  
Fail: any `✗` line → check the specific error message and re-seed if needed

---

## Check 12 — Signal snapshot endpoint works

With backend running, in a new terminal:
```cmd
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5000/api/v1/signals/snapshot
```

To get a token first:
```cmd
curl -X POST http://localhost:5000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@artha.local\",\"password\":\"admin123\"}"
```
Copy the `token` value from the response, then use it in the snapshot call.

Pass:
```json
{"success":true,"data":{"source":"ledger-only","cashFlow":"0","tdsPayable":"0","outputCGST":"0","outputSGST":"0"}}
```

---

## All checks passed?

You are ready. Open http://localhost:5173 and start using Artha.

Next steps:
1. Go to Settings → Company and fill in your company details + GSTIN
2. Create a test invoice at Invoices → New Invoice
3. Send the invoice to see the journal entry created automatically
4. Check Journal Entries in the Accounting section
