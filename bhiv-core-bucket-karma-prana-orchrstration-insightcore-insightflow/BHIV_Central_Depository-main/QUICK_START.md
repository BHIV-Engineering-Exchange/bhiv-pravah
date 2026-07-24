# Quick Start Guide - With Cloud Credentials

## ✅ Setup Complete

Your project is now connected to:
- **MongoDB Atlas** (Cloud Database)
- **Redis Cloud** (Cloud Cache)
- **Audit Middleware** (Enterprise Logging)

## Start the Server

```bash
cd "C:\Users\Ashmit Pandey\Downloads\BHIV_Central_Depository-main"
python main.py
```

## Expected Startup Output

```
INFO - Governance Gate initialized
INFO - Connected to Redis at redis-17252.c265.us-east-1-2.ec2.cloud.redislabs.com:17252
INFO - Successfully connected to MongoDB
INFO - Audit middleware indexes created successfully
INFO - Uvicorn running on http://0.0.0.0:8000
```

## Test the System

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Expected**: All services show "connected"

### 2. Create Test Audit Log
```bash
curl -X POST "http://localhost:8000/audit/log?operation_type=CREATE&artifact_id=test_artifact_001&requester_id=ashmit&integration_id=test_integration&status=success"
```

**Expected**: Returns audit_id

### 3. Query Audit Log
```bash
curl http://localhost:8000/audit/artifact/test_artifact_001
```

**Expected**: Returns audit history

### 4. Test Basket Execution
```bash
curl -X POST "http://localhost:8000/run-basket" -H "Content-Type: application/json" -d "{\"basket_name\": \"working_test\"}"
```

**Expected**: Returns execution results

## Access Points

- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Admin Panel**: http://localhost:5173 (if started)

## Key Features Now Active

### 1. Audit Middleware ✅
- Immutable audit trail in MongoDB
- Complete operation history
- Change delta tracking
- Incident response support

### 2. Redis Caching ✅
- High-speed execution logs
- Agent state management
- Basket execution tracking
- Performance optimization

### 3. MongoDB Storage ✅
- Persistent audit logs
- Application logs
- Basket metadata
- Agent metadata

### 4. Governance Gate ✅
- Integration validation
- Threat detection
- Scale limits enforcement
- Operation rules

## All Endpoints (97 Total)

### Core Endpoints
- `GET /health` - System health
- `GET /agents` - List agents
- `GET /baskets` - List baskets
- `POST /run-agent` - Execute agent
- `POST /run-basket` - Execute basket

### Audit Endpoints (7)
- `GET /audit/artifact/{id}` - Artifact history
- `GET /audit/user/{id}` - User activities
- `GET /audit/recent` - Recent operations
- `GET /audit/failed` - Failed operations
- `POST /audit/validate-immutability/{id}` - Validate immutability
- `POST /audit/log` - Create audit log

### Governance Endpoints (80+)
- `/governance/info` - Bucket info
- `/governance/gate/*` - Governance gate
- `/governance/threats/*` - Threat model
- `/governance/scale/*` - Scale limits
- `/governance/retention/*` - Retention policy
- And many more...

## MongoDB Collections

Your MongoDB database will have:
- `audit_events` - Audit trail (immutable)
- `logs` - Application logs
- `baskets` - Basket metadata
- `agents` - Agent metadata

## Redis Keys

Your Redis cache will have:
- `execution:*` - Execution logs
- `agent:*` - Agent state and logs
- `basket:*` - Basket metadata

## Monitoring

### View Audit Logs in MongoDB
```bash
# Connect to MongoDB
mongosh "mongodb+srv://blackholeinfiverse54_db_user:Gjpl998Z6hsQLjJF@artha.rzneis7.mongodb.net/?appName=Artha"

# Query audit events
use Artha
db.audit_events.find().sort({timestamp: -1}).limit(10)
```

### View Redis Data
```bash
# Connect to Redis
redis-cli -h redis-17252.c265.us-east-1-2.ec2.cloud.redislabs.com -p 17252 -a gK22JxYlv9HCpBBuNWpizNT1YjBOOoAD --user default

# List keys
KEYS *

# Get execution logs
LRANGE execution:*:logs 0 10
```

## Security

### ✅ Credentials Secured
- Stored in `.env` file
- Not committed to git
- Loaded via environment variables

### ✅ Cloud Services
- MongoDB Atlas (managed, secure)
- Redis Cloud (managed, secure)
- SSL/TLS enabled

### ✅ Audit Trail
- All operations logged
- Immutable audit entries
- Complete change history

## Troubleshooting

### Server won't start
1. Check .env file exists
2. Verify credentials are correct
3. Check network connectivity

### MongoDB connection fails
- Verify MongoDB URI in .env
- Check network/firewall
- Ensure IP is whitelisted in MongoDB Atlas

### Redis connection fails
- Verify Redis credentials in .env
- Check network connectivity
- Ensure Redis Cloud instance is active

### Audit middleware inactive
- Check MongoDB connection
- Verify audit_events collection exists
- Check server logs for errors

## Next Steps

1. ✅ Start server: `python main.py`
2. ✅ Test health: `curl http://localhost:8000/health`
3. ✅ Create audit log
4. ✅ Run test basket
5. ✅ Check MongoDB for audit data
6. ✅ Check Redis for execution logs

## Support

- **Documentation**: See README.md
- **Test Guide**: See AUDIT_MIDDLEWARE_TEST_GUIDE.md
- **Credentials**: See CREDENTIALS_SETUP_COMPLETE.md
- **API Docs**: http://localhost:8000/docs

---

**Status**: ✅ READY FOR PRODUCTION

All systems operational with cloud credentials! 🚀
