# Postman Testing Guide

Base URL: `http://localhost:8000`

## 1. Sample Text Module Test

**POST** `/core`
```json
{
    "module": "sample_text",
    "intent": "generate",
    "user_id": "test_user",
    "data": {
        "input_text": "Hello world this is a test"
    }
}
```
**Expected Output:**
```json
{
    "status": "success",
    "message": "Text processed successfully",
    "result": {
        "word_count": 6
    }
}
```

## 2. Finance Agent Test

**POST** `/core`
```json
{
    "module": "finance",
    "intent": "generate",
    "user_id": "finance_user",
    "data": {
        "report_type": "quarterly"
    }
}
```
**Expected Output:**
```json
{
    "status": "success",
    "message": "Financial report generated",
    "result": {
        "report_type": "financial",
        "data": {
            "report_type": "quarterly"
        }
    }
}
```

## 3. Memory Limit Test (5 Entries)

Send these **6 requests** sequentially with same user_id:

**Request 1-6:** **POST** `/core`
```json
{
    "module": "finance",
    "intent": "generate",
    "user_id": "memory_test",
    "data": {
        "test": "request_1"
    }
}
```
Change `"request_1"` to `"request_2"`, `"request_3"`, etc.

**Check Memory:** **GET** `/get-history?user_id=memory_test`

**Expected Output:** Array with exactly 5 entries (oldest deleted)
```json
[
    {
        "module": "finance",
        "timestamp": "2024-01-01T12:00:00",
        "request": {"module": "finance", "intent": "generate", "data": {"test": "request_6"}},
        "response": {"status": "success", "message": "Financial report generated", "result": {...}}
    },
    // ... 4 more entries (request_5, request_4, request_3, request_2)
]
```

## 4. Cross-Module Memory Isolation Test

**Step 1:** Send 3 finance requests
```json
{
    "module": "finance",
    "intent": "generate",
    "user_id": "isolation_test",
    "data": {"test": "finance_1"}
}
```

**Step 2:** Send 3 education requests
```json
{
    "module": "education",
    "intent": "generate",
    "user_id": "isolation_test",
    "data": {"test": "education_1"}
}
```

**Check:** **GET** `/get-history?user_id=isolation_test`

**Expected:** 6 total entries (3 finance + 3 education)

## 5. Context Retrieval Test

**GET** `/get-context?user_id=isolation_test`

**Expected Output:** Last 3 interactions across all modules
```json
[
    {
        "module": "education",
        "timestamp": "2024-01-01T12:03:00",
        "request": {...},
        "response": {...}
    },
    {
        "module": "education", 
        "timestamp": "2024-01-01T12:02:00",
        "request": {...},
        "response": {...}
    },
    {
        "module": "education",
        "timestamp": "2024-01-01T12:01:00", 
        "request": {...},
        "response": {...}
    }
]
```

## 6. Invalid Module Test

**POST** `/core`
```json
{
    "module": "invalid_module",
    "intent": "generate",
    "user_id": "test",
    "data": {}
}
```
**Expected:** HTTP 422 Validation Error
 
## 7. Empty Text Test

**POST** `/core`
```json
{
    "module": "sample_text",
    "intent": "generate",
    "user_id": "empty_test",
    "data": {
        "input_text": ""
    }
}
```
**Expected Output:**
```json
{
    "status": "success",
    "message": "Text processed successfully",
    "result": {
        "word_count": 0
    }
}
```

## 8. API Info Test

**GET** `/`

**Expected Output:**
```json
{
    "message": "Unified Backend Bridge API",
    "version": "1.0.0",
    "docs": "/docs"
}
```

## Test Sequence Summary

1. Start app: `python main.py`
2. Test sample_text module functionality
3. Test memory limit with 6 requests
4. Test cross-module isolation
5. Verify context retrieval
6. Test validation errors
7. Test edge cases (empty input)

All tests should return HTTP 200 status codes except the invalid module test (422).