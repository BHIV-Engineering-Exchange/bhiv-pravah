# Primary Bucket Owner Integration

## Overview
This integration connects the Real-Time Micro-Bridge to the Primary Bucket Owner system for centralized artifact management and governance.

## Architecture

```
Real-Time Micro-Bridge → primaryBucketAdapter.js → Primary Bucket Owner (port 8000)
         ↓
   Local Storage (bucket_artifacts/)
```

## Setup

### 1. Update Environment Variables

Add to your `.env` file:

```env
# Enable Primary Bucket integration
USE_PRIMARY_BUCKET=true
PRIMARY_BUCKET_URL=http://localhost:8000
```

### 2. Start Primary Bucket Owner

```bash
cd "d:\Internship Task\Primary_Bucket_Owner-main\Primary_Bucket_Owner-main"
python main.py
```

The Primary Bucket should start on port 8000.

### 3. Start Real-Time Micro-Bridge

```bash
cd "d:\Internship Task\Real-Time Micro-Bridge\backend"
node index.js
```

## How It Works

### Dual-Write Strategy

When `USE_PRIMARY_BUCKET=true`, all execution artifacts are written to:
1. **Local Storage** (bucket_artifacts/) - for immediate access
2. **Primary Bucket** (via HTTP API) - for governance and centralized management

### Artifact Types Sent

All artifacts comply with Primary Bucket's approved artifact classes:

| Artifact Type | Primary Bucket Class | Description |
|--------------|---------------------|-------------|
| Execution Schema | `execution_metadata` | Game mode, physics, movement config |
| Execution Start | `execution_metadata` | Start timestamp, trace ID |
| Execution Completion | `execution_metadata` | Completion timestamp, status, duration |
| Execution Logs | `logs` | Event logs (dispatched, completed, failed) |

### Governance Validation

Primary Bucket validates each artifact against:
- **Artifact admission policy** (approved/rejected classes)
- **Size constraints** (max 10MB for execution_metadata)
- **Schema validation** (structured JSON only)
- **Retention policies** (1 year for execution_metadata)

## Testing

### Test Integration

```bash
cd backend
node tests/test_primary_bucket_integration.js
```

Expected output:
```
✅ Primary Bucket is healthy: healthy
✅ Execution schema sent successfully
✅ Execution start sent successfully
✅ Execution completion sent successfully
```

### Test with Real Execution

```bash
# Run a test execution
node tests/test_core_execute.js
```

Check Primary Bucket logs to verify artifacts were received.

## API Endpoints Used

### Primary Bucket Endpoints

- `POST /governance/validate-artifact-admission` - Validate and store artifacts
- `GET /governance/artifact-policy` - Get artifact admission policy
- `GET /health` - Health check

## Error Handling

- **Primary Bucket unavailable**: Artifacts are still written to local storage
- **Validation failure**: Logged but doesn't block local storage
- **Network errors**: Caught and logged, execution continues

## Monitoring

Check logs for Primary Bucket sync status:

```bash
# Real-Time Micro-Bridge logs
tail -f backend/logs/application.log | grep PRIMARY_BUCKET

# Primary Bucket logs
# Check Primary Bucket console output
```

## Disabling Integration

Set in `.env`:
```env
USE_PRIMARY_BUCKET=false
```

System will only write to local storage.

## Troubleshooting

### Primary Bucket not reachable
```
Error: connect ECONNREFUSED 127.0.0.1:8000
```
**Solution**: Start Primary Bucket Owner on port 8000

### Artifact rejected
```
Execution schema rejected: Not in approved artifact classes
```
**Solution**: Check artifact class matches Primary Bucket's approved list

### Port conflict
```
Error: Port 8000 already in use
```
**Solution**: Change `PRIMARY_BUCKET_URL` in .env or stop conflicting service

## Benefits

1. **Centralized Governance** - All artifacts validated against enterprise policies
2. **Audit Trail** - Complete provenance tracking in Primary Bucket
3. **Compliance** - Automatic retention and deletion policies
4. **Multi-Product** - Share artifacts across multiple systems
5. **Fallback** - Local storage ensures reliability

## Next Steps

- Configure retention policies in Primary Bucket
- Set up artifact queries via Primary Bucket API
- Enable cross-product artifact sharing
- Implement artifact lifecycle management
