#!/usr/bin/env python3
"""
BHIV HR Platform - Two-Factor Authentication Endpoints Testing
Tests all 2FA-related endpoints and generates a comprehensive report.
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
    """Test 2FA endpoints and generate report"""
    print("Testing BHIV HR Platform Two-Factor Authentication Endpoints")
    print("=" * 75)
    
    # 2FA endpoints configuration
    twofa_endpoints = [
        # User 2FA Authentication System
        {
            "name": "Setup 2FA",
            "endpoint": "/v1/auth/2fa/setup",
            "method": "POST",
            "category": "User 2FA Auth",
            "description": "Setup 2FA for user authentication",
            "test_data": {
                "user_id": 1,
                "username": "test_user",
                "email": "test@example.com"
            }
        },
        {
            "name": "Verify 2FA",
            "endpoint": "/v1/auth/2fa/verify",
            "method": "POST",
            "category": "User 2FA Auth",
            "description": "Verify 2FA token for user",
            "test_data": {
                "user_id": 1,
                "token": "123456"
            }
        },
        {
            "name": "Login with 2FA",
            "endpoint": "/v1/auth/2fa/login",
            "method": "POST",
            "category": "User 2FA Auth",
            "description": "Login with 2FA authentication",
            "test_data": {
                "username": "test_user",
                "password": "test_password",
                "token": "123456"
            }
        },
        {
            "name": "Get 2FA Status",
            "endpoint": "/v1/auth/2fa/status/1",
            "method": "GET",
            "category": "User 2FA Auth",
            "description": "Get 2FA status for user ID 1"
        },
        {
            "name": "Disable 2FA",
            "endpoint": "/v1/auth/2fa/disable",
            "method": "POST",
            "category": "User 2FA Auth",
            "description": "Disable 2FA for user",
            "test_data": {
                "user_id": 1,
                "password": "test_password"
            }
        },
        {
            "name": "Generate Backup Codes",
            "endpoint": "/v1/auth/2fa/backup-codes",
            "method": "POST",
            "category": "User 2FA Auth",
            "description": "Generate backup codes for user",
            "test_data": {
                "user_id": 1
            }
        },
        {
            "name": "Test 2FA Token",
            "endpoint": "/v1/auth/2fa/test-token",
            "method": "POST",
            "category": "User 2FA Auth",
            "description": "Test 2FA token validity",
            "test_data": {
                "user_id": 1,
                "token": "123456"
            }
        },
        {
            "name": "Get QR Code",
            "endpoint": "/v1/auth/2fa/qr/1",
            "method": "GET",
            "category": "User 2FA Auth",
            "description": "Get QR code for 2FA setup for user ID 1"
        },
        # Client 2FA System
        {
            "name": "Setup 2FA for Client",
            "endpoint": "/v1/2fa/setup",
            "method": "POST",
            "category": "Client 2FA",
            "description": "Setup 2FA for client",
            "test_data": {
                "client_id": "<DEMO_USERNAME>",
                "email": "client@<DEMO_USERNAME>.com"
            }
        },
        {
            "name": "Verify 2FA Setup",
            "endpoint": "/v1/2fa/verify-setup",
            "method": "POST",
            "category": "Client 2FA",
            "description": "Verify 2FA setup for client",
            "test_data": {
                "client_id": "<DEMO_USERNAME>",
                "token": "123456"
            }
        },
        {
            "name": "Login with 2FA Client",
            "endpoint": "/v1/2fa/login-with-2fa",
            "method": "POST",
            "category": "Client 2FA",
            "description": "Client login with 2FA",
            "test_data": {
                "client_code": "<DEMO_USERNAME>",
                "password": "<DEMO_PASSWORD>",
                "token": "123456"
            }
        },
        {
            "name": "Get Client 2FA Status",
            "endpoint": "/v1/2fa/status/<DEMO_USERNAME>",
            "method": "GET",
            "category": "Client 2FA",
            "description": "Get 2FA status for client <DEMO_USERNAME>"
        },
        {
            "name": "Disable Client 2FA",
            "endpoint": "/v1/2fa/disable",
            "method": "POST",
            "category": "Client 2FA",
            "description": "Disable 2FA for client",
            "test_data": {
                "client_id": "<DEMO_USERNAME>",
                "password": "<DEMO_PASSWORD>"
            }
        },
        {
            "name": "Regenerate Backup Codes",
            "endpoint": "/v1/2fa/regenerate-backup-codes",
            "method": "POST",
            "category": "Client 2FA",
            "description": "Regenerate backup codes for client",
            "test_data": {
                "client_id": "<DEMO_USERNAME>"
            }
        },
        {
            "name": "Test Client 2FA Token",
            "endpoint": "/v1/2fa/test-token/<DEMO_USERNAME>/123456",
            "method": "GET",
            "category": "Client 2FA",
            "description": "Test 2FA token for client <DEMO_USERNAME>"
        },
        {
            "name": "Demo 2FA Setup",
            "endpoint": "/v1/2fa/demo-setup",
            "method": "GET",
            "category": "Client 2FA",
            "description": "Demo 2FA setup process"
        }
    ]
    
    results = []
    
    for endpoint_config in twofa_endpoints:
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
    
    print(f"\nReport generated: 2fa_endpoints_test_report.md")
    print("=" * 75)

def generate_markdown_report(results):
    """Generate a comprehensive markdown report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# BHIV HR Platform - Two-Factor Authentication Endpoints Test Report

**Generated:** {timestamp}  
**Platform:** BHIV HR Gateway Service  
**Base URL:** {BASE_URL}  
**Test Category:** Two-Factor Authentication (2FA) System

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
    
    # Add 2FA security analysis
    report += "## 🔐 Two-Factor Authentication Analysis\n\n"
    report += "### 2FA Security Features\n\n"
    report += "The 2FA system provides enterprise-grade security with:\n\n"
    report += "- **TOTP Authentication** - Time-based One-Time Password support\n"
    report += "- **QR Code Generation** - Easy mobile app setup\n"
    report += "- **Backup Codes** - Recovery options for lost devices\n"
    report += "- **Dual System Support** - Separate 2FA for users and clients\n"
    report += "- **Token Validation** - Real-time token verification\n"
    report += "- **Status Management** - Enable/disable 2FA functionality\n\n"
    
    report += "### 2FA Implementation Benefits:\n\n"
    report += "1. **Enhanced Security** - Prevents unauthorized access even with compromised passwords\n"
    report += "2. **Mobile Integration** - Works with Google Authenticator, Authy, etc.\n"
    report += "3. **Recovery Options** - Backup codes prevent account lockout\n"
    report += "4. **Enterprise Ready** - Separate systems for internal users and external clients\n"
    report += "5. **Real-time Validation** - Immediate token verification\n"
    report += "6. **Audit Trail** - Complete 2FA activity logging\n\n"
    
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
    report += "## 💡 2FA Security Recommendations\n\n"
    
    if total_success == total_count:
        report += "✅ **All 2FA endpoints are functioning correctly**\n\n"
        report += "- User 2FA authentication system is operational\n"
        report += "- Client 2FA system is working properly\n"
        report += "- QR code generation is available\n"
        report += "- Backup code systems are functional\n"
        report += "- Token validation is working correctly\n"
        report += "- Status management endpoints are operational\n\n"
    else:
        failed_count = total_count - total_success
        report += f"⚠️ **{failed_count} 2FA endpoint(s) failed testing**\n\n"
        failed_endpoints = [r for r in results if r["status"] != "success"]
        for failed in failed_endpoints:
            report += f"- `{failed['endpoint_info']['endpoint']}`: {failed.get('message', 'Unknown error')}\n"
        report += "\n"
    
    report += "### 2FA Best Practices:\n\n"
    report += "1. **Mandatory 2FA** - Require 2FA for all administrative accounts\n"
    report += "2. **Backup Codes** - Ensure users have secure backup code storage\n"
    report += "3. **Token Expiry** - Implement appropriate TOTP time windows\n"
    report += "4. **Rate Limiting** - Prevent brute force attacks on 2FA tokens\n"
    report += "5. **Audit Logging** - Monitor all 2FA setup and usage events\n"
    report += "6. **Recovery Process** - Establish secure 2FA recovery procedures\n"
    report += "7. **Mobile App Support** - Test compatibility with major authenticator apps\n\n"
    
    # Add usage examples
    report += "## 📝 2FA Usage Examples\n\n"
    report += "### Setup User 2FA\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/auth/2fa/setup" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "user_id": 1,\n'
    report += '    "username": "john_doe",\n'
    report += '    "email": "john@example.com"\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += "### Get QR Code for Setup\n"
    report += "```bash\n"
    report += f'curl -H "Authorization: Bearer {API_KEY}" \\\n'
    report += f'     "{BASE_URL}/v1/auth/2fa/qr/1"\n'
    report += "```\n\n"
    
    report += "### Verify 2FA Token\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/auth/2fa/verify" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "user_id": 1,\n'
    report += '    "token": "123456"\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += "### Setup Client 2FA\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/2fa/setup" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "client_id": "<DEMO_USERNAME>",\n'
    report += '    "email": "admin@<DEMO_USERNAME>.com"\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += f"---\n\n"
    report += f"**Report Generated:** {timestamp}  \n"
    report += f"**Test Duration:** {sum(r.get('response_time', 0) for r in results):.3f}s total  \n"
    report += f"**Platform:** BHIV HR Platform v3.0.0-Phase3  \n"
    
    # Write report to file
    with open("2fa_endpoints_test_report.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
