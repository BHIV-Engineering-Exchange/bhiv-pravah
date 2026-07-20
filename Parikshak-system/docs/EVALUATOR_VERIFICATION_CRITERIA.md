# 🎯 EVALUATOR VERIFICATION FRAMEWORK - COMPLETE SPECIFICATION

## 📋 DECISION CORRECTNESS CRITERIA

### **How to Verify a Decision is Correct:**

1. **Score Range Validation**: `0 ≤ score ≤ 100`
2. **Status-Score Alignment**: 
   - Score ≥ 80 → Status = "pass"
   - 50 ≤ Score < 80 → Status = "borderline"  
   - Score < 50 → Status = "fail"
3. **Assignment Authority**: If assignment engine says FAIL → final must be FAIL
4. **Contract Compliance**: All required fields present and valid
5. **Hierarchy Respected**: Signals cannot override assignment decisions

---

## 🔄 EXACT MATCH REQUIREMENTS (Determinism)

### **MANDATORY EXACT MATCH** ✅
These fields MUST be identical across multiple runs with same input:

```json
{
  "score": 75,                    // MUST match exactly
  "status": "borderline",         // MUST match exactly
  "failure_reasons": ["scope"],   // MUST match exactly (content & order)
  "analysis": {
    "technical_quality": 70,      // MUST match exactly
    "clarity": 80,                // MUST match exactly  
    "discipline_signals": 65      // MUST match exactly
  }
}
```

### **TOLERANCE ALLOWED** ⚠️
These fields can have small variance:

```json
{
  "meta": {
    "evaluation_time_ms": 150,    // ±50ms tolerance allowed
    "determinism_hash": "abc123"  // Can be regenerated but should be consistent
  }
}
```

### **MISMATCH INDICATORS** ❌
Consider it a mismatch when:

- Score differs by >1 point
- Status changes between runs
- Failure reasons list changes
- Core analysis values differ
- Required fields missing

---

## 📝 SAMPLE TEST CASES

### **Test Case 1: High Quality Task**

**Input:**
```json
{
  "task_title": "Implement Secure REST API Authentication System with JWT and Database Integration",
  "task_description": "Objective: Build comprehensive authentication system\n\nDeliverables:\n- JWT token generation and validation\n- User registration and login endpoints\n- Secure password hashing\n- Database integration for user management\n\nTimeline: 3 weeks development\n\nScope: Authentication module only\n\nTechnical Requirements:\n- RESTful API design\n- Secure password storage\n- Token expiration handling\n- Input validation",
  "submitted_by": "Test Developer",
  "module_id": "task-review-agent",
  "schema_version": "v1.0"
}
```

**Expected Output:**
```json
{
  "score": 80,
  "readiness_percent": 80,
  "status": "pass",
  "failure_reasons": [],
  "improvement_hints": [
    "Consider adding API versioning strategy",
    "Include rate limiting specifications"
  ],
  "analysis": {
    "technical_quality": 85,
    "clarity": 90,
    "discipline_signals": 75
  },
  "meta": {
    "evaluation_time_ms": 150,
    "mode": "hybrid-aware-v2",
    "contract_version": "aware-v2"
  },
  "accuracy_score": 90.0,
  "completeness_score": 100.0,
  "quality_score": 85.0,
  "timeline_penalty": 0.0,
  "deliverables_matched": 4,
  "deliverables_total": 4
}
```

### **Test Case 2: Poor Quality Task**

**Input:**
```json
{
  "task_title": "Fix bug",
  "task_description": "Fix the bug in the system",
  "submitted_by": "Developer",
  "module_id": "task-review-agent",
  "schema_version": "v1.0"
}
```

**Expected Output:**
```json
{
  "score": 49,
  "readiness_percent": 49,
  "status": "fail",
  "failure_reasons": [
    "objective",
    "deliverables",
    "timeline"
  ],
  "improvement_hints": [
    "Add objective to task definition",
    "Add deliverables to task definition", 
    "Add timeline to task definition",
    "Enhance technical depth and architectural clarity"
  ],
  "analysis": {
    "technical_quality": 0,
    "clarity": 25,
    "discipline_signals": 0
  },
  "meta": {
    "evaluation_time_ms": 120,
    "mode": "hybrid-aware-v2",
    "contract_version": "aware-v2"
  },
  "accuracy_score": 100.0,
  "completeness_score": 0.0,
  "quality_score": 0.0,
  "timeline_penalty": 0.0,
  "deliverables_matched": 0,
  "deliverables_total": 4
}
```

### **Test Case 3: Borderline Quality Task**

**Input:**
```json
{
  "task_title": "Database API Implementation",
  "task_description": "Objective: Create database API endpoints\n\nDeliverables:\n- CRUD operations for user data\n- Basic API documentation\n\nTimeline: 1 week development",
  "submitted_by": "Developer",
  "module_id": "task-review-agent",
  "schema_version": "v1.0"
}
```

**Expected Output:**
```json
{
  "score": 62,
  "readiness_percent": 62,
  "status": "borderline",
  "failure_reasons": [
    "scope"
  ],
  "improvement_hints": [
    "Add scope to task definition",
    "Enhance technical specifications",
    "Include acceptance criteria"
  ],
  "analysis": {
    "technical_quality": 50,
    "clarity": 75,
    "discipline_signals": 60
  },
  "meta": {
    "evaluation_time_ms": 135,
    "mode": "hybrid-aware-v2",
    "contract_version": "aware-v2"
  },
  "accuracy_score": 75.0,
  "completeness_score": 75.0,
  "quality_score": 50.0,
  "timeline_penalty": 0.0,
  "deliverables_matched": 3,
  "deliverables_total": 4
}
```

---

## 🧪 DETERMINISM VERIFICATION

### **Mandatory Reproducibility Test:**

```python
# MUST produce identical results
input_data = create_task("Fix bug", "Fix the bug in the system")

output_1 = evaluator.evaluate(input_data)
output_2 = evaluator.evaluate(input_data)  # Same input again

# These MUST be exactly equal
assert output_1["score"] == output_2["score"]
assert output_1["status"] == output_2["status"] 
assert output_1["failure_reasons"] == output_2["failure_reasons"]
assert output_1["analysis"] == output_2["analysis"]

# These can have tolerance
assert abs(output_1["meta"]["evaluation_time_ms"] - 
          output_2["meta"]["evaluation_time_ms"]) <= 50
```

### **When to Consider it a Mismatch:**

1. **Score Variance**: Any difference in score value
2. **Status Change**: Different status for same input
3. **Analysis Drift**: Technical quality, clarity, or discipline signals differ
4. **Failure Reason Changes**: Different failure reasons or order
5. **Missing Fields**: Required fields not present

---

## ✅ VERIFICATION CHECKLIST

### **Decision Correctness Verification:**
- [ ] Score is between 0-100
- [ ] Status aligns with score (pass/borderline/fail)
- [ ] Assignment authority respected (FAIL cannot be overridden)
- [ ] All required fields present
- [ ] Contract compliance verified
- [ ] Hierarchy rules followed

### **Determinism Verification:**
- [ ] Same input produces same score
- [ ] Same input produces same status
- [ ] Same input produces same failure reasons
- [ ] Same input produces same analysis values
- [ ] Timing variance within acceptable range (±50ms)

### **Quality Verification:**
- [ ] High quality tasks score ≥70
- [ ] Poor quality tasks score <50
- [ ] Borderline tasks score 50-79
- [ ] Failure reasons are actionable
- [ ] Improvement hints are relevant

---

## 🎯 ANSWER TO YOUR QUESTIONS

### **1. How will you verify whether a decision is correct?**
- Check score range (0-100)
- Verify status-score alignment
- Ensure assignment authority is respected
- Validate contract compliance
- Confirm all required fields present

### **2. What exactly should match in replay?**
- **EXACT**: score, status, failure_reasons, analysis values
- **TOLERANCE**: evaluation_time_ms (±50ms), determinism_hash

### **3. When should it be considered a mismatch?**
- Score differs by any amount
- Status changes between runs
- Failure reasons list changes
- Core analysis values differ

### **4. Must output remain exactly the same?**
**YES** - Core evaluation fields must be identical:
- Score, status, failure reasons, analysis
**NO** - Timing and hash fields can have small variance

---

This framework provides clear, measurable criteria for verifying evaluator decisions and ensuring deterministic behavior across all system components.