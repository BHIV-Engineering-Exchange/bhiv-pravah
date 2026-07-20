# API Contract — Part 4: Gateway Security & Portals (51-85 of 111)

**Continued from:** [API_CONTRACT_PART3.md](./API_CONTRACT_PART3.md)

**Version:** 4.1.0  
**Last Updated:** January 22, 2026  
**Total Endpoints:** 111 (80 Gateway + 6 Agent + 25 LangGraph)  
**Database:** MongoDB Atlas  
**Analysis Source:** Comprehensive endpoint analysis from services directories

---

## Gateway Security Testing

### 46. GET /v1/security/rate-limit-status

**Purpose:** Check current rate limit status

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `check_rate_limit_status()`

**Timeout:** 5s

**Request:**
```http
GET /v1/security/rate-limit-status
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "rate_limit_enabled": true,
  "requests_per_minute": 60,
  "current_requests": 15,
  "remaining_requests": 45,
  "reset_time": "2026-01-22T13:37:00Z",
  "status": "active"
}
```

**When Called:** Admin monitors rate limiting

**Database Impact:** Query rate limit cache/memory

---

### 47. GET /v1/security/blocked-ips

**Purpose:** View list of blocked IP addresses

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `view_blocked_ips()`

**Timeout:** 5s

**Request:**
```http
GET /v1/security/blocked-ips
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "blocked_ips": [
    {
      "ip": "192.168.1.100",
      "reason": "Rate limit exceeded",
      "blocked_at": "2026-01-22T10:30:00Z"
    }
  ],
  "total_blocked": 1,
  "last_updated": "2026-01-22T13:37:00Z"
}
```

**When Called:** Admin reviews security blocks

**Database Impact:** Query blocked IPs cache/database

---

### 48. POST /v1/security/test-input-validation

**Purpose:** Test input validation against various attack vectors (XSS, SQL injection, etc.)

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_input_validation()`

**Timeout:** 5s

**Request:**
```http
POST /v1/security/test-input-validation
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "input_data": "<script>alert('xss')</script>",
  "field_type": "text_input",
  "validation_rules": ["xss", "sql_injection", "command_injection"]
}
```

**Response (200 OK):**
```json
{
  "input": "<script>alert('xss')</script>",
  "validation_result": "BLOCKED",
  "threats_detected": ["XSS attempt detected"],
  "validation_rules_applied": ["xss", "sql_injection", "command_injection"],
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid input format
- 401 Unauthorized: Invalid API key

**When Called:** Security testing, penetration testing

**Database Impact:** None (security validation only)

---

### 49. POST /v1/security/validate-email

**Purpose:** Validate email format and security checks

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `validate_email()`

**Timeout:** 5s

**Request:**
```http
POST /v1/security/validate-email
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "email": "test@example.com",
  "check_mx_record": true,
  "check_disposable": true
}
```

**Response (200 OK):**
```json
{
  "email": "test@example.com",
  "is_valid": true,
  "checks_passed": {
    "format": true,
    "mx_record": true,
    "disposable": false
  },
  "security_score": 95,
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid email format
- 401 Unauthorized: Invalid API key

**When Called:** Email validation during registration or form submission

**Database Impact:** None (validation only)

---

### 50. POST /v1/security/test-email-validation

**Purpose:** Comprehensive email validation testing

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_email_validation()`

**Timeout:** 10s

**Request:**
```http
POST /v1/security/test-email-validation
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "email": "test@example.com",
  "validation_tests": ["format", "domain", "disposable", "role_account"]
}
```

**Response (200 OK):**
```json
{
  "email": "test@example.com",
  "tests_results": {
    "format": {"passed": true, "details": "Valid RFC format"},
    "domain": {"passed": true, "details": "MX record exists"},
    "disposable": {"passed": false, "details": "Not disposable domain"},
    "role_account": {"passed": false, "details": "Not a role account"}
  },
  "overall_security_rating": "safe",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid email format
- 401 Unauthorized: Invalid API key

**When Called:** Security testing of email validation mechanisms

**Database Impact:** None (validation only)

---

### 51. POST /v1/security/validate-phone

**Purpose:** Validate phone number format and security checks

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `validate_phone()`

**Timeout:** 5s

**Request:**
```http
POST /v1/security/validate-phone
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "phone": "+1234567890",
  "country_code": "US",
  "validate_format": true,
  "validate_carrier": false
}
```

**Response (200 OK):**
```json
{
  "phone": "+1234567890",
  "is_valid": true,
  "formatted_number": "+1234567890",
  "country_code": "US",
  "validation_details": {
    "format_valid": true,
    "international_format": true,
    "valid_length": true
  },
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid phone format
- 401 Unauthorized: Invalid API key

**When Called:** Phone validation during registration or form submission

**Database Impact:** None (validation only)

---

### 52. POST /v1/security/test-phone-validation

**Purpose:** Comprehensive phone validation testing

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_phone_validation()`

**Timeout:** 10s

**Request:**
```http
POST /v1/security/test-phone-validation
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "phone": "+1234567890",
  "validation_tests": ["format", "country", "carrier"]
}
```

**Response (200 OK):**
```json
{
  "phone": "+1234567890",
  "tests_results": {
    "format": {"passed": true, "details": "Valid E.164 format"},
    "country": {"passed": true, "details": "Valid US number"},
    "carrier": {"passed": true, "details": "Carrier verified"}
  },
  "security_rating": "valid",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid phone format
- 401 Unauthorized: Invalid API key

**When Called:** Security testing of phone validation mechanisms

**Database Impact:** None (validation only)

---

### 53. GET /v1/security/test-headers

**Purpose:** Test security headers configuration

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_security_headers()`

**Timeout:** 5s

**Request:**
```http
GET /v1/security/test-headers
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "security_headers": {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
  },
  "headers_compliance": {
    "csp_compliant": true,
    "hsts_compliant": true,
    "xss_protection_active": true
  },
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** Security audit of HTTP headers

**Database Impact:** None (header validation only)

---

### 54. GET /v1/security/security-headers-test

**Purpose:** Legacy test for security headers (deprecated in favor of /v1/security/test-headers)

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_security_headers_legacy()`

**Timeout:** 5s

**Request:**
```http
GET /v1/security/security-headers-test
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "security_headers": {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'"
  },
  "headers_status": "valid",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** Legacy security testing tools

**Database Impact:** None (header validation only)

---

### 55. POST /v1/security/penetration-test

**Purpose:** Perform penetration testing simulation

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `penetration_test()`

**Timeout:** 30s

**Request:**
```http
POST /v1/security/penetration-test
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "target_endpoint": "/api/v1/test",
  "test_types": ["sql_injection", "xss", "csrf", "idor"],
  "severity_threshold": "medium"
}
```

**Response (200 OK):**
```json
{
  "test_session_id": "pt_123456",
  "target_endpoint": "/api/v1/test",
  "tests_executed": 4,
  "vulnerabilities_found": 0,
  "highest_severity": "none",
  "test_summary": {
    "sql_injection": {"status": "passed", "vulnerabilities": 0},
    "xss": {"status": "passed", "vulnerabilities": 0},
    "csrf": {"status": "passed", "vulnerabilities": 0},
    "idor": {"status": "passed", "vulnerabilities": 0}
  },
  "completed_at": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid test configuration
- 401 Unauthorized: Invalid API key

**When Called:** Regular security penetration testing

**Database Impact:** INSERT into security_test_logs collection

---

### 56. GET /v1/security/test-auth

**Purpose:** Test authentication mechanisms

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_authentication()`

**Timeout:** 10s

**Request:**
```http
GET /v1/security/test-auth
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "auth_status": "valid",
  "token_type": "bearer",
  "token_algorithm": "HS256",
  "expiration_time": 86400,
  "claims": {
    "sub": "api_client",
    "type": "service",
    "exp": 1702134000
  },
  "security_checks": {
    "token_signature_valid": true,
    "not_expired": true,
    "algorithm_secure": true
  },
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** Authentication mechanism validation

**Database Impact:** None (token validation only)

---

### 57. GET /v1/security/penetration-test-endpoints

**Purpose:** List endpoints available for penetration testing

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `penetration_test_endpoints()`

**Timeout:** 5s

**Request:**
```http
GET /v1/security/penetration-test-endpoints
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "available_endpoints": [
    {"path": "/api/v1/test", "methods": ["GET", "POST"]},
    {"path": "/v1/users", "methods": ["GET", "POST", "PUT", "DELETE"]},
    {"path": "/v1/data", "methods": ["GET", "POST"]}
  ],
  "total_endpoints": 3,
  "last_scan": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** Planning penetration testing sessions

**Database Impact:** None (static endpoint list)

---

## Gateway CSP Management

### 58. POST /v1/security/csp-report

**Purpose:** Report Content Security Policy violations

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `csp_violation_reporting()`

**Timeout:** 5s

**Request:**
```http
POST /v1/security/csp-report
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "violated_directive": "script-src",
  "blocked_uri": "https://malicious-site.com/script.js",
  "document_uri": "https://bhiv-platform.com/dashboard"
}
```

**Response (200 OK):**
```json
{
  "message": "CSP violation reported successfully",
  "violation": {
    "violated_directive": "script-src",
    "blocked_uri": "https://malicious-site.com/script.js",
    "document_uri": "https://bhiv-platform.com/dashboard",
    "timestamp": "2026-01-22T13:37:00Z"
  },
  "report_id": "csp_report_1702134000"
}
```

**When Called:** Browser reports CSP violation

**Database Impact:** INSERT into csp_violations collection

---

### 59. GET /v1/security/csp-violations

**Purpose:** View all Content Security Policy violations

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `view_csp_violations()`

**Timeout:** 10s

**Request:**
```http
GET /v1/security/csp-violations
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "violations": [
    {
      "id": "csp_violation_1",
      "directive": "script-src",
      "blocked_uri": "https://malicious-site.com/script.js",
      "document_uri": "https://bhiv-platform.com/dashboard",
      "violated_directive": "script-src 'self'",
      "effective_directive": "script-src",
      "original_policy": "script-src 'self'; object-src 'none';",
      "referrer": "",
      "status_code": 200,
      "timestamp": "2026-01-22T13:37:00Z",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "total_violations": 1,
  "period_start": "2026-01-01T00:00:00Z",
  "period_end": "2026-01-22T23:59:59Z",
  "last_updated": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** Security team reviews CSP violations

**Database Impact:** SELECT from csp_violations collection

---

### 60. GET /v1/security/csp-policies

**Purpose:** Get current Content Security Policy configurations

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `get_csp_policies()`

**Timeout:** 5s

**Request:**
```http
GET /v1/security/csp-policies
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "current_policies": {
    "default_src": "'self'",
    "script_src": "'self' 'unsafe-inline'",
    "style_src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
    "img_src": "'self' data: https:",
    "font_src": "'self' https://fonts.gstatic.com",
    "connect_src": "'self' https://api.example.com",
    "frame_ancestors": "'none'",
    "report_uri": "/v1/security/csp-report"
  },
  "policy_effective_date": "2026-01-01T00:00:00Z",
  "enforcement_mode": "enforce",
  "report_only": false,
  "last_updated": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** Admin audits CSP policies

**Database Impact:** SELECT from csp_policies configuration

---

### 61. POST /v1/security/test-csp-policy

**Purpose:** Test Content Security Policy enforcement

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_csp_policy()`

**Timeout:** 10s

**Request:**
```http
POST /v1/security/test-csp-policy
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "policy_directive": "script-src 'self'",
  "test_payload": "<script>alert('test')</script>",
  "expected_result": "blocked",
  "test_scenario": "xss_script_attempt"
}
```

**Response (200 OK):**
```json
{
  "test_id": "csp_test_123",
  "policy_directive": "script-src 'self'",
  "test_payload": "<script>alert('test')</script>",
  "expected_result": "blocked",
  "actual_result": "blocked",
  "test_passed": true,
  "execution_time": "0.02s",
  "policy_enforcement": "active",
  "test_scenario": "xss_script_attempt",
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid test configuration
- 401 Unauthorized: Invalid API key

**When Called:** Security testing of CSP policies

**Database Impact:** INSERT into csp_test_logs collection

---

## Gateway Two-Factor Authentication

### 62. POST /v1/auth/2fa/setup

**Purpose:** Initialize 2FA for user account with QR code generation

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `setup_2fa()`

**Timeout:** 30s

**Request:**
```http
POST /v1/auth/2fa/setup
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "user_id": "user_12345",
  "user_type": "candidate"
}
```

**Response (200 OK):**
```json
{
  "message": "2FA setup initiated",
  "user_id": "user_12345",
  "user_type": "candidate",
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "manual_entry_key": "JBSWY3DPEHPK3PXP",
  "instructions": "Scan QR code with Google Authenticator, Microsoft Authenticator, or Authy"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key
- 400 Bad Request: Missing user_id

**When Called:** User enables 2FA in security settings

**Database Impact:** UPDATE user records with 2FA settings

---

### 63. POST /v1/auth/2fa/verify

**Purpose:** Verify TOTP code during 2FA authentication

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `verify_2fa()`

**Timeout:** 10s

**Request:**
```http
POST /v1/auth/2fa/verify
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "user_id": "user_12345",
  "totp_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "2FA verification successful",
  "user_id": "user_12345",
  "verified": true,
  "verified_at": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid 2FA code
- 400 Bad Request: Missing required fields

**When Called:** User submits 2FA code during login

**Database Impact:** UPDATE user records with last verified timestamp

---

### 64. POST /v1/auth/2fa/login

**Purpose:** Login with 2FA verification

**Authentication:** None (public endpoint)

**Implementation:** `services/gateway/app/main.py` → `login_2fa()`

**Timeout:** 15s

**Request:**
```http
POST /v1/auth/2fa/login
Content-Type: application/json

{
  "username": "demo_user",
  "password": "demo_password",
  "totp_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": "user_12345",
  "2fa_verified": true
}
```

**Error Responses:**
- 401 Unauthorized: Invalid credentials or 2FA code
- 400 Bad Request: Missing required fields

**When Called:** User attempts to login with 2FA

**Database Impact:** UPDATE user login timestamps and session data

---

### 65. GET /v1/auth/2fa/status/{user_id}

**Purpose:** Check 2FA status for user

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `get_2fa_status()`

**Timeout:** 5s

**Request:**
```http
GET /v1/auth/2fa/status/user_12345
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "user_id": "user_12345",
  "2fa_enabled": true,
  "setup_date": "2026-01-01T12:00:00Z",
  "last_used": "2026-01-22T08:30:00Z",
  "backup_codes_remaining": 8
}
```

**Error Responses:**
- 404 Not Found: User not found
- 401 Unauthorized: Invalid API key

**When Called:** Dashboard loads user security settings

**Database Impact:** SELECT from user records for 2FA status

---

### 66. POST /v1/auth/2fa/disable

**Purpose:** Disable 2FA for user account

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `disable_2fa()`

**Timeout:** 10s

**Request:**
```http
POST /v1/auth/2fa/disable
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "user_id": "user_12345",
  "confirmation": true
}
```

**Response (200 OK):**
```json
{
  "message": "2FA disabled successfully",
  "user_id": "user_12345",
  "disabled_at": "2026-01-22T13:37:00Z",
  "was_enabled": true
}
```

**Error Responses:**
- 404 Not Found: User not found
- 401 Unauthorized: Invalid API key
- 400 Bad Request: Confirmation not provided

**When Called:** User disables 2FA in security settings

**Database Impact:** UPDATE user records to disable 2FA

---

### 67. POST /v1/auth/2fa/backup-codes

**Purpose:** Generate backup codes for 2FA recovery

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `generate_backup_codes()`

**Timeout:** 15s

**Request:**
```http
POST /v1/auth/2fa/backup-codes
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "user_id": "user_12345"
}
```

**Response (200 OK):**
```json
{
  "message": "Backup codes generated successfully",
  "user_id": "user_12345",
  "backup_codes": [
    "ABCD-EFGH",
    "IJKL-MNOP",
    "QRST-UVWX",
    "YZ12-3456",
    "7890-ABCD"
  ],
  "codes_generated_at": "2026-01-22T13:37:00Z",
  "expires_at": "2027-01-22T13:37:00Z",
  "total_codes": 5
}
```

**Error Responses:**
- 404 Not Found: User not found
- 401 Unauthorized: Invalid API key

**When Called:** User requests 2FA backup codes

**Database Impact:** UPDATE user records with encrypted backup codes

---

### 68. POST /v1/auth/2fa/test-token

**Purpose:** Test 2FA token validity

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_2fa_token()`

**Timeout:** 5s

**Request:**
```http
POST /v1/auth/2fa/test-token
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "user_id": "user_12345",
  "totp_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "user_id": "user_12345",
  "token_valid": true,
  "valid_until": "2026-01-22T13:38:00Z",
  "verification_time": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid 2FA code
- 400 Bad Request: Missing required fields

**When Called:** User tests 2FA token during setup

**Database Impact:** None (validation only)

---

### 69. GET /v1/auth/2fa/qr/{user_id}

**Purpose:** Get QR code for 2FA setup

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `get_qr_code()`

**Timeout:** 10s

**Request:**
```http
GET /v1/auth/2fa/qr/user_12345
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "user_id": "user_12345",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "provisioning_uri": "otpauth://totp/BHIV-HR:user_12345?secret=JBSWY3DPEHPK3PXP&issuer=BHIV-HR",
  "setup_instructions": "Scan QR code with authenticator app"
}
```

**Error Responses:**
- 404 Not Found: User not found
- 401 Unauthorized: Invalid API key

**When Called:** User accesses 2FA setup QR code

**Database Impact:** SELECT from user records to get secret key

---

## Gateway Password Management

### 70. POST /v1/auth/password/validate

**Purpose:** Validate password against security requirements

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `validate_password()`

**Timeout:** 5s

**Request:**
```http
POST /v1/auth/password/validate
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "password": "SecurePass123!",
  "user_context": "registration"
}
```

**Response (200 OK):**
```json
{
  "password_strength": "Very Strong",
  "score": 100,
  "max_score": 100,
  "is_valid": true,
  "requirements_met": {
    "min_length": true,
    "uppercase": true,
    "lowercase": true,
    "numbers": true,
    "special_chars": true,
    "not_common": true
  },
  "feedback": [],
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid input format
- 401 Unauthorized: Invalid API key

**When Called:** Password validation during registration or change

**Database Impact:** None (validation only)

---

### 71. GET /v1/auth/password/generate

**Purpose:** Generate secure random password

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `generate_password()`

**Timeout:** 5s

**Request:**
```http
GET /v1/auth/password/generate?length=12&include_symbols=true&exclude_ambiguous=false
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "generated_password": "Xk9$mN2#pL7@",
  "length": 12,
  "includes_symbols": true,
  "includes_numbers": true,
  "includes_uppercase": true,
  "includes_lowercase": true,
  "excludes_ambiguous": false,
  "entropy_bits": 75.2,
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Parameters:**
- length: Password length (default: 12, min: 8, max: 128)
- include_symbols: Include special characters (default: true)
- exclude_ambiguous: Exclude ambiguous characters (default: false)

**Error Responses:**
- 400 Bad Request: Invalid parameters
- 401 Unauthorized: Invalid API key

**When Called:** Password reset or initial account setup

**Database Impact:** None (generation only)

---

### 72. GET /v1/auth/password/policy

**Purpose:** Get current password policy requirements

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `get_password_policy()`

**Timeout:** 5s

**Request:**
```http
GET /v1/auth/password/policy
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "policy": {
    "min_length": 8,
    "max_length": 128,
    "require_uppercase": true,
    "require_lowercase": true,
    "require_numbers": true,
    "require_special_chars": true,
    "min_special_chars": 1,
    "max_repeating_chars": 2,
    "avoid_common_patterns": true,
    "avoid_personal_info": true
  },
  "policy_version": "1.0.0",
  "effective_date": "2026-01-01T00:00:00Z",
  "last_updated": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** UI displays password requirements

**Database Impact:** SELECT from password_policy configuration

---

### 73. POST /v1/auth/password/change

**Purpose:** Change user password with validation

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `change_password()`

**Timeout:** 10s

**Request:**
```http
POST /v1/auth/password/change
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "user_id": "user_12345",
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePass456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully",
  "user_id": "user_12345",
  "changed_at": "2026-01-22T13:37:00Z",
  "requires_logout": false
}
```

**Error Responses:**
- 400 Bad Request: Invalid password format
- 401 Unauthorized: Invalid current password
- 404 Not Found: User not found

**When Called:** User changes their password

**Database Impact:** UPDATE user records with new hashed password

---

### 74. POST /v1/auth/password/strength

**Purpose:** Analyze password strength in detail

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `test_password_strength()`

**Timeout:** 5s

**Request:**
```http
POST /v1/auth/password/strength
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "password": "SecurePass123!",
  "user_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }
}
```

**Response (200 OK):**
```json
{
  "password": "SecurePass123!",
  "strength_score": 95,
  "max_score": 100,
  "strength_level": "very_strong",
  "crack_time": {
    "offline_fast_hashing_1e10_per_second": "centuries",
    "online_bcrypt_12_rounds": "centuries",
    "online_throttling_100_per_hour": "centuries"
  },
  "feedback": {
    "warning": "",
    "suggestions": ["Add another word or two. Uncommon words are better."]
  },
  "characteristics": {
    "length": 14,
    "has_uppercase": true,
    "has_lowercase": true,
    "has_numbers": true,
    "has_special_chars": true,
    "num_special_chars": 1
  },
  "timestamp": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid input format
- 401 Unauthorized: Invalid API key

**When Called:** Password strength analysis during registration

**Database Impact:** None (analysis only)

---

### 75. GET /v1/auth/password/security-tips

**Purpose:** Get password security recommendations

**Authentication:** Bearer token required

**Implementation:** `services/gateway/app/main.py` → `get_security_tips()`

**Timeout:** 5s

**Request:**
```http
GET /v1/auth/password/security-tips
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "security_tips": [
    "Use at least 12 characters",
    "Include uppercase, lowercase, numbers, and special characters",
    "Avoid common patterns and personal information",
    "Use unique passwords for different accounts",
    "Consider using a password manager",
    "Enable two-factor authentication when available"
  ],
  "best_practices": [
    "Create passphrases with random words",
    "Change passwords regularly for sensitive accounts",
    "Never share passwords with others",
    "Be cautious of phishing attempts"
  ],
  "updated_at": "2026-01-22T13:37:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid API key

**When Called:** User accesses password security guidance

**Database Impact:** SELECT from security_tips configuration

---

## Gateway Candidate Portal

### 76. POST /v1/candidate/register

**Purpose:** Register new candidate account

**Authentication:** None (public registration)

**Implementation:** `services/gateway/app/main.py` → `candidate_register()`

**Timeout:** 15s

**Request:**
```http
POST /v1/candidate/register
Content-Type: application/json

{
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "password": "SecurePass123!",
  "phone": "+1234567890",
  "location": "New York, NY",
  "experience_years": 3,
  "technical_skills": "JavaScript, React, Node.js",
  "education_level": "Bachelor",
  "seniority_level": "Mid"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Registration successful",
  "candidate_id": 456
}
```

**Sequence:**
1. Check email uniqueness
2. Hash password with bcrypt
3. Insert into candidates collection with status='applied'
4. Return candidate_id

**Error Responses:**
- 409 Conflict: Email already registered

**When Called:** Candidate signs up

**Database Impact:** INSERT into candidates collection

---

### 77. POST /v1/candidate/login

**Purpose:** Candidate authentication with JWT token

**Authentication:** None (public login)

**Implementation:** `services/gateway/app/main.py` → `candidate_login()`

**Timeout:** 10s

**Request:**
```http
POST /v1/candidate/login
Content-Type: application/json

{
  "email": "jane.smith@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "candidate": {
    "id": 456,
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "phone": "+1234567890",
    "location": "New York, NY",
    "experience_years": 3,
    "technical_skills": "JavaScript, React, Node.js",
    "seniority_level": "Mid",
    "education_level": "Bachelor",
    "status": "applied"
  }
}
```

**Error Responses:**
- 401 Unauthorized: Invalid credentials

**When Called:** Candidate logs in

**Database Impact:** SELECT from candidates collection

---

### 78. PUT /v1/candidate/profile/{candidate_id}

**Purpose:** Update candidate profile

**Authentication:** Candidate JWT token required

**Implementation:** `services/gateway/app/main.py` → `update_candidate_profile()`

**Timeout:** 15s

**Request:**
```http
PUT /v1/candidate/profile/456
Content-Type: application/json
Authorization: Bearer CANDIDATE_JWT_TOKEN

{
  "phone": "+0987654321",
  "location": "San Francisco, CA",
  "experience_years": 4,
  "technical_skills": "JavaScript, React, Node.js, TypeScript"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Profile updated successfully"
}
```

**Validation:**
- Phone: E.164 format
- Experience years: Non-negative

**Error Responses:**
- 400 Bad Request: Invalid phone format
- 401 Unauthorized: Invalid token

**When Called:** Candidate updates profile

**Database Impact:** UPDATE candidates collection

---

### 79. POST /v1/candidate/apply

**Purpose:** Apply for job

**Authentication:** Candidate JWT token required

**Implementation:** `services/gateway/app/main.py` → `apply_for_job()`

**Timeout:** 20s

**Request:**
```http
POST /v1/candidate/apply
Content-Type: application/json
Authorization: Bearer CANDIDATE_JWT_TOKEN

{
  "candidate_id": 456,
  "job_id": 123,
  "cover_letter": "I am excited to apply for this position..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Application submitted successfully",
  "application_id": 789
}
```

**Sequence:**
1. Check if already applied
2. Create job_applications collection if not exists
3. Insert application with status='applied'
4. Trigger application webhook

**Error Responses:**
- 409 Conflict: Already applied
- 404 Not Found: Job not found

**When Called:** Candidate applies for job

**Database Impact:** INSERT into job_applications collection

---

### 80. GET /v1/candidate/applications/{candidate_id}

**Purpose:** Get candidate's job applications

**Authentication:** Candidate JWT token required

**Implementation:** `services/gateway/app/main.py` → `get_candidate_applications()`

**Timeout:** 15s

**Request:**
```http
GET /v1/candidate/applications/456
Authorization: Bearer CANDIDATE_JWT_TOKEN
```

**Response (200 OK):**
```json
{
  "applications": [
    {
      "id": 789,
      "job_id": 123,
      "status": "applied",
      "applied_date": "2026-01-22T13:37:00Z",
      "cover_letter": "I am excited to apply...",
      "job_title": "Senior Software Engineer",
      "department": "Engineering",
      "location": "Remote",
      "experience_level": "senior",
      "company": "Tech Innovations Inc",
      "updated_at": "2026-01-22T13:37:00Z"
    }
  ],
  "count": 1
}
```

**When Called:** Candidate views application history

**Database Impact:** SELECT from job_applications, jobs, clients collections with JOIN

---

## Summary Table - Part 4

| Endpoint | Method | Category | Purpose | Auth Required | Timeout |
|----------|--------|----------|---------|---------------|---------|
| /v1/security/rate-limit-status | GET | Security | Check rate limits | Yes | 5s |
| /v1/security/blocked-ips | GET | Security | View blocked IPs | Yes | 5s |
| /v1/security/test-input-validation | POST | Security | Input validation test | Yes | 5s |
| /v1/security/validate-email | POST | Security | Email validation | Yes | 5s |
| /v1/security/test-email-validation | POST | Security | Email validation test | Yes | 10s |
| /v1/security/validate-phone | POST | Security | Phone validation | Yes | 5s |
| /v1/security/test-phone-validation | POST | Security | Phone validation test | Yes | 10s |
| /v1/security/test-headers | GET | Security | Security headers test | Yes | 5s |
| /v1/security/security-headers-test | GET | Security | Legacy security headers | Yes | 5s |
| /v1/security/penetration-test | POST | Security | Penetration testing | Yes | 30s |
| /v1/security/test-auth | GET | Security | Authentication test | Yes | 10s |
| /v1/security/penetration-test-endpoints | GET | Security | Penetration test endpoints | Yes | 5s |
| /v1/security/csp-report | POST | CSP | Report violation | Yes | 5s |
| /v1/security/csp-violations | GET | CSP | CSP violations | Yes | 10s |
| /v1/security/csp-policies | GET | CSP | CSP policies | Yes | 5s |
| /v1/security/test-csp-policy | POST | CSP | CSP policy test | Yes | 10s |
| /v1/auth/2fa/setup | POST | 2FA | 2FA setup | Yes | 30s |
| /v1/auth/2fa/verify | POST | 2FA | 2FA verification | Yes | 10s |
| /v1/auth/2fa/login | POST | 2FA | 2FA login | No | 15s |
| /v1/auth/2fa/status/{user_id} | GET | 2FA | 2FA status | Yes | 5s |
| /v1/auth/2fa/disable | POST | 2FA | Disable 2FA | Yes | 10s |
| /v1/auth/2fa/backup-codes | POST | 2FA | 2FA backup codes | Yes | 15s |
| /v1/auth/2fa/test-token | POST | 2FA | Test 2FA token | Yes | 5s |
| /v1/auth/2fa/qr/{user_id} | GET | 2FA | Get 2FA QR code | Yes | 10s |
| /v1/auth/password/validate | POST | Password | Validate password | Yes | 5s |
| /v1/auth/password/generate | GET | Password | Generate password | Yes | 5s |
| /v1/auth/password/policy | GET | Password | Get password policy | Yes | 5s |
| /v1/auth/password/change | POST | Password | Change password | Yes | 10s |
| /v1/auth/password/strength | POST | Password | Password strength test | Yes | 5s |
| /v1/auth/password/security-tips | GET | Password | Security tips | Yes | 5s |
| /v1/candidate/register | POST | Candidate | Register | No | 15s |
| /v1/candidate/login | POST | Candidate | Login | No | 10s |
| /v1/candidate/profile/{id} | PUT | Candidate | Update profile | Yes | 15s |
| /v1/candidate/apply | POST | Candidate | Apply for job | Yes | 20s |
| /v1/candidate/applications/{id} | GET | Candidate | Get applications | Yes | 15s |

**Total Endpoints in Part 4:** 35 (46-80 of 111)

---

**Continue to:** [API_CONTRACT_PART5.md](./API_CONTRACT_PART5.md) for AI Agent & LangGraph Services