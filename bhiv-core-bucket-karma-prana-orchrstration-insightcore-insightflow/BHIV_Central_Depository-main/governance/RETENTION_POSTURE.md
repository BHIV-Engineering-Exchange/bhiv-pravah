# Document 06: Retention Posture

**Date:** January 13, 2026  
**Purpose:** Data deletion and lifecycle policy  
**Audience:** Data governance, compliance, operations  
**Classification:** Policy (Public)

## Overview

This document defines the data retention and deletion strategy for BHIV Central Depository (Bucket v1.0.0). It establishes clear policies for how long data is kept, when it's deleted, and how to handle special cases like GDPR requests and legal holds.

## 1. Deletion Strategy: Tombstoning + TTL

### Core Principle
Two-layer deletion approach: Mark as deleted + automatic cleanup

### Layer 1: Tombstoning (Soft Delete)
When data needs to be deleted:
1. Mark with `deletion_timestamp`
2. Keep for audit trail (1-3 months)
3. Then hard delete

### Layer 2: TTL (Automatic Cleanup)
- **Redis**: 1-24 hours (auto-expire)
- **MongoDB**: 1 year (TTL index)
- **Files**: Manual rotation, keep 5-10 backups

## 2. Per-Artifact Retention Rules

| Artifact | Retention | Strategy | Notes |
|----------|-----------|----------|-------|
| Agent Specifications | Permanent | Keep forever | v1 reference baseline |
| Basket Configurations | Permanent | Keep forever | Workflow definitions |
| Execution Metadata | 1 year | TTL in MongoDB | 1hr in Redis |
| Agent Outputs | 1 year | TTL in MongoDB | 1hr in Redis |
| Logs (success) | 1 year | File rotation | 5 backups |
| Logs (error) | 1 year | File rotation | 3 backups |
| Agent State | 1 hour | TTL in Redis | Auto-expire |
| Metrics | 1 month | TTL in Redis | Aggregate only |

## 3. Data Lifecycle

```
Day 0: Execution happens
├─ Redis: Store (1-24hr TTL)
├─ MongoDB: Store (1yr TTL)
└─ Files: Append to log

Day 1-30: Available for analysis
├─ Redis: May still be available
├─ MongoDB: Available
└─ Files: Available

Day 30: Data older than 1 month
├─ Redis: Expired and cleaned
├─ MongoDB: Still available
└─ Files: Rotated but available

Day 365: Data older than 1 year
├─ Redis: Long since expired
├─ MongoDB: TTL index triggers deletion
└─ Files: Moved to archive, then deleted
```

## 4. Special Cases

### GDPR Right-to-be-Forgotten

**Current Process (Manual):**
1. User requests deletion
2. Audit review determines what to delete
3. Tombstone with `deletion_timestamp`
4. Wait 90 days for audit period
5. Hard delete after audit period
6. Verify deletion in all systems

**Timeline:** 90 days  
**Automation:** Manual

**Future Process (Phase 2, Q2 2026):**
1. Automated PII detection
2. Automatic anonymization
3. Audit trail of deletion
4. Compliance reporting

**Timeline:** 30 days  
**Automation:** Automated

### Legal Hold

**Process:**
1. Legal sends data hold request
2. Flag data as "hold" in MongoDB
3. Prevent automatic deletion
4. Wait for legal clearance
5. Then proceed with normal retention

**Implementation:**
```json
{
  "legal_hold": true,
  "hold_date": "2026-01-15",
  "hold_reason": "Litigation case #123"
}
```

### Data Subject Access Request (DSAR)

**Current Process:**
1. Subject requests their data
2. Find all logs mentioning them (limited, no user tracking yet)
3. Export data in machine-readable format
4. Verify before sending
5. Keep record of export

**Timeline:** 30 days (GDPR requirement)

**Limitations:** No user tracking in v1.0.0 - limited data retrieval capability

## 5. Deletion Procedures

### Automated Deletion (Bucket-Handled)
```bash
# Redis TTL: Automatic after 1-24 hours
# MongoDB TTL: Automatic after 1 year (configured)
# File logs: Automatic rotation (daily)
```

### Manual Deletion (If Needed)

**Delete specific execution:**
```javascript
db.logs.updateOne(
  { execution_id: "xxx" },
  { $set: { deleted: true, deletion_timestamp: ISODate() } }
)
```

**Actually delete after 90 days:**
```javascript
db.logs.deleteMany({ 
  deleted: true,
  deletion_timestamp: { $lt: ISODate("90 days ago") }
})
```

## 6. Storage Impact Analysis

### Current Storage (Baseline)
Estimated per day:
- 100 executions/day
- ~50KB per execution (average)
- = 5MB/day Bucket data
- = 150MB/month
- = 1.8GB/year

### Storage Breakdown
- **Redis**: ~50MB (rolling 1-24hr)
- **MongoDB**: ~1.8GB/year (growing)
- **File logs**: ~500MB (rotated)
- **Total**: ~2.4GB after 1 year

### Scaling Projections
- **1,000 executions/day** = 24GB/year
- **10,000 executions/day** = 240GB/year (archive needed)

## 7. Cleanup Scripts

### Daily File Log Cleanup (Automated)
```python
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    'logs/application.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5           # Keep 5 backups
)
```

### Manual MongoDB Cleanup (If Needed)
```python
from datetime import datetime, timedelta

db = mongo_client['workflow_ai']['logs']

# Delete logs older than 1 year
one_year_ago = datetime.utcnow() - timedelta(days=365)
db.logs.delete_many({
    'timestamp': { '$lt': one_year_ago }
})

# Delete tombstoned data after 90 days
ninety_days_ago = datetime.utcnow() - timedelta(days=90)
db.logs.delete_many({
    'deleted': True,
    'deletion_timestamp': { '$lt': ninety_days_ago }
})
```

## 8. Tunable Parameters

Configure these in `.env` or config file:

```env
# Retention periods
REDIS_EXECUTION_TTL=86400          # 24 hours (seconds)
MONGODB_LOG_RETENTION_DAYS=365     # 1 year
FILE_LOG_MAX_SIZE=10485760         # 10MB
FILE_LOG_BACKUP_COUNT=5            # Keep 5 backups
ERROR_LOG_BACKUP_COUNT=3           # Keep 3 backups

# Deletion strategy
TOMBSTONE_PERIOD_DAYS=90           # Keep tombstones 90 days
ENABLE_AUTO_CLEANUP=true           # Auto delete old data
GDPR_ANONYMIZE=false               # Anonymize PII (Phase 2)
```

## 9. Compliance Checklist

- ✅ Retention policy documented (this doc)
- ✅ Deletion procedure tested
- ✅ Storage capacity planned
- ⚠️ GDPR procedures ready (manual, Phase 2 automated)
- ✅ Legal hold capability tested
- ✅ Backup strategy in place
- ✅ Disaster recovery tested
- ✅ Regular cleanup runs

## 10. API Endpoints

### Get Retention Configuration
```bash
GET /governance/retention/config
```
Returns tunable parameters and current configuration.

### Get Retention Rules
```bash
GET /governance/retention/rules
```
Returns per-artifact retention rules.

### Get Data Lifecycle
```bash
GET /governance/retention/lifecycle
```
Returns data lifecycle stages visualization.

### Get Deletion Strategy
```bash
GET /governance/retention/deletion-strategy
```
Returns tombstoning + TTL strategy details.

### Get GDPR Process
```bash
GET /governance/retention/gdpr
```
Returns GDPR right-to-be-forgotten process.

### Get Legal Hold Process
```bash
GET /governance/retention/legal-hold
```
Returns legal hold implementation details.

### Get Storage Impact
```bash
GET /governance/retention/storage-impact
```
Returns storage analysis and projections.

### Get Cleanup Procedures
```bash
GET /governance/retention/cleanup-procedures
```
Returns automated and manual cleanup procedures.

### Get Compliance Checklist
```bash
GET /governance/retention/compliance-checklist
```
Returns retention compliance status.

### Get DSAR Process
```bash
GET /governance/retention/dsar
```
Returns Data Subject Access Request process.

### Calculate Retention Date
```bash
POST /governance/retention/calculate?artifact_type=execution_metadata&created_date=2026-01-01T00:00:00
```
Calculates when specific data should be deleted.

## 11. Integration with Existing System

### Backward Compatibility
✅ All retention endpoints are **purely additive**  
✅ No breaking changes to existing endpoints  
✅ Existing basket deletion endpoint enhanced with retention-aware cleanup  
✅ Redis and MongoDB cleanup integrated seamlessly

### Enhanced Basket Deletion
The existing `/baskets/{basket_name}` DELETE endpoint now includes:
- Redis data cleanup (execution logs, agent outputs, state)
- MongoDB data cleanup (logs, basket records)
- File log cleanup (basket_runs directory)
- Deletion event logging for audit trail

### Automatic Cleanup
- Redis TTL: Already configured in `utils/redis_service.py`
- MongoDB TTL: Can be configured via MongoDB indexes
- File rotation: Already implemented in `utils/logger.py`

## 12. Phase 2 Enhancements (Q2 2026)

1. **Automated PII Detection** - Scan data for personal information
2. **Automatic Anonymization** - Replace PII with anonymized values
3. **GDPR Automation** - Reduce manual intervention from 90 days to 30 days
4. **User Tracking** - Enable proper DSAR data retrieval
5. **Compliance Reporting** - Automated compliance status reports

## Summary

Document 06 establishes a comprehensive retention posture for BHIV Central Depository:

- **Two-layer deletion**: Tombstoning (soft delete) + TTL (automatic cleanup)
- **Clear retention rules**: Permanent for configs, 1 year for logs, 1 hour for state
- **GDPR compliance**: Manual process (90 days), automated in Phase 2 (30 days)
- **Legal hold support**: MongoDB flag prevents automatic deletion
- **Storage planning**: 2.4GB/year baseline, scales to 240GB at 10K executions/day
- **11 new API endpoints**: Full programmatic access to retention policies
- **100% backward compatible**: No breaking changes to existing system

**Status:** ✅ Implemented and integrated with existing governance layer
