# CORS Error Fix Guide

## 🔴 Error You're Seeing

```
Access to fetch at 'http://localhost:3000/api/v1/learning/explore' from origin 'http://localhost:5173' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

## ✅ What This Means

**CORS (Cross-Origin Resource Sharing)** is a browser security feature. Your frontend (localhost:5173) is trying to access your backend (localhost:3000), but the browser is blocking it because:
1. Backend isn't running, OR
2. Backend crashed, OR
3. CORS headers aren't being sent

## 🔧 Quick Fixes

### **Fix 1: Check if Backend is Running**

```powershell
# Check if backend is running on port 3000
netstat -ano | findstr :3000
```

**If nothing shows up:** Backend is NOT running.

**Start it:**
```powershell
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

---

### **Fix 2: Restart Backend (After Our Changes)**

We just updated the code, so you need to restart:

```powershell
# Stop the current backend (Ctrl+C)
# Then restart:
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

**Look for this in the output:**
```
Gurukul API v2 (Refactored) Started at http://0.0.0.0:3000
```

---

### **Fix 3: Verify CORS is Working**

**Test in browser:**
1. Open: `http://localhost:3000/docs`
2. Should see FastAPI docs page
3. If you see it → Backend is running ✅

**Test CORS directly:**
```javascript
// In browser console (on localhost:5173)
fetch('http://localhost:3000/api/v1/chat/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

**Expected:** `{status: "ok"}`  
**If error:** Backend not running or CORS issue

---

### **Fix 4: Check Backend Logs**

When you start the backend, check for errors:

**Common errors:**
- `ModuleNotFoundError` → Missing dependencies
- `ImportError` → Code import issue
- `Port already in use` → Another process using port 3000

**Solution:**
```powershell
# Install missing dependencies
cd backend
pip install -r requirements.txt

# Or kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

---

### **Fix 5: Verify CORS Configuration**

The CORS is already configured in `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**This should work!** If it doesn't, the backend isn't running.

---

## 🧪 Step-by-Step Test

### **Step 1: Start Backend**
```powershell
cd C:\Users\Yashika\gurukul-backend-\backend
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:3000
Gurukul API v2 (Refactored) Started at http://0.0.0.0:3000
```

---

### **Step 2: Test Backend Directly**

Open browser: `http://localhost:3000/docs`

**Should see:** FastAPI Swagger UI

---

### **Step 3: Test from Frontend**

In browser console (on localhost:5173):
```javascript
fetch('http://localhost:3000/api/v1/chat/health', {
  method: 'GET',
  headers: {'Content-Type': 'application/json'}
})
.then(r => r.json())
.then(console.log)
```

**Expected:** `{status: "ok"}`  
**If CORS error:** Backend not running or crashed

---

### **Step 4: Test Learning Endpoint**

```javascript
fetch('http://localhost:3000/api/v1/learning/explore', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    subject: 'Math',
    topic: 'Algebra'
  })
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

---

## 🐛 Common Issues

### **Issue 1: Backend Crashed on Startup**

**Check for errors:**
- Missing imports
- Database connection failed
- Vector store initialization failed

**Solution:**
```powershell
# Check what error backend shows
# Fix the error
# Restart backend
```

---

### **Issue 2: Port Already in Use**

**Error:** `Address already in use`

**Solution:**
```powershell
# Find process using port 3000
netstat -ano | findstr :3000

# Kill it
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --port 3001
```

---

### **Issue 3: Import Errors**

**Error:** `ModuleNotFoundError: No module named 'app.services.knowledge_base_helper'`

**Solution:**
```powershell
# Make sure you're in backend directory
cd backend

# Verify file exists
dir app\services\knowledge_base_helper.py

# If missing, check git status
git status
```

---

## ✅ Verification Checklist

- [ ] Backend is running (check `http://localhost:3000/docs`)
- [ ] No errors in backend console
- [ ] CORS middleware is loaded (check startup logs)
- [ ] Frontend can reach backend (test `/health` endpoint)
- [ ] Authentication token is valid (if required)

---

## 🚀 Quick Start Commands

```powershell
# Terminal 1: Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload

# Terminal 2: Frontend (if not running)
cd Frontend
npm run dev
```

---

## 📝 Summary

**The CORS error usually means:**
1. ✅ Backend is NOT running → Start it
2. ✅ Backend crashed → Check logs, fix error, restart
3. ✅ Backend needs restart after code changes → Restart it

**The CORS configuration is correct** - the issue is likely that the backend isn't running or needs a restart after our changes.

---

## 🔍 Still Not Working?

1. **Check backend logs** for errors
2. **Verify backend is on port 3000**: `http://localhost:3000/docs`
3. **Test with curl:**
   ```bash
   curl http://localhost:3000/api/v1/chat/health
   ```
4. **Check firewall** isn't blocking port 3000
5. **Try different port** (3001, 8000) to rule out port conflicts

---

**Most likely solution:** Restart your backend server after our code changes! 🚀
