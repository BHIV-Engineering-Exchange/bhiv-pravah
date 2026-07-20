# 🚨 Failure Observability Scenarios

This document details the failure scenarios evaluated for the BHIV HR platform to confirm error context capturing and resilience.

## Scenario 1: Weak Password Policy Rejection
- **Trigger**: Submission of a weak password (`"123"`) to `/v1/auth/password/validate`.
- **Expected Error**: `400 Bad Request` or validation object with `is_valid: false`.
- **Observed Diagnostics**: The system returns structural feedback lists specifying missing uppercase, lowercase, special characters, and length requirements.

## Scenario 2: XSS Injection Blocking
- **Trigger**: Post a payload containing HTML scripts to `/v1/security/test-input-validation`.
- **Expected Error**: The firewall middleware flags threat vectors.
- **Observed Diagnostics**: System responds with `validation_result: "BLOCKED"` and logs `["XSS attempt detected"]`.

## Scenario 3: Incorrect 2FA Verification
- **Trigger**: Submit code `999999` to `/v1/auth/2fa/verify`.
- **Expected Error**: `401 Unauthorized`.
- **Observed Diagnostics**: HTTP 401 returned with detail: `Invalid 2FA code`.

## Scenario 4: Query Non-Existent Resource
- **Trigger**: GET request for invalid Job ID.
- **Expected Error**: `404 Not Found`.
- **Observed Diagnostics**: HTTP 404 response with `detail: "Job not found"` or similar, letting the application handle missing data gracefully.
