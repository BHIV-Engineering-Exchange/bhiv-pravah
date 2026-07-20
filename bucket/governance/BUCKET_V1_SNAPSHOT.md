# 02 — BUCKET V1 SNAPSHOT (Baseline State)

**Date Captured**: January 13, 2026  
**Purpose**: Freeze current state to detect future drift  
**Audience**: All teams, future owners  
**Classification**: Reference (Public)

---

## 1. MONGODB SCHEMA (Current)

### **Collection: logs**

```json
{
  "_id": "ObjectId",
  "agent": "agent_name",
  "message": "Log message",
  "timestamp": "ISODate('2025-01-01T00:00:00Z')",
  "level": "info|warning|error",
  "execution_id": "1234567890_abcd1234 (optional)",
  "basket_name": "basket_name (optional)",
  "duration_ms": 1000,
  "additional_details": {}
}
```

#### **Indexes**
- `agent` (ascending)
- `timestamp` (descending)
- `execution_id` (ascending)
- `level` (ascending)

#### **TTL**: None (permanent storage)

---

## 2. REDIS DATA STRUCTURES (Current)

### **Execution Logs**
```
Key: execution:{execution_id}:logs
Type: List<Dict>
TTL: 24 hours
Structure: [{agent, step, data, status, timestamp}]
```

### **Agent Outputs**
```
Key: execution:{execution_id}:outputs:{agent_name}
Type: Dict
TTL: 1 hour
Structure: {result, status, timestamp}
```

### **Agent State**
```
Key: agent:{agent_name}:state:{execution_id}
Type: Dict
TTL: 1 hour
Structure: {key-value state data}
```

### **Basket Execution**
```
Key: basket:{basket_name}:execution:{execution_id}
Type: Dict
TTL: 24 hours
Structure: {status, agents_completed, result, errors}
```

### **Basket Executions List**
```
Key: basket:{basket_name}:executions
Type: List<str>
TTL: None (rolling list of last 100)
```

---

## 3. API ENDPOINTS (Current)

### **Core Endpoints**
- `GET /health` - System health check
- `GET /agents` - List all agents
- `GET /baskets` - List all baskets
- `POST /run-agent` - Execute single agent
- `POST /run-basket` - Execute basket workflow
- `POST /create-basket` - Create new basket
- `DELETE /baskets/{basket_name}` - Delete basket

### **Governance Endpoints** (v1.0.0)
- `GET /governance/info` - Get governance metadata
- `GET /governance/snapshot` - Get schema snapshot
- `POST /governance/validate-artifact` - Validate artifact class
- `POST /governance/validate-schema` - Validate MongoDB document

### **Monitoring Endpoints**
- `GET /logs` - Get logs
- `GET /redis/status` - Redis status
- `GET /execution-logs/{execution_id}` - Execution logs
- `GET /agent-logs/{agent_name}` - Agent logs
- `POST /redis/cleanup` - Cleanup old data

### **Law Agent Endpoints**
- `POST /basic-query` - Basic legal query
- `POST /adaptive-query` - Adaptive legal query
- `POST /enhanced-query` - Enhanced legal query

---

## 4. AGENT INVENTORY (Current)

### **Finance Domain** (3 agents)
- `cashflow_analyzer` - Transaction analysis
- `goal_recommender` - Financial recommendations
- `financial_coordinator` - Financial operations

### **Automotive Domain** (3 agents)
- `auto_diagnostics` - Vehicle diagnostics
- `vehicle_maintenance` - Maintenance scheduling
- `fuel_efficiency` - Fuel optimization

### **Education Domain** (5 agents)
- `vedic_quiz_agent` - Interactive quizzes
- `sanskrit_parser` - Sanskrit text analysis
- `gurukul_anomaly` - Anomaly detection
- `gurukul_feedback` - Feedback processing
- `gurukul_trend` - Trend analysis

### **Other Domains** (3 agents)
- `workflow_agent` - Business workflow optimization
- `law_agent` - Legal query processing
- `textToJson` - Text to JSON conversion

**Total Agents**: 14

---

## 5. BASKET INVENTORY (Current)

### **Active Baskets**
- `finance_daily_check` - Financial analysis workflow
- `working_test` - Cashflow analyzer test
- `goal_test` - Goal recommender test
- `coordinator_test` - Financial coordinator test
- `chained_test` - Multi-agent chain test
- `multi_agent_test` - Multi-agent workflow
- `law_agent_test` - Law agent test
- `text_to_json_test` - Text conversion test

**Total Baskets**: 8+

---

## 6. FILE SYSTEM STRUCTURE (Current)

### **Log Files**
```
logs/
├── application.log (10MB max, 5 backups)
├── errors.log (5MB max, 3 backups)
├── executions.log (10MB max, 5 backups)
└── basket_runs/
    └── {basket_name}_{execution_id}.log
```

### **Configuration Files**
```
├── .env (environment variables)
├── agents_and_baskets.yaml (agent/basket config)
├── requirements.txt (Python dependencies)
└── admin-panel/package.json (Frontend dependencies)
```

---

## 7. DRIFT DETECTION

### **How to Detect Drift**

Use the snapshot API to compare current state:

```bash
# Get current snapshot
curl http://localhost:8000/governance/snapshot

# Compare with baseline (this document)
# Any differences indicate drift
```

### **What Constitutes Drift**

✅ **Acceptable Changes** (No drift):
- New agents added
- New baskets created
- Log entries added
- Execution data added

❌ **Breaking Changes** (Drift detected):
- MongoDB schema fields removed
- Redis key patterns changed
- Required fields modified
- TTL policies changed
- Index definitions altered

### **Drift Response Protocol**

1. **Detect**: Compare current state with snapshot
2. **Document**: Record what changed and why
3. **Escalate**: Notify Ashmit (Primary Owner)
4. **Decide**: Approve as v1.1 or reject as breaking
5. **Version**: If approved, update to v1.1 or v2.0

---

## 8. SCHEMA VALIDATION

### **Validate MongoDB Document**

```bash
curl -X POST "http://localhost:8000/governance/validate-schema?collection=logs" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "test_agent",
    "message": "Test message",
    "timestamp": "2026-01-13T00:00:00Z",
    "level": "info"
  }'
```

### **Validate Redis Key**

```python
from governance.snapshot import validate_redis_key

result = validate_redis_key("execution:12345_abcd:logs")
# Returns: {"valid": True, "structure": "execution_logs", "ttl_hours": 24}
```

---

## 9. SNAPSHOT METADATA

```json
{
  "snapshot_date": "2026-01-13",
  "snapshot_version": "1.0.0",
  "mongodb_collections": ["logs"],
  "redis_structures": [
    "execution_logs",
    "agent_outputs",
    "agent_state",
    "basket_execution",
    "basket_executions_list"
  ],
  "total_agents": 14,
  "total_baskets": 8,
  "api_endpoints": 20
}
```

---

## 10. BACKWARD COMPATIBILITY GUARANTEE

This snapshot represents **Bucket v1.0.0** baseline.

### **Compatibility Promise**

All systems integrating with Bucket v1 can rely on:
- ✅ MongoDB `logs` collection schema unchanged
- ✅ Redis key patterns unchanged
- ✅ API endpoints unchanged (new ones may be added)
- ✅ Agent input/output schemas unchanged
- ✅ Basket execution flow unchanged

### **Breaking Changes Require**

- Version bump to v2.0
- Migration path documented
- 30-day notice to consumers
- Owner approval (Ashmit)

---

## 11. TESTING SNAPSHOT ENDPOINTS

### **Get Snapshot Info**
```bash
curl http://localhost:8000/governance/snapshot
```

**Expected Response**:
```json
{
  "snapshot_date": "2026-01-13",
  "snapshot_version": "1.0.0",
  "mongodb_collections": ["logs"],
  "redis_structures": [
    "execution_logs",
    "agent_outputs",
    "agent_state",
    "basket_execution",
    "basket_executions_list"
  ],
  "captured_at": "2026-01-13T12:00:00Z"
}
```

### **Validate Schema**
```bash
curl -X POST "http://localhost:8000/governance/validate-schema?collection=logs" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "cashflow_analyzer",
    "message": "Processing transaction",
    "timestamp": "2026-01-13T12:00:00Z",
    "level": "info",
    "execution_id": "1234567890_abcd1234"
  }'
```

**Expected Response**:
```json
{
  "valid": true,
  "reason": "Schema validation passed"
}
```

---

## 12. CHANGE LOG

### **v1.0.0** (January 13, 2026)
- Initial snapshot captured
- MongoDB logs collection defined
- Redis structures documented
- 14 agents inventoried
- 8 baskets cataloged
- API endpoints frozen

### **Future Versions**
- v1.0.1 - Bug fixes only
- v1.1.0 - New non-breaking features
- v2.0.0 - Breaking changes (requires migration)

---

## 13. SNAPSHOT INTEGRITY

### **Checksum** (Conceptual)
```
MongoDB Schema: SHA256(logs_schema)
Redis Structures: SHA256(all_key_patterns)
API Endpoints: SHA256(endpoint_list)
```

### **Verification**
To verify snapshot integrity, compare:
1. Current MongoDB schema vs. this document
2. Current Redis keys vs. documented patterns
3. Current API endpoints vs. listed endpoints
4. Current agent count vs. 14
5. Current basket count vs. 8

Any mismatch = drift detected.

---

## 14. OWNER SIGN-OFF

**Snapshot Approved By**: Ashmit (Primary Owner)  
**Date**: January 13, 2026  
**Status**: ✅ Frozen as Bucket v1.0.0 Baseline

**This snapshot is the official reference for Bucket v1. All future changes must be compared against this baseline.**

---

## 15. INTEGRATION CHECKLIST

For teams integrating with Bucket v1:

- [ ] Read this snapshot document
- [ ] Understand MongoDB schema
- [ ] Understand Redis key patterns
- [ ] Test against validation endpoints
- [ ] Document your integration assumptions
- [ ] Subscribe to drift notifications
- [ ] Plan for v2.0 migration (future)

---

**End of Snapshot Document**
