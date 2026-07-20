#!/usr/bin/env python3
"""
Gateway Service Endpoint Analysis
Analyzes the live Gateway service endpoints and identifies issues
"""

# Live Gateway Endpoints from API Documentation
LIVE_GATEWAY_ENDPOINTS = {
    "Authentication": [
        "POST /auth/2fa/setup",
        "POST /auth/2fa/verify", 
        "POST /auth/login",
        "GET /auth/2fa/status/{user_id}"
    ],
    "LangGraph Workflows": [
        "POST /api/v1/workflow/trigger",
        "GET /api/v1/workflow/status/{workflow_id}",
        "GET /api/v1/workflow/list",
        "GET /api/v1/workflow/health",
        "POST /api/v1/webhooks/candidate-applied",
        "POST /api/v1/webhooks/candidate-shortlisted",
        "POST /api/v1/webhooks/interview-scheduled"
    ],
    "Monitoring": [
        "GET /metrics",
        "GET /health/detailed",
        "GET /metrics/dashboard"
    ],
    "Core API Endpoints": [
        "GET /",
        "GET /health",
        "GET /test-candidates"
    ],
    "Job Management": [
        "GET /v1/jobs",
        "POST /v1/jobs"
    ],
    "Candidate Management": [
        "GET /v1/candidates",
        "GET /v1/candidates/search",
        "GET /v1/candidates/job/{job_id}",
        "GET /v1/candidates/{candidate_id}",
        "POST /v1/candidates/bulk"
    ],
    "AI Matching Engine": [
        "GET /v1/match/{job_id}/top",
        "POST /v1/match/batch"
    ],
    "Assessment & Workflow": [
        "GET /v1/feedback",
        "POST /v1/feedback",
        "GET /v1/interviews",
        "POST /v1/interviews",
        "GET /v1/offers",
        "POST /v1/offers"
    ],
    "Analytics & Statistics": [
        "GET /candidates/stats",
        "GET /v1/database/schema",
        "GET /v1/reports/job/{job_id}/export.csv"
    ],
    "Client Portal API": [
        "POST /v1/client/register",
        "POST /v1/client/login"
    ],
    "Security Testing": [
        "GET /v1/security/rate-limit-status",
        "GET /v1/security/blocked-ips",
        "POST /v1/security/test-input-validation",
        "POST /v1/security/validate-email",
        "POST /v1/security/test-email-validation",
        "POST /v1/security/validate-phone",
        "POST /v1/security/test-phone-validation",
        "GET /v1/security/test-headers",
        "GET /v1/security/security-headers-test",
        "POST /v1/security/penetration-test",
        "GET /v1/security/test-auth",
        "GET /v1/security/penetration-test-endpoints"
    ],
    "CSP Management": [
        "POST /v1/security/csp-report",
        "GET /v1/security/csp-violations",
        "GET /v1/csp/policies",
        "GET /v1/csp/violations",
        "POST /v1/csp/report",
        "GET /v1/csp/test",
        "GET /v1/security/csp-policies",
        "POST /v1/security/test-csp-policy"
    ],
    "Two-Factor Authentication": [
        "POST /v1/auth/2fa/setup",
        "POST /v1/auth/2fa/verify",
        "POST /v1/auth/2fa/login",
        "GET /v1/auth/2fa/status/{user_id}",
        "POST /v1/auth/2fa/disable",
        "POST /v1/auth/2fa/backup-codes",
        "POST /v1/auth/2fa/test-token",
        "GET /v1/auth/2fa/qr/{user_id}",
        "POST /v1/2fa/setup",
        "POST /v1/2fa/verify-setup",
        "POST /v1/2fa/login-with-2fa",
        "GET /v1/2fa/status/{client_id}",
        "POST /v1/2fa/disable",
        "POST /v1/2fa/regenerate-backup-codes",
        "GET /v1/2fa/test-token/{client_id}/{token}",
        "GET /v1/2fa/demo-setup"
    ],
    "Password Management": [
        "POST /v1/auth/password/validate",
        "GET /v1/auth/password/generate",
        "GET /v1/auth/password/policy",
        "POST /v1/auth/password/change",
        "POST /v1/auth/password/strength",
        "GET /v1/auth/password/security-tips",
        "POST /v1/password/validate",
        "POST /v1/password/generate",
        "GET /v1/password/policy",
        "POST /v1/password/change",
        "GET /v1/password/strength-test",
        "GET /v1/password/security-tips"
    ],
    "Candidate Portal": [
        "POST /v1/candidate/register",
        "POST /v1/candidate/login",
        "PUT /v1/candidate/profile/{candidate_id}",
        "POST /v1/candidate/apply",
        "GET /v1/candidate/applications/{candidate_id}"
    ]
}

def analyze_gateway_endpoints():
    """Analyze Gateway endpoints and identify issues"""
    
    print("GATEWAY SERVICE ENDPOINT ANALYSIS")
    print("=" * 50)
    
    # Count total endpoints
    total_endpoints = sum(len(endpoints) for endpoints in LIVE_GATEWAY_ENDPOINTS.values())
    documented_count = 94
    
    print(f"ENDPOINT COUNT ANALYSIS:")
    print(f"   Live Endpoints Found: {total_endpoints}")
    print(f"   Documented Count: {documented_count}")
    print(f"   Discrepancy: {total_endpoints - documented_count}")
    
    if total_endpoints != documented_count:
        print(f"[ERROR] CRITICAL: Endpoint count mismatch!")
    else:
        print(f"[OK] Endpoint count matches documentation")
    
    print(f"\nENDPOINT BREAKDOWN BY CATEGORY:")
    for category, endpoints in LIVE_GATEWAY_ENDPOINTS.items():
        print(f"   {category}: {len(endpoints)} endpoints")
    
    # Identify issues
    print(f"\nIDENTIFIED ISSUES:")
    
    issues = []
    
    # 1. Duplicate 2FA endpoints
    auth_endpoints = LIVE_GATEWAY_ENDPOINTS["Authentication"]
    tfa_endpoints = LIVE_GATEWAY_ENDPOINTS["Two-Factor Authentication"]
    
    duplicate_2fa = []
    for auth_ep in auth_endpoints:
        for tfa_ep in tfa_endpoints:
            if auth_ep.split()[-1] in tfa_ep and "2fa" in auth_ep.lower():
                duplicate_2fa.append((auth_ep, tfa_ep))
    
    if duplicate_2fa:
        issues.append("DUPLICATE_2FA_ENDPOINTS")
        print(f"   [ERROR] Duplicate 2FA endpoints detected:")
        for auth, tfa in duplicate_2fa:
            print(f"      - {auth} vs {tfa}")
    
    # 2. Duplicate password endpoints
    password_endpoints = LIVE_GATEWAY_ENDPOINTS["Password Management"]
    auth_password_count = sum(1 for ep in password_endpoints if "/auth/password/" in ep)
    regular_password_count = sum(1 for ep in password_endpoints if "/password/" in ep and "/auth/password/" not in ep)
    
    if auth_password_count > 0 and regular_password_count > 0:
        issues.append("DUPLICATE_PASSWORD_ENDPOINTS")
        print(f"   [ERROR] Duplicate password management endpoints:")
        print(f"      - Auth-based: {auth_password_count} endpoints")
        print(f"      - Regular: {regular_password_count} endpoints")
    
    # 3. Security testing endpoints in production
    security_test_endpoints = LIVE_GATEWAY_ENDPOINTS["Security Testing"]
    if len(security_test_endpoints) > 5:
        issues.append("EXCESSIVE_SECURITY_TEST_ENDPOINTS")
        print(f"   [WARNING] Excessive security testing endpoints in production: {len(security_test_endpoints)}")
    
    # 4. CSP endpoint duplication
    csp_endpoints = LIVE_GATEWAY_ENDPOINTS["CSP Management"]
    csp_duplicates = []
    for i, ep1 in enumerate(csp_endpoints):
        for ep2 in csp_endpoints[i+1:]:
            if ep1.split()[-1].split('/')[-1] == ep2.split()[-1].split('/')[-1]:
                csp_duplicates.append((ep1, ep2))
    
    if csp_duplicates:
        issues.append("DUPLICATE_CSP_ENDPOINTS")
        print(f"   [ERROR] Duplicate CSP endpoints:")
        for ep1, ep2 in csp_duplicates:
            print(f"      - {ep1} vs {ep2}")
    
    # 5. Missing core endpoints
    core_endpoints = LIVE_GATEWAY_ENDPOINTS["Core API Endpoints"]
    expected_core = ["GET /", "GET /health", "GET /openapi.json", "GET /docs"]
    missing_core = []
    
    for expected in expected_core:
        found = any(expected.split()[-1] in ep for ep in core_endpoints)
        if not found:
            missing_core.append(expected)
    
    if missing_core:
        issues.append("MISSING_CORE_ENDPOINTS")
        print(f"   [WARNING] Missing expected core endpoints: {missing_core}")
    
    # 6. Inconsistent versioning
    v1_endpoints = sum(1 for category in LIVE_GATEWAY_ENDPOINTS.values() 
                      for ep in category if "/v1/" in ep)
    non_v1_endpoints = total_endpoints - v1_endpoints
    
    if non_v1_endpoints > 10:  # Allow some core endpoints without versioning
        issues.append("INCONSISTENT_VERSIONING")
        print(f"   [WARNING] Inconsistent API versioning: {non_v1_endpoints} endpoints without /v1/")
    
    # Summary
    print(f"\nANALYSIS SUMMARY:")
    print(f"   Total Issues Found: {len(issues)}")
    print(f"   Issue Types: {', '.join(issues) if issues else 'None'}")
    
    if not issues:
        print(f"   [OK] No major structural issues detected")
    else:
        print(f"   [ERROR] Issues require attention for production optimization")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    if "DUPLICATE_2FA_ENDPOINTS" in issues:
        print(f"   1. Consolidate 2FA endpoints - remove duplicates")
    if "DUPLICATE_PASSWORD_ENDPOINTS" in issues:
        print(f"   2. Standardize password management endpoints")
    if "EXCESSIVE_SECURITY_TEST_ENDPOINTS" in issues:
        print(f"   3. Move security testing endpoints to development environment")
    if "DUPLICATE_CSP_ENDPOINTS" in issues:
        print(f"   4. Remove duplicate CSP management endpoints")
    if "INCONSISTENT_VERSIONING" in issues:
        print(f"   5. Implement consistent API versioning strategy")
    
    return {
        "total_endpoints": total_endpoints,
        "documented_count": documented_count,
        "discrepancy": total_endpoints - documented_count,
        "issues": issues,
        "categories": {cat: len(eps) for cat, eps in LIVE_GATEWAY_ENDPOINTS.items()}
    }

if __name__ == "__main__":
    result = analyze_gateway_endpoints()
    print(f"\n[COMPLETE] Analysis complete. Found {result['total_endpoints']} endpoints with {len(result['issues'])} issues.")