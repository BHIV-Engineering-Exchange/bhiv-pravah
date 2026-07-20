# Troubleshooting — Artha Local Setup

---

## Backend errors

### `MongoServerSelectionError: connect ECONNREFUSED 127.0.0.1:27017`

MongoDB is not running.

```cmd
net start MongoDB
```

If that fails:
```cmd
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath "C:\data\db"
```

If `C:\data\db` does not exist:
```cmd
mkdir C:\data\db
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath "C:\data\db"
```

---

### `Error: JWT_SECRET is required` or `Missing JWT verification secret`

Your `backend/.env` is missing `JWT_SECRET`.

Open `backend/.env` and add:
```env
JWT_SECRET=artha-local-dev-jwt-secret-change-this-32chars
```

The value must be at least 32 characters.

---

### `Error: HMAC_SECRET` or ledger hash errors

Your `backend/.env` is missing `HMAC_SECRET`.

Add:
```env
HMAC_SECRET=artha-local-hmac-secret-for-ledger-chain
```

> Warning: if you change `HMAC_SECRET` after seeding, all existing ledger
> hashes become invalid. Re-seed the database if this happens:
> ```cmd
> node scripts/seed.js
> ```

---

### `Cannot find module 'express'` or similar

Dependencies not installed.

```cmd
cd backend
npm install
```

---

### `SyntaxError: Cannot use import statement`

Node.js version is too old. The backend uses ES Modules (`"type": "module"`).

Check your version:
```cmd
node --version
```

If below v18, download Node 18 LTS from https://nodejs.org and reinstall.

---

### `Port 5000 is already in use`

Another process is using port 5000.

Find and kill it:
```cmd
netstat -ano | findstr :5000
```
Note the PID in the last column, then:
```cmd
taskkill /PID <PID> /F
```

Or change the backend port in `backend/.env`:
```env
PORT=5001
```
And update `frontend/.env`:
```env
VITE_API_URL=http://localhost:5001/api/v1
```

---

### `Company state is required for GST` when sending an invoice

Company settings are not configured.

1. Go to http://localhost:5173/settings/company
2. Fill in Company Name, GSTIN, and State
3. Save
4. Try sending the invoice again

---

### `Only draft invoices can be sent`

The invoice is already in `sent`, `partial`, or `paid` status.
You cannot re-send it. Create a new invoice.

---

### `Journal entry is already posted`

You are trying to post an entry that is already posted.
This is expected behavior — each entry can only be posted once.

---

### `Cannot post unvalidated entry`

The journal entry lifecycle is: DRAFT → VALIDATED → POSTED.
You cannot skip validation. This is enforced by the system.
If you created a manual journal entry, validate it first via the API:
```
POST /api/v1/ledger/entries/:id/validate
```

---

## Frontend errors

### Blank page at http://localhost:5173

Check the browser console (F12 → Console tab).

Common causes:
- `frontend/.env` missing → create it with `VITE_API_URL=http://localhost:5000/api/v1`
- Vite not started → run `npm run dev` in the frontend folder
- Build error → check the terminal where you ran `npm run dev`

---

### `Network Error` or `ERR_CONNECTION_REFUSED` on API calls

The backend is not running or is on a different port.

1. Check backend terminal — is it still running?
2. Check `frontend/.env` — does `VITE_API_URL` match the backend port?
3. Restart both backend and frontend

---

### `Session expired. Please sign in again.` immediately after login

The JWT token is invalid or the `JWT_SECRET` changed.

1. Clear browser localStorage:
   - F12 → Application → Local Storage → http://localhost:5173 → Clear All
2. Log in again

---

### `You do not have permission to perform this action`

Your user role is `viewer`. You need `admin` or `accountant` role.

Fix in mongosh:
```js
use artha
db.users.updateOne(
  { email: "your@email.com" },
  { $set: { role: "admin" } }
)
```

Then log out and log back in.

---

### Port 5173 already in use

```cmd
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

Or start Vite on a different port:
```cmd
npx vite --port 5174
```
And update `backend/.env`:
```env
FRONTEND_URL=http://localhost:5174
CORS_ORIGIN=http://localhost:5174
```

---

## Database errors

### Seed script fails with `duplicate key error`

The database already has seed data. Either:

**Option A — Skip seeding** (data already exists, this is fine)

**Option B — Re-seed from scratch**
```cmd
mongosh
```
```js
use artha
db.dropDatabase()
exit
```
Then re-run:
```cmd
node scripts/seed.js
node scripts/seed-tds.js
```

---

### `MongooseError: Operation ... buffering timed out`

MongoDB connection dropped. Restart MongoDB:
```cmd
net stop MongoDB
net start MongoDB
```
Then restart the backend.

---

## Redis errors

### `Redis connection error: connect ECONNREFUSED`

Redis is not running. Either:

**Option A — Disable Redis** (recommended for local dev)  
In `backend/.env`, comment out or remove:
```env
# REDIS_HOST=localhost
# REDIS_PORT=6379
```
The app will log `Redis not configured, skipping Redis connection` and work normally.

**Option B — Start Redis**  
If you installed Memurai:
```cmd
net start Memurai
```

---

## Still stuck?

1. Check the backend terminal for the full error stack trace
2. Check `backend/.env` has all required values (MONGODB_URI, JWT_SECRET, HMAC_SECRET)
3. Make sure MongoDB is running: `mongosh --eval "db.runCommand({ping:1})"`
4. Make sure you ran `npm install` in both `backend/` and `frontend/`
5. Make sure Node.js is v18+: `node --version`
