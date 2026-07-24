# 🔧 QUICK FIX: Core Integration Endpoints Not Loaded

## Problem
The Core integration endpoints (`/core/write-event`, `/core/stats`, `/core/events`, `/core/read-context`) are returning 404 errors because the Bucket service was started BEFORE these endpoints were added to the code.

## Solution
**You need to RESTART the Bucket service to load the new endpoints.**

### Option 1: Automatic Restart (Easiest)
```bash
restart_bucket.bat
```

### Option 2: Manual Restart

1. **Stop Bucket:**
   - Press `Ctrl+C` in the terminal running Bucket
   - OR run: `taskkill /F /PID 23340` (replace with actual PID from `netstat -ano | findstr :8000`)

2. **Start Bucket:**
   ```bash
   cd BHIV_Central_Depository-main
   python main.py
   ```

3. **Wait 5 seconds** for Bucket to fully start

4. **Test the integration:**
   ```bash
   python test_integration.py
   ```

## Verification
After restart, you should see:
- ✅ All 4 Core integration endpoints responding (not 404)
- ✅ `/core/write-event` accepts events
- ✅ `/core/stats` returns statistics
- ✅ `/core/events` returns event list
- ✅ `/core/read-context` returns agent context

## Why This Happened
The endpoints were added to `main.py` AFTER the Bucket service was already running. Python doesn't hot-reload code changes automatically, so a restart is required.

## Next Steps
1. Run `restart_bucket.bat` OR manually restart Bucket
2. Run `python test_integration.py` to verify all endpoints work
3. Both Core and Bucket should now communicate successfully! 🎉
