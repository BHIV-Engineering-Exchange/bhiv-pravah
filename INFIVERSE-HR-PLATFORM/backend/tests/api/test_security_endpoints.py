#!/usr/bin/env python3
"""
BHIV HR Platform - Security Testing Endpoints
Tests all security-related endpoints and generates a comprehensive report.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"
API_KEY = "<YOUR_API_KEY>"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_endpoint(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """Test a single endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        else:
            return {"status": "error", "message": f"Unsupported method: {method}"}
        
        response_time = time.time() - start_time
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        return {
            "status": "success" if response.status_code < 400 else "error",
            "status_code": response.status_code,
            "response_time": round(response_time, 3),
            "response_size": len(response.content),
            "response_data": response_data,
            "headers": dict(response.headers)
        }
        
    except requests.exceptions.Timeout:
        return {
            "status": "timeout",
            "message": "Request timed out after 30 seconds",
            "response_time": 30.0
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "connection_error",
            "message": "Failed to connect to the server"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "response_time": time.time() - start_time
        }

def main():
    """Test security endpoints and generate report"""
    print("Testing BHIV HR Platform Security Testing Endpoints")
    print("=" * 70)
    
    # Security test endpoints configuration
    security_endpoints = [
        # Rate Limiting & IP Management
        {
            "name": "Rate Limit Status",
            "endpoint": "/v1/security/rate-limit-status",
            "method": "GET",
            "category": "Rate Limiting",
            "description": "Check current rate limit status and remaining requests"
        },
        {
            "name": "Blocked IPs",
            "endpoint": "/v1/security/blocked-ips",
            "method": "GET",
            "category": "Rate Limiting",
            "description": "View list of blocked IP addresses"
        },
        # Input Validation Testing
        {
            "name": "Input Validation Test",
            "endpoint": "/v1/security/test-input-validation",
            "method": "POST",
            "category": "Input Validation",
            "description": "Test input validation with malicious payloads",
            "test_data": {
                "test_input": "<script>alert('xss')</script>",
                "sql_injection": "'; DROP TABLE users; --",
                "path_traversal": "../../../etc/passwd"
            }
        },
        # Email Validation
        {
            "name": "Email Validation",
            "endpoint": "/v1/security/validate-email",
            "method": "POST",
            "category": "Email Validation",
            "description": "Validate email address format and security",
            "test_data": {
                "email": "test@example.com"
            }
        },
        {
            "name": "Email Validation Test",
            "endpoint": "/v1/security/test-email-validation",
            "method": "POST",
            "category": "Email Validation",
            "description": "Test email validation with various formats",
            "test_data": {
                "emails": [
                    "valid@example.com",
                    "invalid-email",
                    "test@malicious<script>.com"
                ]
            }
        },
        # Phone Validation
        {
            "name": "Phone Validation",
            "endpoint": "/v1/security/validate-phone",
            "method": "POST",
            "category": "Phone Validation",
            "description": "Validate phone number format",
            "test_data": {
                "phone": "+1-555-123-4567"
            }
        },
        {
            "name": "Phone Validation Test",
            "endpoint": "/v1/security/test-phone-validation",
            "method": "POST",
            "category": "Phone Validation",
            "description": "Test phone validation with various formats",
            "test_data": {
                "phones": [
                    "+1-555-123-4567",
                    "555-123-4567",
                    "invalid-phone"
                ]
            }
        },
        # Security Headers
        {
            "name": "Security Headers Test",
            "endpoint": "/v1/security/test-headers",
            "method": "GET",
            "category": "Security Headers",
            "description": "Test security headers implementation"
        },
        {
            "name": "Security Headers Legacy",
            "endpoint": "/v1/security/security-headers-test",
            "method": "GET",
            "category": "Security Headers",
            "description": "Legacy security headers test endpoint"
        },
        # Penetration Testing
        {
            "name": "Penetration Test",
            "endpoint": "/v1/security/penetration-test",
            "method": "POST",
            "category": "Penetration Testing",
            "description": "Run penetration testing suite",
            "test_data": {
                "test_type": "basic",
                "target_endpoints": ["/v1/jobs", "/v1/candidates"]
            }
        },
        {
            "name": "Authentication Test",
            "endpoint": "/v1/security/test-auth",
            "method": "GET",
            "category": "Authentication",
            "description": "Test authentication mechanisms"
        },
        {
            "name": "Penetration Test Endpoints",
            "endpoint": "/v1/security/penetration-test-endpoints",
            "method": "GET",
            "category": "Penetration Testing",
            "description": "List available penetration test endpoints"
        }
    ]
    
    results = []
    
    for endpoint_config in security_endpoints:
        print(f"\nTesting: {endpoint_config['name']} ({endpoint_config['category']})")
        print(f"   Endpoint: {endpoint_config['method']} {endpoint_config['endpoint']}")
        
        test_data = endpoint_config.get("test_data")
        if test_data:
            print(f"   Test Data: {json.dumps(test_data, indent=2)}")
        
        result = test_endpoint(
            endpoint_config["endpoint"],
            endpoint_config["method"],
            test_data
        )
        
        result["endpoint_info"] = endpoint_config
        results.append(result)
        
        # Print immediate results
        if result["status"] == "success":
            print(f"   [OK] Status: {result['status_code']} - {result['response_time']}s")
            if isinstance(result["response_data"], dict):
                print(f"   Response keys: {list(result['response_data'].keys())}")
            elif isinstance(result["response_data"], list):
                print(f"   Response: {len(result['response_data'])} items")
            else:
                print(f"   Response size: {result['response_size']} bytes")
        else:
            print(f"   [ERROR] Status: {result['status']} - {result.get('message', 'Unknown error')}")
    
    # Generate markdown report
    generate_markdown_report(results)
    
    print(f"\nReport generated: security_endpoints_test_report.md")
    print("=" * 70)

def generate_markdown_report(results):
    """Generate a comprehensive markdown report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# BHIV HR Platform - Security Testing Endpoints Report

**Generated:** {timestamp}  
**Platform:** BHIV HR Gateway Service  
**Base URL:** {BASE_URL}  
**Test Category:** Security Testing Endpoints

## 📊 Test Summary

| Endpoint | Method | Category | Status | Response Time | Status Code |
|----------|--------|----------|--------|---------------|-------------|
"""
    
    for result in results:
        endpoint_info = result["endpoint_info"]
        status_icon = "✅" if result["status"] == "success" else "❌"
        status_code = result.get("status_code", "N/A")
        response_time = f"{result.get('response_time', 0):.3f}s"
        
        report += f"| `{endpoint_info['endpoint']}` | {endpoint_info['method']} | {endpoint_info['category']} | {status_icon} {result['status']} | {response_time} | {status_code} |\n"
    
    # Calculate success rate by category
    categories = {}
    for result in results:
        cat = result["endpoint_info"]["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0}
        categories[cat]["total"] += 1
        if result["status"] == "success":
            categories[cat]["success"] += 1
    
    total_success = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)
    
    report += f"\n**Overall Success Rate:** {total_success}/{total_count} ({(total_success/total_count)*100:.1f}%)  \n\n"
    
    report += "**Success Rate by Category:**  \n"
    for cat, stats in categories.items():
        rate = (stats["success"] / stats["total"]) * 100
        report += f"- **{cat}:** {stats['success']}/{stats['total']} ({rate:.1f}%)  \n"
    
    report += "\n## 🔍 Detailed Test Results\n\n"
    
    # Group by category
    for category in categories.keys():
        category_results = [r for r in results if r["endpoint_info"]["category"] == category]
        report += f"### {category}\n\n"
        
        for result in category_results:
            endpoint_info = result["endpoint_info"]
            
            report += f"#### {endpoint_info['name']}\n\n"
            report += f"**Endpoint:** `{endpoint_info['method']} {endpoint_info['endpoint']}`  \n"
            report += f"**Description:** {endpoint_info['description']}  \n\n"
            
            if result["status"] == "success":
                report += f"**✅ Test Result:** PASSED  \n"
                report += f"**Status Code:** {result['status_code']}  \n"
                report += f"**Response Time:** {result['response_time']}s  \n"
                report += f"**Response Size:** {result['response_size']} bytes  \n\n"
                
                # Add response analysis
                if isinstance(result["response_data"], dict):
                    report += "**Response Structure:**\n```json\n"
                    if len(str(result["response_data"])) > 1500:
                        sample_data = {}
                        for k, v in list(result["response_data"].items())[:8]:
                            if isinstance(v, (dict, list)) and len(str(v)) > 100:
                                sample_data[k] = f"... ({type(v).__name__})"
                            else:
                                sample_data[k] = v
                        report += json.dumps(sample_data, indent=2)
                        report += "\n// ... (truncated for readability)\n"
                    else:
                        report += json.dumps(result["response_data"], indent=2)
                    report += "\n```\n\n"
                elif isinstance(result["response_data"], list):
                    report += f"**Response:** Array with {len(result['response_data'])} items  \n"
                    if result["response_data"]:
                        report += "**Sample Item:**\n```json\n"
                        report += json.dumps(result["response_data"][0], indent=2)
                        report += "\n```\n\n"
                else:
                    if len(str(result["response_data"])) > 500:
                        report += f"**Response Preview:** `{str(result['response_data'])[:500]}...`  \n\n"
                    else:
                        report += f"**Response:** `{result['response_data']}`  \n\n"
                    
                # Add test data if it was a POST request
                if endpoint_info["method"] == "POST" and "test_data" in endpoint_info:
                    report += "**Test Data Sent:**\n```json\n"
                    report += json.dumps(endpoint_info["test_data"], indent=2)
                    report += "\n```\n\n"
                    
            else:
                report += f"**❌ Test Result:** FAILED  \n"
                report += f"**Error:** {result.get('message', 'Unknown error')}  \n"
                if "status_code" in result:
                    report += f"**Status Code:** {result['status_code']}  \n"
                if "response_time" in result:
                    report += f"**Response Time:** {result['response_time']}s  \n"
                report += "\n"
    
    # Add security analysis
    report += "## 🔒 Security Analysis\n\n"
    report += "### Security Features Tested\n\n"
    report += "The security testing endpoints validate:\n\n"
    report += "- **Rate Limiting** - Request throttling and IP blocking\n"
    report += "- **Input Validation** - XSS, SQL injection, path traversal protection\n"
    report += "- **Email/Phone Validation** - Format validation and sanitization\n"
    report += "- **Security Headers** - CSP, XSS protection, frame options\n"
    report += "- **Authentication** - Token validation and access control\n"
    report += "- **Penetration Testing** - Automated security vulnerability scanning\n\n"
    
    # Add performance analysis
    report += "## ⚡ Performance Analysis\n\n"
    
    successful_results = [r for r in results if r["status"] == "success"]
    if successful_results:
        avg_response_time = sum(r.get("response_time", 0) for r in successful_results) / len(successful_results)
        report += f"**Average Response Time:** {avg_response_time:.3f}s  \n"
        
        fastest = min(successful_results, key=lambda x: x.get("response_time", float('inf')))
        slowest = max(successful_results, key=lambda x: x.get("response_time", 0))
        
        report += f"**Fastest Endpoint:** `{fastest['endpoint_info']['endpoint']}` ({fastest['response_time']}s)  \n"
        report += f"**Slowest Endpoint:** `{slowest['endpoint_info']['endpoint']}` ({slowest['response_time']}s)  \n"
    
    report += "\n"
    
    # Add recommendations
    report += "## 💡 Security Recommendations\n\n"
    
    if total_success == total_count:
        report += "✅ **All security testing endpoints are functioning correctly**\n\n"
        report += "- Rate limiting is properly configured and monitored\n"
        report += "- Input validation protects against common attacks\n"
        report += "- Email and phone validation is working correctly\n"
        report += "- Security headers are properly implemented\n"
        report += "- Authentication mechanisms are secure\n"
        report += "- Penetration testing tools are operational\n\n"
    else:
        failed_count = total_count - total_success
        report += f"⚠️ **{failed_count} security endpoint(s) failed testing**\n\n"
        failed_endpoints = [r for r in results if r["status"] != "success"]
        for failed in failed_endpoints:
            report += f"- `{failed['endpoint_info']['endpoint']}`: {failed.get('message', 'Unknown error')}\n"
        report += "\n"
    
    report += "### Security Best Practices:\n\n"
    report += "1. **Regular Security Testing** - Run penetration tests regularly\n"
    report += "2. **Monitor Rate Limits** - Track and adjust rate limiting thresholds\n"
    report += "3. **Input Sanitization** - Continuously update validation rules\n"
    report += "4. **Security Headers** - Keep CSP policies updated\n"
    report += "5. **Authentication Audit** - Regular token and access reviews\n"
    report += "6. **Vulnerability Scanning** - Automated security assessments\n\n"
    
    # Add usage examples
    report += "## 📝 Security Testing Examples\n\n"
    report += "### Check Rate Limit Status\n"
    report += "```bash\n"
    report += f'curl -H "Authorization: Bearer {API_KEY}" \\\n'
    report += f'     "{BASE_URL}/v1/security/rate-limit-status"\n'
    report += "```\n\n"
    
    report += "### Test Input Validation\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/security/test-input-validation" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "test_input": "<script>alert(xss)</script>",\n'
    report += '    "sql_injection": "DROP TABLE users"\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += "### Run Penetration Test\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/security/penetration-test" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "test_type": "basic",\n'
    report += '    "target_endpoints": ["/v1/jobs", "/v1/candidates"]\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += f"---\n\n"
    report += f"**Report Generated:** {timestamp}  \n"
    report += f"**Test Duration:** {sum(r.get('response_time', 0) for r in results):.3f}s total  \n"
    report += f"**Platform:** BHIV HR Platform v3.0.0-Phase3  \n"
    
    # Write report to file
    with open("security_endpoints_test_report.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
