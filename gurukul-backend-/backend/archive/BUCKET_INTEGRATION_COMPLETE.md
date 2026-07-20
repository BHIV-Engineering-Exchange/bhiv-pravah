# ✅ Bucket Integration Complete

## Overview

The bucket functionality has been successfully integrated into your existing backend! This allows PRANA packets to be stored and queued for Karma Tracker processing.

---

## What Was Added

### 1. **Database Model** ✅
- **File**: `backend/app/models/prana_models.py`
- **Model**: `PranaPacket`
- **Purpose**: Stores PRANA packets in your database (PostgreSQL/SQLite)

### 2. **Redis Queue Support** ✅
- **File**: `backend/app/core/redis_client.py`
- **Class**: `RedisQueue`
- **Purpose**: Queues packets for Karma Tracker consumption
- **Fallback**: Uses in-memory queue if Redis is not available

### 3. **Enhanced Bucket Router** ✅
- **File**: `backend/app/routers/bucket.py`
- **Endpoints Added**:
  - `POST /api/v1/bucket/prana/ingest` - Receive packets from PRANA
  - `GET /api/v1/bucket/prana/packets/pending` - Get pending packets (for Karma Tracker)
  - `POST /api/v1/bucket/prana/packets/mark-processed` - Mark packet as processed
  - `GET /api/v1/bucket/prana/packets/user/{user_id}` - Get user's packets
  - `GET /api/v1/bucket/prana/status` - Get bucket status

### 4. **Dependencies** ✅
- Added `redis>=5.0.0` to `requirements.txt`
- Redis is optional - system works without it (uses in-memory fallback)

---

## How It Works

### Packet Flow:

```
1. PRANA Frontend → POST /api/v1/bucket/prana/ingest
   ↓
2. Backend validates and stores in database
   ↓
3. Backend queues packet in Redis (or in-memory)
   ↓
4. Karma Tracker polls: GET /api/v1/bucket/prana/packets/pending
   ↓
5. Karma Tracker processes packet and updates karma
   ↓
6. Karma Tracker marks as processed: POST /api/v1/bucket/prana/packets/mark-processed
```

---

## Configuration

### Environment Variables (Optional)

Add these to your `.env` file if you want to use Redis:

```env
# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password_here
REDIS_USERNAME=your_username_here
```

**Note**: Redis is optional! The system will work with an in-memory queue if Redis is not configured.

---

## API Endpoints

### 1. Ingest Packet (PRANA → Backend)

**Endpoint**: `POST /api/v1/bucket/prana/ingest`

**Request Body**:
```json
{
  "user_id": "user_123",
  "session_id": "session_456",
  "lesson_id": "lesson_789",
  "system_type": "gurukul",
  "role": "student",
  "timestamp": "2024-01-20T10:30:00Z",
  "cognitive_state": "ON_TASK",
  "active_seconds": 4.5,
  "idle_seconds": 0.3,
  "away_seconds": 0.2,
  "focus_score": 85.0,
  "raw_signals": {
    "dwell_time_ms": 1200,
    "mouse_velocity": 0.5
  }
}
```

**Response**:
```json
{
  "status": "ingested",
  "packet_id": "uuid-here",
  "received_at": "2024-01-20T10:30:05Z"
}
```

### 2. Get Pending Packets (Karma Tracker → Backend)

**Endpoint**: `GET /api/v1/bucket/prana/packets/pending?limit=10`

**Response**:
```json
{
  "packets": [
    {
      "packet_id": "uuid-here",
      "user_id": "user_123",
      "cognitive_state": "ON_TASK",
      "focus_score": 85.0,
      "active_seconds": 4.5,
      "idle_seconds": 0.3,
      "away_seconds": 0.2,
      "raw_signals": {...},
      "client_timestamp": "2024-01-20T10:30:00Z",
      "received_at": "2024-01-20T10:30:05Z"
    }
  ],
  "count": 1,
  "queue_size": 5
}
```

### 3. Mark Packet as Processed (Karma Tracker → Backend)

**Endpoint**: `POST /api/v1/bucket/prana/packets/mark-processed`

**Request Body**:
```json
{
  "packet_id": "uuid-here",
  "success": true,
  "karma_actions": [
    {
      "action": "completing_lessons",
      "reward": 5,
      "token": "DharmaPoints"
    }
  ]
}
```

### 4. Get Bucket Status

**Endpoint**: `GET /api/v1/bucket/prana/status`

**Response**:
```json
{
  "queue_size": 5,
  "redis_connected": true,
  "model_available": true,
  "total_packets": 1000,
  "processed_packets": 995,
  "pending_packets": 5
}
```

---

## Database Schema

The `prana_packets` table includes:

- `packet_id` (Primary Key)
- `user_id`, `employee_id` (User identification)
- `session_id`, `lesson_id` (Context)
- `system_type`, `role` (System context)
- `cognitive_state`, `state` (User state)
- `active_seconds`, `idle_seconds`, `away_seconds` (Time accounting)
- `focus_score`, `integrity_score` (Scores)
- `raw_signals` (JSON - all raw signals)
- `processed_by_karma` (Boolean - processing status)
- `karma_actions` (JSON - actions generated)
- `client_timestamp`, `received_at`, `processed_at` (Timestamps)

---

## Next Steps

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Database Migration

The model will be created automatically when you start the backend (SQLAlchemy auto-creates tables).

Or manually:
```bash
python -c "from app.core.database import engine, Base; from app.models.prana_models import PranaPacket; Base.metadata.create_all(bind=engine)"
```

### 3. (Optional) Set Up Redis

If you want Redis queuing:

```bash
# Using Docker
docker run -d --name redis -p 6379:6379 redis:alpine

# Or install locally
# Windows: choco install redis-64
# Mac: brew install redis
# Linux: apt-get install redis-server
```

### 4. Update PRANA Bucket Bridge

The PRANA `bucket_bridge.js` should already point to:
```javascript
const defaultEndpoint = 'http://localhost:3000/api/v1/bucket/prana/ingest';
```

**For production**, update to your backend URL:
```javascript
const defaultEndpoint = 'https://your-backend.onrender.com/api/v1/bucket/prana/ingest';
```

### 5. Create Karma Tracker Consumer

Create a service in Karma Tracker that:
1. Polls `/api/v1/bucket/prana/packets/pending` every few seconds
2. Processes each packet
3. Calls Karma Tracker API to update karma
4. Marks packet as processed

Example consumer code:
```python
# Karma Tracker/utils/bucket_consumer.py
import requests
import time

BUCKET_URL = "http://localhost:3000/api/v1"

def poll_and_process():
    while True:
        # Get pending packets
        response = requests.get(f"{BUCKET_URL}/bucket/prana/packets/pending?limit=10")
        packets = response.json()["packets"]
        
        for packet in packets:
            # Process packet and update karma
            karma_action = determine_karma_action(packet)
            
            # Call Karma Tracker API
            requests.post(f"{KARMA_TRACKER_URL}/api/v1/karma/log-action/", json={
                "user_id": packet["user_id"],
                "action": karma_action,
                "intensity": 1.0
            })
            
            # Mark as processed
            requests.post(f"{BUCKET_URL}/bucket/prana/packets/mark-processed", json={
                "packet_id": packet["packet_id"],
                "success": True,
                "karma_actions": [karma_action]
            })
        
        time.sleep(5)  # Poll every 5 seconds
```

---

## Testing

### Test Packet Ingestion

```bash
curl -X POST http://localhost:3000/api/v1/bucket/prana/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "timestamp": "2024-01-20T10:30:00Z",
    "cognitive_state": "ON_TASK",
    "active_seconds": 4.5,
    "idle_seconds": 0.3,
    "away_seconds": 0.2,
    "focus_score": 85.0,
    "raw_signals": {}
  }'
```

### Test Get Pending Packets

```bash
curl http://localhost:3000/api/v1/bucket/prana/packets/pending?limit=10
```

### Test Status

```bash
curl http://localhost:3000/api/v1/bucket/prana/status
```

---

## Troubleshooting

### Redis Connection Failed

**Symptom**: Logs show "Redis connection failed"

**Solution**: 
- Redis is optional - system works without it
- If you want Redis, make sure it's running and configured
- Check `REDIS_HOST` and `REDIS_PORT` in `.env`

### Database Model Not Found

**Symptom**: "PranaPacket model not found"

**Solution**:
- Make sure `app/models/prana_models.py` exists
- Check that `app/models/__init__.py` imports `PranaPacket`
- Restart the backend server

### Packets Not Appearing in Queue

**Solution**:
- Check that packets are being stored in database
- Verify Redis is working (or check in-memory queue)
- Check `/api/v1/bucket/prana/status` endpoint

---

## Status

✅ **Integration Complete!**

- ✅ Database model created
- ✅ Redis queue support added
- ✅ Consumer endpoints created
- ✅ Status tracking implemented
- ✅ Graceful fallback (works without Redis)

**Ready for Karma Tracker integration!**

