# Operations Guide

## Overview

This guide covers day-to-day operations for the ARTHA BHIV ecosystem participant.

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:5000/health

# Detailed health
curl http://localhost:5000/health/detailed

# Readiness (Kubernetes)
curl http://localhost:5000/ready

# Liveness (Kubernetes)
curl http://localhost:5000/live
```

### Governance Status

```bash
# Comprehensive governance status
curl http://localhost:5000/api/v1/governance/status \
  -H "Authorization: Bearer <token>"

# Response:
{
  "governance_status": "operational",
  "capabilities": { ... },
  "circuit_breakers": { ... },
  "replay_statistics": { ... },
  "provenance_integrity": { ... },
  "last_verification": { ... }
}
```

### Circuit Breakers

```bash
# Check circuit breaker status
curl http://localhost:5000/api/v1/governance/circuit-breakers \
  -H "Authorization: Bearer <token>"

# Response:
{
  "status": {
    "mongodb": { "state": "CLOSED", "failure_count": 0 },
    "redis": { "state": "CLOSED", "failure_count": 0 },
    "setu_api": { "state": "CLOSED", "failure_count": 0 },
    ...
  },
  "open_circuits": []
}
```

### Runtime Status

```bash
# Full runtime status
curl http://localhost:5000/api/v1/runtime/status \
  -H "Authorization: Bearer <token>"
```

## Routine Operations

### Daily Verification

Run the verification suite daily to ensure system integrity:

```bash
# Run verification suite
curl http://localhost:5000/api/v1/governance/verification/run \
  -H "Authorization: Bearer <token>"

# Check results
# All tests should show status: "PASS"
```

### Weekly Adversarial Testing

Run the adversarial suite weekly to verify security:

```bash
# Run adversarial suite
curl http://localhost:5000/api/v1/governance/adversarial/run \
  -H "Authorization: Bearer <token>"

# Check results
# All attacks should show blocked: true
```

### Monthly Contract Verification

Verify all capability contracts are intact:

```bash
# Verify all contracts
curl http://localhost:5000/api/v1/governance/capabilities/verify \
  -H "Authorization: Bearer <token>"

# Check results
# All contracts should show valid: true
```

## Log Monitoring

### Application Logs

Logs are written to:
- `backend/logs/error.log` — Error logs
- `backend/logs/combined.log` — All logs

### Key Log Patterns

```bash
# Check for errors
grep -i "error" backend/logs/error.log | tail -20

# Check governance decisions
grep "POLICY_ENGINE" backend/logs/combined.log | tail -20

# Check capability violations
grep "AUTHORITY_VIOLATION" backend/logs/combined.log | tail -20

# Check circuit breaker events
grep "CIRCUIT_BREAKER" backend/logs/combined.log | tail -20
```

### Structured Logging

All governance events are logged with structured data:

```json
{
  "timestamp": "2026-07-04T12:00:00.000Z",
  "level": "error",
  "message": "[POLICY_ENGINE] DENY",
  "capability": "ARTHA-LEDGER-001",
  "method": "POST",
  "path": "/api/v1/ledger/entries",
  "user": { "id": "...", "email": "...", "role": "viewer" },
  "decision": "DENY"
}
```

## Performance Monitoring

### Response Times

```bash
# Check performance metrics
curl http://localhost:5000/api/v1/performance/metrics \
  -H "Authorization: Bearer <token>"
```

### Memory Usage

```bash
# Check memory via health endpoint
curl http://localhost:5000/health/detailed
```

### Database Performance

```bash
# Check database stats
curl http://localhost:5000/api/v1/database/stats \
  -H "Authorization: Bearer <token>"
```

## Backup and Recovery

### MongoDB Backup

```bash
# Create backup
mongodump --uri="mongodb://localhost:27017/artha" --out=/backups/artha-$(date +%Y%m%d)

# Automated backup script
./scripts/backup-prod.sh
```

### Redis Backup

```bash
# Redis data is optional (cache only)
# No backup required for Redis
```

### Evidence Backup

```bash
# Backup evidence directory
tar -czf evidence-$(date +%Y%m%d).tar.gz backend/evidence/
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend instances
docker-compose -f docker-compose.prod.yml up -d --scale artha-backend=3

# Load balancer distributes requests across instances
```

### Database Scaling

```bash
# MongoDB replica set for high availability
# See MongoDB documentation for replica set setup
```

## Troubleshooting

### Issue: Capability Not Found

**Symptoms:** 403 error with "Route not mapped to any capability"

**Resolution:**
1. Check contracts exist in `contracts/capability_contracts/`
2. Check `capability_route_map.json` has correct mappings
3. Review server logs for contract loading errors
4. Restart application to reload contracts

### Issue: Policy Engine Blocking Valid Request

**Symptoms:** 403 error with "POLICY_VIOLATION"

**Resolution:**
1. Check capability is not read-only
2. Check collection is not in blocked_mutations
3. Review policy decision logs
4. Verify capability contract is correct

### Issue: Circuit Breaker Open

**Symptoms:** 503 error with "Service temporarily unavailable"

**Resolution:**
1. Check dependency health (MongoDB, Redis, etc.)
2. Wait for recovery window (configurable per breaker)
3. Force reset: `POST /api/v1/governance/circuit-breakers/:name/reset`
4. Review failure logs for root cause

### Issue: Provenance Chain Invalid

**Symptoms:** Provenance verification fails

**Resolution:**
1. Check for data corruption
2. If irreparable, restart application (chain reinitializes)
3. Record recovery event in provenance chain
4. Investigate root cause

### Issue: Contract Hash Mismatch

**Symptoms:** Contract verification fails

**Resolution:**
1. Check if contract files were modified
2. Restore original contract files from git
3. Restart application to reload contracts
4. Verify integrity again

## Maintenance Windows

### Planned Maintenance

1. Notify users of maintenance window
2. Create backup before maintenance
3. Perform maintenance
4. Run verification suite
5. Run adversarial suite
6. Verify all systems operational
7. Notify users maintenance complete

### Emergency Maintenance

1. Assess impact
2. Create emergency backup if possible
3. Perform minimal necessary changes
4. Run verification suite
5. Monitor for issues
6. Notify users of resolution

## Capacity Planning

### Monitoring Metrics

Track these metrics for capacity planning:
- Request rate (requests/second)
- Response time (ms)
- Error rate (%)
- Database connections
- Memory usage
- Disk usage

### Scaling Triggers

Scale when:
- Response time > 500ms consistently
- Error rate > 1%
- Memory usage > 80%
- Disk usage > 70%
- Database connections > 80% of max
