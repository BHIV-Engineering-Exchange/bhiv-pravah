# 🚀 Insight Flow Quick Setup Guide

## ✅ Environment Configuration Complete

Your `.env` file has been created with Supabase credentials.

---

## 📋 Setup Steps

### Step 1: Initialize Supabase Database

1. Go to: https://nzkqubedbeiqdxtpsves.supabase.co
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `setup_supabase.sql`
4. Click **Run** to create tables and sample agents

### Step 2: Install Dependencies

```bash
cd "Insight_Flow-main\backend"

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Start Insight Flow Backend

```bash
# Option 1: Using startup script
cd "Insight_Flow-main"
start_insight_flow.bat

# Option 2: Manual start
cd "Insight_Flow-main\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload
```

### Step 4: Start Insight Flow Bridge

```bash
# New terminal
cd "Insight_Flow-main"
python insight_flow_bridge.py
```

### Step 5: Verify Integration

```bash
# Check backend health
curl http://localhost:8007/health

# Check bridge health
curl http://localhost:8006/health

# Test routing
curl -X POST "http://localhost:8006/route" \
  -H "Content-Type: application/json" \
  -d "{\"input_data\": {\"text\": \"test\"}, \"input_type\": \"text\"}"
```

---

## 🔧 Configuration Details

### Supabase Connection
- **URL**: https://nzkqubedbeiqdxtpsves.supabase.co
- **Database**: PostgreSQL (managed by Supabase)
- **Tables**: agents, routing_logs, feedback_events, q_learning_table

### Service Ports
- **Insight Flow Backend**: 8007
- **Insight Flow Bridge**: 8006
- **Karma Integration**: 8000 (your existing Karma service)

### Features Enabled
- ✅ Q-Learning routing
- ✅ Karma weighting (connects to port 8000)
- ✅ Supabase database
- ✅ JWT authentication
- ✅ Telemetry security
- ❌ STP wrapping (disabled for simplicity)
- ❌ Sovereign Core (using Supabase instead)

---

## 🧪 Testing

### Test 1: Backend Health
```bash
curl http://localhost:8007/health
```
Expected: `{"status": "healthy", "app": "InsightFlow", ...}`

### Test 2: Bridge Health
```bash
curl http://localhost:8006/health
```
Expected: `{"status": "ok", "service": "Insight Flow Bridge", ...}`

### Test 3: Agent Routing
```bash
curl -X POST "http://localhost:8006/route-agent" \
  -H "Content-Type: application/json" \
  -d "{\"agent_type\": \"nlp\", \"confidence_threshold\": 0.75}"
```

### Test 4: Analytics
```bash
curl http://localhost:8006/analytics
```

---

## 🔍 Troubleshooting

### Issue: Database connection failed
**Solution**: Verify Supabase SQL script was run successfully

### Issue: Module not found
**Solution**: 
```bash
cd backend
pip install -r requirements.txt
pip install asyncpg python-dotenv supabase
```

### Issue: Port already in use
**Solution**: 
```bash
# Check what's using port 8007
netstat -ano | findstr :8007

# Kill process if needed
taskkill /PID <process_id> /F
```

---

## 📊 System Architecture

```
User Request
     ↓
Insight Flow Bridge (8006)
     ↓
Insight Flow Backend (8007)
  - Q-Learning Engine
  - Karma Weighting (→ 8000)
  - Supabase Database
     ↓
Route Decision
     ↓
BHIV Core (8002)
     ↓
Normal Flow → Bucket → Karma
```

---

## ✅ Verification Checklist

- [ ] Supabase SQL script executed
- [ ] `.env` file created in `backend/` directory
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Backend starts on port 8007
- [ ] Bridge starts on port 8006
- [ ] Health checks pass
- [ ] Routing test successful

---

## 📚 Next Steps

1. **Start all services** in order:
   - Karma (8000)
   - Bucket (8001)
   - Core (8002)
   - Insight Flow Backend (8007)
   - Insight Flow Bridge (8006)

2. **Test integration**:
   ```bash
   python test_insight_flow_integration.py
   ```

3. **Access dashboard** (optional):
   ```bash
   cd frontend
   npm install
   npm run dev
   # Access: http://localhost:3000
   ```

---

## 🎯 Quick Commands

```bash
# Start everything
cd "Insight_Flow-main"
start_insight_flow.bat  # Terminal 1
python insight_flow_bridge.py  # Terminal 2

# Test
curl http://localhost:8007/health
curl http://localhost:8006/health
```

---

**Setup Complete!** 🎉

Your Insight Flow is now configured and ready to integrate with BHIV Core.
