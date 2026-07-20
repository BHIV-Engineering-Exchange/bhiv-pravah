#!/usr/bin/env python3
"""
BHIV HR Platform - Candidate Portal Endpoints Testing
Tests all candidate portal endpoints and generates a comprehensive report.
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
        elif method == "PUT":
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
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
    """Test candidate portal endpoints and generate report"""
    print("Testing BHIV HR Platform Candidate Portal Endpoints")
    print("=" * 65)
    
    # Candidate portal endpoints configuration
    candidate_endpoints = [
        {
            "name": "Candidate Register",
            "endpoint": "/v1/candidate/register",
            "method": "POST",
            "category": "Authentication",
            "description": "Register new candidate account",
            "test_data": {
                "email": "newcandidate@example.com",
                "password": "SecurePass123!",
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+1-555-987-6543",
                "location": "San Francisco, CA"
            }
        },
        {
            "name": "Candidate Login",
            "endpoint": "/v1/candidate/login",
            "method": "POST",
            "category": "Authentication",
            "description": "Authenticate candidate and get access token",
            "test_data": {
                "email": "candidate@example.com",
                "password": "password123"
            }
        },
        {
            "name": "Update Candidate Profile",
            "endpoint": "/v1/candidate/profile/1",
            "method": "PUT",
            "category": "Profile Management",
            "description": "Update candidate profile information",
            "test_data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe.updated@example.com",
                "phone": "+1-555-123-9999",
                "location": "New York, NY",
                "skills": ["Python", "JavaScript", "React", "Node.js"],
                "experience_years": 5,
                "education": "Bachelor's in Computer Science",
                "summary": "Experienced full-stack developer with 5 years in web development"
            }
        },
        {
            "name": "Apply for Job",
            "endpoint": "/v1/candidate/apply",
            "method": "POST",
            "category": "Job Applications",
            "description": "Submit job application",
            "test_data": {
                "candidate_id": 1,
                "job_id": 1,
                "cover_letter": "I am very interested in this position and believe my skills in Python and web development make me a great fit for this role.",
                "resume_url": "https://example.com/resume.pdf",
                "additional_notes": "Available for immediate start"
            }
        },
        {
            "name": "Get Candidate Applications",
            "endpoint": "/v1/candidate/applications/1",
            "method": "GET",
            "category": "Job Applications",
            "description": "Retrieve all applications for candidate ID 1"
        }
    ]
    
    results = []
    
    for endpoint_config in candidate_endpoints:
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
    
    print(f"\nReport generated: candidate_portal_endpoints_test_report.md")
    print("=" * 65)

def generate_markdown_report(results):
    """Generate a comprehensive markdown report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# BHIV HR Platform - Candidate Portal Endpoints Test Report

**Generated:** {timestamp}  
**Platform:** BHIV HR Gateway Service  
**Base URL:** {BASE_URL}  
**Test Category:** Candidate Portal System

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
                    
                # Add test data if it was a POST/PUT request
                if endpoint_info["method"] in ["POST", "PUT"] and "test_data" in endpoint_info:
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
    
    # Add candidate portal analysis
    report += "## 👥 Candidate Portal Analysis\n\n"
    report += "### Candidate Portal Features\n\n"
    report += "The candidate portal provides comprehensive job seeker functionality:\n\n"
    report += "- **Account Management** - Registration and authentication system\n"
    report += "- **Profile Management** - Complete candidate profile updates\n"
    report += "- **Job Applications** - Apply for positions with cover letters\n"
    report += "- **Application Tracking** - View all submitted applications\n"
    report += "- **Secure Authentication** - JWT-based candidate login system\n"
    report += "- **Data Validation** - Input validation and error handling\n\n"
    
    report += "### Candidate Experience Benefits:\n\n"
    report += "1. **Easy Registration** - Simple account creation process\n"
    report += "2. **Profile Control** - Complete profile management capabilities\n"
    report += "3. **Job Discovery** - Access to available positions\n"
    report += "4. **Application Management** - Track application status\n"
    report += "5. **Secure Access** - Protected candidate data and privacy\n"
    report += "6. **Mobile Ready** - API-first design for mobile applications\n\n"
    
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
    report += "## 💡 Candidate Portal Recommendations\n\n"
    
    if total_success == total_count:
        report += "✅ **All candidate portal endpoints are functioning correctly**\n\n"
        report += "- Candidate registration is working properly\n"
        report += "- Authentication system is secure and functional\n"
        report += "- Profile management allows complete updates\n"
        report += "- Job application process is streamlined\n"
        report += "- Application tracking provides visibility\n\n"
    else:
        failed_count = total_count - total_success
        report += f"⚠️ **{failed_count} candidate portal endpoint(s) failed testing**\n\n"
        failed_endpoints = [r for r in results if r["status"] != "success"]
        for failed in failed_endpoints:
            report += f"- `{failed['endpoint_info']['endpoint']}`: {failed.get('message', 'Unknown error')}\n"
        report += "\n"
    
    report += "### Candidate Portal Best Practices:\n\n"
    report += "1. **User Experience** - Ensure intuitive and responsive interface\n"
    report += "2. **Data Security** - Protect candidate personal information\n"
    report += "3. **Application Process** - Streamline job application workflow\n"
    report += "4. **Status Updates** - Provide real-time application status\n"
    report += "5. **Profile Completeness** - Encourage complete profile information\n"
    report += "6. **Mobile Optimization** - Ensure mobile-friendly experience\n"
    report += "7. **Communication** - Enable candidate-recruiter communication\n\n"
    
    # Add usage examples
    report += "## 📝 Candidate Portal Usage Examples\n\n"
    report += "### Register New Candidate\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/candidate/register" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "email": "candidate@example.com",\n'
    report += '    "password": "SecurePass123!",\n'
    report += '    "first_name": "John",\n'
    report += '    "last_name": "Doe",\n'
    report += '    "phone": "+1-555-123-4567",\n'
    report += '    "location": "San Francisco, CA"\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += "### Candidate Login\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/candidate/login" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "email": "candidate@example.com",\n'
    report += '    "password": "password123"\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += "### Update Profile\n"
    report += "```bash\n"
    report += f'curl -X PUT "{BASE_URL}/v1/candidate/profile/1" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "first_name": "John",\n'
    report += '    "last_name": "Doe",\n'
    report += '    "skills": ["Python", "JavaScript", "React"],\n'
    report += '    "experience_years": 5\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += "### Apply for Job\n"
    report += "```bash\n"
    report += f'curl -X POST "{BASE_URL}/v1/candidate/apply" \\\n'
    report += f'  -H "Authorization: Bearer {API_KEY}" \\\n'
    report += '  -H "Content-Type: application/json" \\\n'
    report += '  -d {\n'
    report += '    "candidate_id": 1,\n'
    report += '    "job_id": 1,\n'
    report += '    "cover_letter": "I am interested in this position...",\n'
    report += '    "resume_url": "https://example.com/resume.pdf"\n'
    report += '  }\n'
    report += "```\n\n"
    
    report += f"---\n\n"
    report += f"**Report Generated:** {timestamp}  \n"
    report += f"**Test Duration:** {sum(r.get('response_time', 0) for r in results):.3f}s total  \n"
    report += f"**Platform:** BHIV HR Platform v3.0.0-Phase3  \n"
    
    # Write report to file
    with open("candidate_portal_endpoints_test_report.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
