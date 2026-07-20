#!/usr/bin/env python3
"""
BHIV HR Platform - CSP Management Endpoints Testing
Tests all CSP-related endpoints and generates a comprehensive report.
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
    """Test CSP management endpoints and generate report"""
    print("Testing BHIV HR Platform CSP Management Endpoints")
    print("=" * 65)
    
    # CSP endpoints configuration
    csp_endpoints = [
        # CSP Violation Reporting
        {
            "name": "CSP Violation Report",
            "endpoint": "/v1/security/csp-report",
            "method": "POST",
            "category": "Violation Reporting",
            "description": "Report CSP violations for security monitoring",
            "test_data": {
                "csp-report": {
                    "document-uri": "https://example.com/page",
                    "referrer": "https://example.com/",
                    "violated-directive": "script-src 'self'",
                    "effective-directive": "script-src",
                    "original-policy": "default-src 'self'; script-src 'self'",
                    "blocked-uri": "https://malicious.com/script.js",
                    "status-code": 200
                }
            }
        },
        {
            "name": "View CSP Violations",
            "endpoint": "/v1/security/csp-violations",
            "method": "GET",
            "category": "Violation Reporting",
            "description": "View recorded CSP violations"
        },
        # CSP Policies Management
        {
            "name": "Get CSP Policies",
            "endpoint": "/v1/csp/policies",
            "method": "GET",
            "category": "Policy Management",
            "description": "Retrieve current CSP policies"
        },
        {
            "name": "Get CSP Violations (Alt)",
            "endpoint": "/v1/csp/violations",
            "method": "GET",
            "category": "Policy Management",
            "description": "Alternative endpoint for CSP violations"
        },
        {
            "name": "CSP Report (Alt)",
            "endpoint": "/v1/csp/report",
            "method": "POST",
            "category": "Policy Management",
            "description": "Alternative CSP violation reporting endpoint",
            "test_data": {
                "violation_type": "script-src",
                "blocked_uri": "https://untrusted.com/script.js",
                "document_uri": "https://example.com/test",
                "line_number": 42,
                "column_number": 15
            }
        },
        {
            "name": "Test CSP",
            "endpoint": "/v1/csp/test",
            "method": "GET",
            "category": "Policy Management",
            "description": "Test CSP policy implementation"
        },
        # Security CSP Management
        {
            "name": "Current CSP Policies",
            "endpoint": "/v1/security/csp-policies",
            "method": "GET",
            "category": "Security Management",
            "description": "Get current CSP policies from security module"
        },
        {
            "name": "Test CSP Policy",
            "endpoint": "/v1/security/test-csp-policy",
            "method": "POST",
            "category": "Security Management",
            "description": "Test CSP policy configuration",
            "test_data": {
                "policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
                "test_url": "https://example.com/test",
                "expected_violations": ["script-src"]
            }
        }
    ]
    
    results = []
    
    for endpoint_config in csp_endpoints:
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
    
    print(f"\nReport generated: csp_endpoints_test_report.md")
    print("=" * 65)

def generate_markdown_report(results):
    """Generate a comprehensive markdown report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# BHIV HR Platform - CSP Management Endpoints Test Report

**Generated:** {timestamp}  
**Platform:** BHIV HR Gateway Service  
**Base URL:** {BASE_URL}  
**Test Category:** CSP (Content Security Policy) Management

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
    
    # Add CSP analysis
    report += "## 🛡️ CSP Security Analysis\n\n"
    report += "### Content Security Policy Features\n\n"
    report += "The CSP management system provides:\n\n"
    report += "- **Violation Reporting** - Real-time CSP violation tracking\n"
    report += "- **Policy Management** - Dynamic CSP policy configuration\n"
    report += "- **Security Monitoring** - Comprehensive violation analysis\n"
    report += "- **Testing Framework** - CSP policy validation tools\n"
    report += "- **Multiple Endpoints** - Redundant CSP management interfaces\n\n"
    
    report += "### CSP Implementation Benefits:\n\n"
    report += "1. **XSS Protection** - Prevents cross-site scripting attacks\n"
    report += "2. **Data Injection Defense** - Blocks malicious content injection\n"
    report += "3. **Clickjacking Prevention** - Frame-ancestors directive protection\n"
    report += "4. **Mixed Content Security** - HTTPS enforcement\n"
    report += "5. **Resource Control** - Whitelist-based resource loading\n\n"
    
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
    report += "## 💡 CSP Management Recommendations\n\n"
    
    if total_success == total_count:
        report += "✅ **All CSP management endpoints are functioning correctly**\n\n"
        report += "- CSP violation reporting is operational\n"
        report += "- Policy management system is working\n"
        report += "- Security monitoring is active\n"
        report += "- Testing framework is available\n"
        report += "- Multiple management interfaces provide redundancy\n\n"
    else:
        failed_count = total_count - total_success
        report += f"⚠️ **{failed_count} CSP endpoint(s) failed testing**\n\n"
        failed_endpoints = [r for r in results if r["status"] != "success"]
        for failed in failed_endpoints:
            report += f"- `{failed['endpoint_info']['endpoint']}`: {failed.get('message', 'Unknown error')}\n"
        report += "\n"
    
    report += "### CSP Best Practices:\n\n"
    report += "1. **Regular Policy Review** - Update CSP policies based on violations\n"
    report += "2. **Violation Monitoring** - Actively monitor and analyze CSP reports\n"
    report += "3. **Gradual Enforcement** - Start with report-only mode before enforcement\n"
    report += "4. **Nonce Implementation** - Use nonces for inline scripts when necessary\n"
    report += "5. **Policy Testing** - Test CSP changes in staging environment\n"
    report += "6. **Performance Impact** - Monitor CSP overhead on page load times\n\n"
    
    # Add usage examples
    report += "## 📝 CSP Management Examples\n\n"
    report += "### View Current CSP Policies\n"
    report += "```bash\n"
    report += f'curl -H "Authorization: Bearer {API_KEY}" \\\n'
    report += f'     "{BASE_URL}/v1/csp/policies"\n'
    report += "```\n\n"
    
    report += "### Report CSP Violation\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/security/csp-report" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "csp-report": {\n'
    report += '      "document-uri": "https://example.com/page",\n'
    report += '      "violated-directive": "script-src self",\n'
    report += '      "blocked-uri": "https://malicious.com/script.js"\n'
    report += '    }\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += "### Test CSP Policy\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/security/test-csp-policy" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "policy": "default-src self; script-src self unsafe-inline",\n'
    report += '    "test_url": "https://example.com/test"\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += f"---\n\n"
    report += f"**Report Generated:** {timestamp}  \n"
    report += f"**Test Duration:** {sum(r.get('response_time', 0) for r in results):.3f}s total  \n"
    report += f"**Platform:** BHIV HR Platform v3.0.0-Phase3  \n"
    
    # Write report to file
    with open("csp_endpoints_test_report.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
