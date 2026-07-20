# 03 — INTEGRATION BOUNDARY

**Date**: January 13, 2026  
**Purpose**: Define clear boundaries between Bucket and consuming systems  
**Audience**: Integration teams, architects  
**Classification**: Policy (Public)

---

## 1. ONE-WAY DATA FLOW (Core Principle)

### **Allowed Direction**
```
External System → Bucket API → MongoDB/Redis/Files
        ↑              ↓
    ALLOWED        ALLOWED
  (Read results) (Store data)
```

### **Forbidden Direction**
```
External System ← Bucket API ← ??? (This is wrong)
    FORBIDDEN      FORBIDDEN
(Bucket doesn't  (This violates
 push to you)    independent operation)
```

### **What This Means**

✅ **YES, you can**:
- Call Bucket API endpoints
- Get results back synchronously
- Store results in your database
- Use data for downstream processing
- Read agent outputs
- Check execution status

❌ **NO, you cannot**:
- Expect Bucket to push data to you
- Have Bucket call your webhooks
- Expect Bucket to trigger your workflows
- Have Bucket update your databases
- Have Bucket notify you of changes (currently)

---

## 2. INTEGRATION REQUIREMENTS (Mandatory)

Every integration must:

### **1. Have Own Input/Output Mapping**
- You map your data to Bucket input format
- You map Bucket output to your format
- No coupling required

### **2. Be Stateless**
- Bucket doesn't know about your system
- Your system doesn't embed Bucket logic
- Clear separation of concerns

### **3. Handle Bucket Latency**
- Agent execution: 0.1-2 seconds
- 2-agent basket: 0.2-5 seconds
- API response: <100ms additional
- Plan accordingly

### **4. Implement Error Handling**
- Bucket may fail
- Network may fail
- Retry logic in your system
- Exponential backoff recommended

### **5. Document Data Usage**
- What Bucket data are you using?
- How are you transforming it?
- What downstream impact?
- For your reference + Ashmit review

---

## 3. BUCKET BOUNDARY DEFINITION

### **What Bucket Accepts (Input)**
✅ Agent specifications (read-only reference)  
✅ Basket configurations (read/create)  
✅ Agent input data (JSON format)  
✅ Execution requests (REST API)  

### **What Bucket Returns (Output)**
✅ Agent execution results (JSON)  
✅ Basket workflow results (JSON)  
✅ Execution metadata (execution_id, timestamps)  
✅ Status codes and error messages  

### **What Bucket Does NOT Accept**
❌ Binary data (use object storage)  
❌ Video files (use video storage)  
❌ Large files (use separate storage)  
❌ Unstructured documents (use doc storage)  
❌ User credentials (use secret management)  

### **What Bucket Does NOT Provide**
❌ Push notifications (you must poll)  
❌ Webhooks (you must poll)  
❌ Real-time streams (you must poll)  
❌ User authentication (manage separately)  
❌ Role-based access control (manage separately)  

---

## 4. DIRECTIONALITY VALIDATION CHECKLIST

### **Before Approving Integration, Verify**

- [ ] Data flows ONE WAY (external → Bucket only)
- [ ] No reverse dependency (Bucket doesn't call external system)
- [ ] No bidirectional coupling
- [ ] External system independent of Bucket availability
- [ ] Error handling in external system (not Bucket's job)
- [ ] Data mapping documented (external team responsibility)
- [ ] Bucket API used read-only (mostly)

---

## 5. INTEGRATION PATTERNS

### **Pattern 1: Synchronous Request-Response** ✅ Recommended
```
Your System → POST /run-basket → Bucket
Your System ← Result (JSON) ← Bucket
```

**Use when**: Immediate results needed, low latency acceptable

### **Pattern 2: Polling for Status** ✅ Acceptable
```
Your System → POST /run-basket → Bucket (get execution_id)
Your System → GET /execution-logs/{id} → Bucket (poll)
Your System ← Result when ready ← Bucket
```

**Use when**: Long-running operations, async processing

### **Pattern 3: Webhook Push** ❌ Not Supported
```
Your System ← Webhook callback ← Bucket (NOT AVAILABLE)
```

**Status**: Not implemented in v1.0.0

---

## 6. ERROR HANDLING REQUIREMENTS

### **Your System Must Handle**

1. **Network Errors**
   - Connection timeout
   - DNS resolution failure
   - Network unreachable

2. **HTTP Errors**
   - 400 Bad Request (invalid input)
   - 404 Not Found (agent/basket not found)
   - 500 Internal Server Error (Bucket failure)
   - 503 Service Unavailable (Redis/MongoDB down)

3. **Timeout Errors**
   - Set reasonable timeout (30s recommended)
   - Implement retry with exponential backoff
   - Max 3 retries recommended

4. **Data Validation Errors**
   - Validate input before sending
   - Handle schema validation failures
   - Log errors for debugging

---

## 7. PERFORMANCE EXPECTATIONS

### **Latency Targets**
- API response time: <100ms (excluding agent execution)
- Single agent execution: 0.1-2 seconds
- 2-agent basket: 0.2-5 seconds
- Financial coordinator: 1-30 seconds (external API dependent)

### **Throughput Limits**
- Current: Single instance, sequential processing
- Concurrent requests: Limited by server capacity
- Rate limiting: Not implemented (v1.0.0)

### **Scaling Considerations**
- Horizontal scaling: Not yet supported
- Load balancing: Not yet implemented
- Caching: Redis-based (1hr TTL for outputs)

---

## 8. DATA OWNERSHIP

### **Bucket Owns**
- Agent specifications
- Basket configurations
- Execution logs (24hr in Redis, permanent in MongoDB)
- Agent outputs (1hr in Redis)
- System metadata

### **You Own**
- Your input data
- Your output data (after retrieval)
- Your business logic
- Your data transformations
- Your downstream systems

### **Shared Responsibility**
- Data format compatibility
- Schema evolution coordination
- Breaking change communication
- Migration planning

---

## 9. INTEGRATION APPROVAL PROCESS

### **Step 1: Submit Integration Request**
- Document your use case
- Describe data flow
- Identify agents/baskets needed
- Estimate volume/frequency

### **Step 2: Ashmit Reviews**
- Validates one-way flow
- Checks artifact class compliance
- Verifies no reverse dependencies
- Approves or requests changes

### **Step 3: Implementation**
- Akanksha provides technical guidance
- You implement integration
- You test thoroughly
- You document your integration

### **Step 4: Production Approval**
- Final review by Ashmit
- Performance validation
- Error handling verification
- Go-live approval

---

## 10. KNOWN LIMITATIONS (v1.0.0)

### **Current Limitations**
❌ No webhooks/push notifications  
❌ No authentication/authorization  
❌ No rate limiting  
❌ No distributed tracing  
❌ No multi-tenancy  
❌ No data encryption at rest  
❌ No audit trail for reads  

### **Workarounds**
- Polling for async operations
- External auth layer (API gateway)
- Client-side rate limiting
- External monitoring tools
- Single-tenant deployment
- Encryption in transit (HTTPS)
- Application-level logging

---

## 11. FUTURE ENHANCEMENTS (Roadmap)

### **Planned for v1.1**
- Webhook support (opt-in)
- Basic authentication
- Rate limiting

### **Planned for v2.0**
- OAuth2 integration
- Role-based access control
- Multi-tenancy support
- Distributed tracing
- Data encryption at rest

---

## 12. INTEGRATION EXAMPLES

### **Example 1: Simple Agent Call**
```bash
curl -X POST "http://localhost:8000/run-basket" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "working_test",
    "input_data": {
      "transactions": [
        {"id": 1, "amount": 1000, "description": "Income"}
      ]
    }
  }'
```

### **Example 2: Error Handling**
```python
import requests
import time

def call_bucket_with_retry(basket_name, input_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/run-basket",
                json={"basket_name": basket_name, "input_data": input_data},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

### **Example 3: Polling Pattern**
```python
import requests
import time

def execute_and_poll(basket_name, input_data):
    # Start execution
    response = requests.post(
        "http://localhost:8000/run-basket",
        json={"basket_name": basket_name, "input_data": input_data}
    )
    result = response.json()
    execution_id = result.get("execution_metadata", {}).get("execution_id")
    
    # Poll for completion (if needed for long-running operations)
    while True:
        logs = requests.get(f"http://localhost:8000/execution-logs/{execution_id}")
        # Check if complete
        if logs.json().get("status") == "completed":
            return result
        time.sleep(1)
```

---

## 13. COMPLIANCE CHECKLIST

Before going live, verify:

- [ ] One-way data flow confirmed
- [ ] Error handling implemented
- [ ] Retry logic with exponential backoff
- [ ] Timeout configured (30s recommended)
- [ ] Input validation in your system
- [ ] Output transformation documented
- [ ] Performance tested under load
- [ ] Failure scenarios tested
- [ ] Documentation complete
- [ ] Ashmit approval obtained

---

## 14. CONTACT & ESCALATION

### **For Integration Questions**
- **Primary Contact**: Ashmit (Primary Owner)
- **Technical Support**: Akanksha (Executor)
- **Advisory**: Vijay Dhawan (Technical Advisor)

### **Escalation Path**
1. Technical issues → Akanksha
2. Policy questions → Ashmit
3. Complex decisions → Ashmit + Vijay
4. Critical issues → CTO

---

**END OF INTEGRATION BOUNDARY DOCUMENT**

**This document defines the official integration policy for BHIV Bucket v1. All integrations must comply with these boundaries.**
