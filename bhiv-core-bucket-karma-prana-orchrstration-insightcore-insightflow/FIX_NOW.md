# 🚨 IMMEDIATE FIX - Port 8000 Showing Workflow Instead of Karma

## THE PROBLEM
Workflow Executor is running on port 8000 (Karma's port). You're seeing Workflow endpoints at http://localhost:8000/docs

## THE SOLUTION (Do This NOW)

### Step 1: Close ALL Terminal Windows
Look at your screen and **manually close** every terminal/command prompt window that shows:
- `python main.py`
- `uvicorn main:app`
- Any Python process

**CLOSE THEM ALL** - Press CTRL+C or click the X button.

### Step 2: Verify Nothing is Running
Open a NEW terminal and run:
```bash
netstat -ano | findstr ":8000"
```

If you see ANYTHING, note the PID numbers and run:
```bash
taskkill /F /PID <number>
```

For example, if you see PID 24144:
```bash
taskkill /F /PID 24144
```

### Step 3: Start ONLY Karma on Port 8000
Open a NEW terminal:
```bash
cd karma_chain_v2-main
python main.py
```

**WAIT** - You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Verify Karma is Running
Open browser: http://localhost:8000/docs

**You should see**: "KarmaChain v2" (NOT "Workflow Executor")

If you still see "Workflow Executor", go back to Step 1 - you didn't close all terminals!

### Step 5: Start Other Services
Only AFTER Karma is confirmed on port 8000:

**Terminal 2:**
```bash
cd BHIV_Central_Depository-main
python main.py
```

**Terminal 3:**
```bash
cd v1-BHIV_CORE-main
python mcp_bridge.py
```

**Terminal 4:**
```bash
cd workflow-executor-main
python main.py
```

This should show: `Uvicorn running on http://0.0.0.0:8003`

---

## CHECKLIST

- [ ] Closed ALL terminal windows
- [ ] Verified port 8000 is free (netstat shows nothing)
- [ ] Started Karma on port 8000
- [ ] Verified http://localhost:8000/docs shows "KarmaChain v2"
- [ ] Started other services
- [ ] Verified http://localhost:8003/docs shows "Workflow Executor"

---

## IF STILL NOT WORKING

**Option 1: Restart Computer**
This will kill ALL processes and free all ports.

**Option 2: Use Task Manager**
1. Open Task Manager (CTRL+SHIFT+ESC)
2. Find all "Python" processes
3. Right-click → End Task on each one
4. Start services again

---

**The issue is NOT in the code - it's that old processes are still running!**
