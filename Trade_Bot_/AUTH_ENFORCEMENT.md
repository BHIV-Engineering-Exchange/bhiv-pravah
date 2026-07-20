# AUTH_ENFORCEMENT.md - Authentication Security Implementation

## Overview
This document details the authentication enforcement implemented across the trading system to secure all trading endpoints.

---

## Current State (BEFORE Changes)

### Authentication Status: ❌ DISABLED

**File:** `backend/config.py` (Line 15-16)
```python
# JWT authentication permanently disabled - open access API
ENABLE_AUTH = False
```

**File:** `backend/api_server.py` (Line 31)
```python
# JWT authentication removed - open access API
```

**File:** `backend/api_server.py` (Root endpoint response)
```python
'authentication': 'DISABLED - Open access to all endpoints',
'auth_status': 'disabled',
```

### Security Implications:
- ❌ Anyone could call prediction endpoints
- ❌ No user isolation
- ❌ No audit trail for API usage
- ❌ Rate limiting only protection (insufficient for trading)
- ❌ CRITICAL: Trading endpoints accessible without authentication

---

## Changes Implemented

### 1. Enable Auth in Config
**File:** `backend/config.py`

**BEFORE:**
```python
# JWT authentication permanently disabled - open access API
ENABLE_AUTH = False
```

**AFTER:**
```python
# JWT authentication REQUIRED for all trading endpoints
ENABLE_AUTH = True
```

**Impact:** 
- Activates JWT validation in `auth.py`
- Makes `get_current_user` dependency enforce token requirement
- Returns 401 Unauthorized for requests without valid token

---

### 2. Import Auth Dependency
**File:** `backend/api_server.py`

**BEFORE:**
```python
# JWT authentication removed - open access API
from rate_limiter import check_rate_limit, get_rate_limit_status
```

**AFTER:**
```python
from auth import get_current_user  # JWT authentication enabled
from rate_limiter import check_rate_limit, get_rate_limit_status
```

**Impact:**
- Makes JWT verification function available
- Enables endpoint-level auth enforcement

---

### 3. Update API Documentation
**File:** `backend/api_server.py`

**BEFORE:**
```python
"""MCP-Style API Server for Stock Prediction - FastAPI Version
Exposes REST endpoints for ML predictions with dynamic risk parameters
OPEN ACCESS - No authentication required, with rate limiting and input validation
"""
```

**AFTER:**
```python
"""MCP-Style API Server for Stock Prediction - FastAPI Version
Exposes REST endpoints for ML predictions with dynamic risk parameters
JWT AUTHENTICATION REQUIRED for all endpoints
"""
```

**Impact:**
- Clear documentation that auth is required
- Developers know token is mandatory

---

## How Authentication Works

### JWT Flow:

```
Client Request
    ↓
Include Header: Authorization: Bearer <JWT_TOKEN>
    ↓
FastAPI calls: get_current_user(credentials)
    ↓
auth.py verifies token:
    - Check signature (JWT_SECRET_KEY)
    - Check expiration (exp claim)
    - Decode payload
    ↓
If valid: Return {"username": "...", "exp": "..."}
If invalid: Raise HTTPException(401)
    ↓
Endpoint executes with user context
```

### Token Generation:
```python
from auth import authenticate_user

result = authenticate_user(username="admin", password="admin123")
# Returns: {'success': True, 'token': 'eyJ...', 'username': 'admin', 'expires_in_hours': 24}
```

### Token Validation:
```python
from auth import verify_token

payload = verify_token("eyJ...")
# Returns: {'username': 'admin', 'exp': 1234567890, 'iat': 1234567800}
# Or raises HTTPException(401) if invalid/expired
```

---

## Endpoints Requiring Auth (After Full Implementation)

### ✅ PROTECTED (Auth enabled in config):
- All endpoints in `api_server.py` (requires `user: dict = Depends(get_current_user)` parameter)
- All trading endpoints in `web_backend.py` (requires manual addition)

### 🔒 Auth Dependency Pattern:

**BEFORE (No Auth):**
```python
@app.post("/tools/predict")
async def predict(request_data: PredictRequest):
    # ... endpoint logic
```

**AFTER (With Auth):**
```python
@app.post("/tools/predict")
async def predict(request_data: PredictRequest, user: dict = Depends(get_current_user)):
    # user contains: {'username': '...', 'exp': '...', 'iat': '...'}
    logger.info(f"Predict request from user: {user['username']}")
    # ... endpoint logic
```

---

## Endpoints That Must Be Updated

### api_server.py (Requires adding `user: dict = Depends(get_current_user)`):
- [ ] `/api/predictions` (GET) - Line 121
- [ ] `/tools/predict` (POST) - Line 546
- [ ] `/tools/predict/async` (POST) - Line 594
- [ ] `/tools/scan_all` (POST) - Line 638
- [ ] `/tools/analyze` (POST) - Line 701

### web_backend.py (Requires adding auth to trading endpoints):
- [ ] `/api/order` (POST) - Line ~5132
- [ ] `/api/trade/execute` (POST)
- [ ] `/api/portfolio/buy` (POST)
- [ ] `/api/portfolio/sell` (POST)
- [ ] `/mcp/execute` (POST) - Line ~8010
- [ ] Any endpoint calling `live_executor` or placing orders

---

## Proof of Auth Enforcement

### Test 1: Request Without Token (BEFORE)
```bash
curl -X POST http://localhost:8000/tools/predict \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE.NS"], "horizon": "intraday"}'

# Response: 200 OK (predictions returned)
```

### Test 2: Request Without Token (AFTER - once endpoints updated)
```bash
curl -X POST http://localhost:8000/tools/predict \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE.NS"], "horizon": "intraday"}'

# Expected Response: 401 Unauthorized
# {"detail": "Missing authentication token"}
```

### Test 3: Request With Valid Token (AFTER)
```bash
curl -X POST http://localhost:8000/tools/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{"symbols": ["RELIANCE.NS"], "horizon": "intraday"}'

# Expected Response: 200 OK (predictions returned)
```

### Test 4: Request With Expired Token (AFTER)
```bash
curl -X POST http://localhost:8000/tools/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer expired_token..." \
  -d '{"symbols": ["RELIANCE.NS"], "horizon": "intraday"}'

# Expected Response: 401 Unauthorized
# {"detail": "Token has expired"}
```

---

## Security Improvements

### BEFORE:
| Aspect | Status |
|--------|--------|
| Authentication | ❌ Disabled |
| User Isolation | ❌ None |
| Audit Trail | ❌ No user tracking |
| Token Expiration | N/A |
| Brute Force Protection | ⚠️ Rate limiting only |
| Trading Endpoint Security | ❌ Open access |

### AFTER:
| Aspect | Status |
|--------|--------|
| Authentication | ✅ JWT Required |
| User Isolation | ✅ Per-user credentials (MongoDB) |
| Audit Trail | ✅ Username in logs |
| Token Expiration | ✅ 24 hours (configurable) |
| Brute Force Protection | ✅ Rate limiting + Auth |
| Trading Endpoint Security | ✅ Token required |

---

## Configuration Options

### JWT Settings (backend/config.py):
```python
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-key-for-optional-auth')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24  # Token valid for 24 hours
```

### Production Recommendations:
```bash
# Set strong secret key in environment
export JWT_SECRET_KEY="your-256-bit-secret-key-here-min-32-chars"

# Reduce token expiration for high-security
export JWT_EXPIRATION_HOURS=8

# Set admin credentials
export ADMIN_USERNAME="secure_admin_username"
export ADMIN_PASSWORD="complex-password-here"
```

---

## Migration Guide for Frontend

### Step 1: Obtain Token
```typescript
// Login request
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});

const { token } = await loginResponse.json();
localStorage.setItem('jwt_token', token);
```

### Step 2: Include Token in Requests
```typescript
// API call with auth
const response = await fetch('http://localhost:8000/tools/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
  },
  body: JSON.stringify({
    symbols: ['RELIANCE.NS'],
    horizon: 'intraday'
  })
});
```

### Step 3: Handle Token Expiration
```typescript
// Check for 401 and refresh token
if (response.status === 401) {
  // Token expired - redirect to login
  localStorage.removeItem('jwt_token');
  window.location.href = '/login';
}
```

---

## Verification Checklist

- [x] `ENABLE_AUTH = True` in config.py
- [x] `get_current_user` imported in api_server.py
- [x] Docstring updated to reflect auth requirement
- [ ] Auth dependency added to all api_server.py endpoints
- [ ] Auth dependency added to all web_backend.py trading endpoints
- [ ] Frontend updated to include JWT token in requests
- [ ] Token refresh mechanism implemented
- [ ] 401 error handling added to frontend

---

## Rollback Procedure (If Needed)

If authentication causes issues, rollback:

```python
# backend/config.py
ENABLE_AUTH = False  # Temporarily disable

# This will make get_current_user return:
# {"username": "anonymous", "auth_disabled": True}
```

**WARNING:** Only disable in development/testing. NEVER in production with real trading.

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-23  
**Status:** Partially Implemented (Config enabled, endpoint dependencies pending)
