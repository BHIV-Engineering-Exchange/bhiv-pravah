# Incident Recovery Guide

## Overview

This guide covers incident response and recovery for the ARTHA BHIV ecosystem participant.

## Incident Classification

### Severity 1 (Critical)
- System completely unavailable
- Data integrity compromised
- Security breach detected

### Severity 2 (High)
- Major feature unavailable
- Performance severely degraded
- Circuit breaker open

### Severity 3 (Medium)
- Minor feature unavailable
- Performance degraded
- Non-critical error

### Severity 4 (Low)
- Cosmetic issue
- Minor inconvenience

## Incident Response Procedures

### Step 1: Detection

**Automatic Detection:**
- Health check failures
- Circuit breaker open events
- Contract integrity violations
- Authority boundary violations

**Manual Detection:**
- User reports
- Monitoring alerts
- Log analysis

### Step 2: Triage

```bash
# Check system health
curl http://localhost:5000/health/detailed

# Check governance status
curl http://localhost:5000/api/v1/governance/status \
  -H "Authorization: Bearer <token>"

# Check circuit breakers
curl http://localhost:5000/api/v1/governance/circuit-breakers \
  -H "Authorization: Bearer <token>"

# Check recent logs
tail -100 backend/logs/error.log
```

### Step 3: Containment

**If Security Incident:**
1. Block affected IP addresses
2. Revoke compromised tokens
3. Enable enhanced logging
4. Notify security team

**If Data Integrity Incident:**
1. Stop writes to affected collections
2. Create emergency backup
3. Assess damage extent
4. Notify data team

**If Availability Incident:**
1. Check circuit breakers
2. Check dependency health
3. Check resource usage
4. Notify operations team

### Step 4: Recovery

#### Recovery Procedure 1: Circuit Breaker Open

```bash
# Check which circuit breaker is open
curl http://localhost:5000/api/v1/governance/circuit-breakers \
  -H "Authorization: Bearer <token>"

# Check dependency health
# MongoDB: mongosh --eval "db.adminCommand('ping')"
# Redis: redis-cli ping

# Fix dependency issue
# Wait for recovery window or force reset

# Force reset circuit breaker
curl -X POST http://localhost:5000/api/v1/governance/circuit-breakers/mongodb/reset \
  -H "Authorization: Bearer <token>"

# Verify recovery
curl http://localhost:5000/health/detailed
```

#### Recovery Procedure 2: Contract Integrity Violation

```bash
# Verify which contracts are tampered
curl http://localhost:5000/api/v1/governance/capabilities/verify \
  -H "Authorization: Bearer <token>"

# Restore original contracts
git checkout contracts/capability_contracts/

# Restart application
docker-compose -f docker-compose.prod.yml restart

# Verify integrity
curl http://localhost:5000/api/v1/governance/capabilities/verify \
  -H "Authorization: Bearer <token>"
```

#### Recovery Procedure 3: Database Corruption

```bash
# Stop application
docker-compose -f docker-compose.prod.yml down

# Restore from backup
mongorestore --uri="mongodb://localhost:27017/artha" --archive=<backup-file>

# Start application
docker-compose -f docker-compose.prod.yml up -d

# Verify data integrity
curl http://localhost:5000/api/v1/ledger/verify-chain \
  -H "Authorization: Bearer <token>"
```

#### Recovery Procedure 4: Provenance Chain Corruption

```bash
# Check provenance integrity
curl http://localhost:5000/api/v1/governance/provenance/verify \
  -H "Authorization: Bearer <token>"

# If invalid, restart application (chain reinitializes)
docker-compose -f docker-compose.prod.yml restart

# Record recovery event
curl -X POST http://localhost:5000/api/v1/governance/provenance/record \
  -H "Authorization: Bearer <token>" \
  -d '{"type": "RECOVERY", "details": "Provenance chain reinitialized"}'
```

### Step 5: Post-Incident

1. **Document the incident:**
   - Timeline
   - Root cause
   - Impact
   - Resolution steps

2. **Review and improve:**
   - Update runbooks
   - Add monitoring if missing
   - Improve automation
   - Update documentation

3. **Notify stakeholders:**
   - Internal team
   - External users (if affected)
   - Management (if significant)

## Common Incidents and Resolutions

### Incident: MongoDB Connection Lost

**Symptoms:**
- 503 errors
- Circuit breaker for mongodb opens
- Application logs show connection errors

**Resolution:**
1. Check MongoDB server status
2. Check network connectivity
3. Restart MongoDB if needed
4. Wait for circuit breaker recovery
5. Verify application reconnects

### Incident: Redis Connection Lost

**Symptoms:**
- Cache misses
- Slower response times
- Circuit breaker for redis opens

**Resolution:**
1. Check Redis server status
2. Check network connectivity
3. Restart Redis if needed
4. Wait for circuit breaker recovery
5. Verify caching resumes

### Incident: SETU API Unavailable

**Symptoms:**
- Signal dispatch failures
- Circuit breaker for setu_api opens
- Compliance filings delayed

**Resolution:**
1. Check SETU API status
2. Check API credentials
3. Wait for SETU recovery
4. Force reset circuit breaker if needed
5. Retry failed dispatches

### Incident: Authority Boundary Violation

**Symptoms:**
- 403 errors for valid requests
- Policy engine denials
- Audit log shows violations

**Resolution:**
1. Check capability contracts
2. Check route mappings
3. Check user roles
4. Review policy engine logs
5. Update contracts if needed

### Incident: Hash Chain Break

**Symptoms:**
- Ledger verification fails
- Chain integrity check fails
- Audit trail shows gaps

**Resolution:**
1. Identify break point
2. Assess data integrity
3. Restore from backup if needed
4. Rebuild chain if possible
5. Document and investigate

## Emergency Contacts

- **Operations Team:** ops@artha.bhiv.in
- **Security Team:** security@artha.bhiv.in
- **Development Team:** dev@artha.bhiv.in
- **Management:** management@artha.bhiv.in

## Communication Templates

### Internal Notification

```
Subject: [ARTHA Incident] Severity X - Brief Description

Incident: Brief description
Severity: X
Impact: What's affected
Status: Investigating/Contained/Resolved
ETA: Estimated time to resolution

Actions taken:
1. ...
2. ...

Next steps:
1. ...
2. ...

Contact: [Your Name]
```

### External Notification

```
Subject: [ARTHA Service Update] Brief Description

We're currently experiencing issues with [feature].

Impact: What's affected
Status: We're working to resolve this
ETA: Expected resolution time

We apologize for the inconvenience.

ARTHA Team
```

## Post-Incident Review

### Review Checklist

- [ ] Timeline documented
- [ ] Root cause identified
- [ ] Impact assessed
- [ ] Resolution steps documented
- [ ] Monitoring improvements identified
- [ ] Process improvements identified
- [ ] Documentation updated
- [ ] Team notified

### Review Meeting Agenda

1. Incident overview
2. Timeline walkthrough
3. Root cause analysis
4. Impact assessment
5. Resolution review
6. Improvement actions
7. Follow-up assignments
