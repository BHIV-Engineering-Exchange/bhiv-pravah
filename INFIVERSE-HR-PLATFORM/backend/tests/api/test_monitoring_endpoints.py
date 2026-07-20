#!/usr/bin/env python3
"""
BHIV HR Platform - Monitoring Endpoints Testing
Tests the monitoring endpoints individually and generates a comprehensive report.
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

def test_endpoint(endpoint: str, method: str = "GET", data: Dict = None, auth_required: bool = True) -> Dict[str, Any]:
    """Test a single endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    headers = HEADERS if auth_required else {"Content-Type": "application/json"}
    
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
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
    """Test monitoring endpoints and generate report"""
    print("Testing BHIV HR Platform Monitoring Endpoints")
    print("=" * 60)
    
    # Test endpoints
    monitoring_endpoints = [
        {
            "name": "Prometheus Metrics",
            "endpoint": "/metrics",
            "method": "GET",
            "auth_required": False,
            "description": "Export Prometheus metrics for monitoring"
        },
        {
            "name": "Detailed Health Check",
            "endpoint": "/health/detailed",
            "method": "GET", 
            "auth_required": True,
            "description": "Comprehensive health check with system metrics"
        },
        {
            "name": "Metrics Dashboard",
            "endpoint": "/metrics/dashboard",
            "method": "GET",
            "auth_required": True,
            "description": "Real-time metrics dashboard data"
        }
    ]
    
    results = []
    
    for endpoint_config in monitoring_endpoints:
        print(f"\nTesting: {endpoint_config['name']}")
        print(f"   Endpoint: {endpoint_config['endpoint']}")
        print(f"   Method: {endpoint_config['method']}")
        print(f"   Auth Required: {endpoint_config['auth_required']}")
        
        result = test_endpoint(
            endpoint_config["endpoint"],
            endpoint_config["method"],
            auth_required=endpoint_config["auth_required"]
        )
        
        result["endpoint_info"] = endpoint_config
        results.append(result)
        
        # Print immediate results
        if result["status"] == "success":
            print(f"   [OK] Status: {result['status_code']} - {result['response_time']}s")
            if isinstance(result["response_data"], dict):
                print(f"   Response keys: {list(result['response_data'].keys())}")
            else:
                print(f"   Response size: {result['response_size']} bytes")
        else:
            print(f"   [ERROR] Status: {result['status']} - {result.get('message', 'Unknown error')}")
    
    # Generate markdown report
    generate_markdown_report(results)
    
    print(f"\nReport generated: monitoring_endpoints_test_report.md")
    print("=" * 60)

def generate_markdown_report(results):
    """Generate a comprehensive markdown report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# BHIV HR Platform - Monitoring Endpoints Test Report

**Generated:** {timestamp}  
**Platform:** BHIV HR Gateway Service  
**Base URL:** {BASE_URL}  
**Test Category:** Monitoring Endpoints

## 📊 Test Summary

| Endpoint | Status | Response Time | Status Code | Auth Required |
|----------|--------|---------------|-------------|---------------|
"""
    
    for result in results:
        endpoint_info = result["endpoint_info"]
        status_icon = "✅" if result["status"] == "success" else "❌"
        status_code = result.get("status_code", "N/A")
        response_time = f"{result.get('response_time', 0):.3f}s"
        auth_req = "Yes" if endpoint_info["auth_required"] else "No"
        
        report += f"| `{endpoint_info['endpoint']}` | {status_icon} {result['status']} | {response_time} | {status_code} | {auth_req} |\n"
    
    report += "\n## 🔍 Detailed Test Results\n\n"
    
    for i, result in enumerate(results, 1):
        endpoint_info = result["endpoint_info"]
        
        report += f"### {i}. {endpoint_info['name']}\n\n"
        report += f"**Endpoint:** `{endpoint_info['method']} {endpoint_info['endpoint']}`  \n"
        report += f"**Description:** {endpoint_info['description']}  \n"
        report += f"**Authentication:** {'Required' if endpoint_info['auth_required'] else 'Not Required'}  \n\n"
        
        if result["status"] == "success":
            report += f"**✅ Test Result:** PASSED  \n"
            report += f"**Status Code:** {result['status_code']}  \n"
            report += f"**Response Time:** {result['response_time']}s  \n"
            report += f"**Response Size:** {result['response_size']} bytes  \n\n"
            
            # Add response analysis
            if isinstance(result["response_data"], dict):
                report += "**Response Structure:**\n```json\n"
                # Show first few keys or structure
                if len(str(result["response_data"])) > 1000:
                    report += json.dumps({k: "..." for k in list(result["response_data"].keys())[:10]}, indent=2)
                    report += "\n// ... (truncated for readability)\n"
                else:
                    report += json.dumps(result["response_data"], indent=2)
                report += "\n```\n\n"
            else:
                report += f"**Response Type:** {type(result['response_data']).__name__}  \n"
                if isinstance(result["response_data"], str) and len(result["response_data"]) > 200:
                    report += f"**Response Preview:** `{result['response_data'][:200]}...`  \n\n"
                else:
                    report += f"**Response:** `{result['response_data']}`  \n\n"
        else:
            report += f"**❌ Test Result:** FAILED  \n"
            report += f"**Error:** {result.get('message', 'Unknown error')}  \n"
            if "response_time" in result:
                report += f"**Response Time:** {result['response_time']}s  \n"
            report += "\n"
    
    # Add code structure analysis
    report += "## 🏗️ Code Structure Analysis\n\n"
    report += "### Monitoring System Implementation\n\n"
    report += "The monitoring endpoints are implemented using:\n\n"
    report += "- **Advanced Monitoring System** (`monitoring.py`)\n"
    report += "- **Prometheus Metrics Integration**\n"
    report += "- **System Performance Tracking**\n"
    report += "- **Business Metrics Collection**\n"
    report += "- **Health Check Aggregation**\n\n"
    
    report += "### Key Components:\n\n"
    report += "1. **AdvancedMonitor Class** - Core monitoring functionality\n"
    report += "2. **Prometheus Metrics** - Counter, Histogram, Gauge metrics\n"
    report += "3. **Performance Buffers** - Deque-based metric storage\n"
    report += "4. **System Metrics** - CPU, memory, disk monitoring\n"
    report += "5. **Alert Thresholds** - Configurable monitoring alerts\n\n"
    
    # Add recommendations
    report += "## 💡 Recommendations\n\n"
    
    success_count = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)
    
    if success_count == total_count:
        report += "✅ **All monitoring endpoints are functioning correctly**\n\n"
        report += "- Prometheus metrics are being exported properly\n"
        report += "- Health checks provide comprehensive system status\n"
        report += "- Dashboard metrics are accessible for real-time monitoring\n"
    else:
        report += f"⚠️ **{total_count - success_count} out of {total_count} endpoints failed**\n\n"
        report += "**Action Items:**\n"
        for result in results:
            if result["status"] != "success":
                endpoint_info = result["endpoint_info"]
                report += f"- Fix `{endpoint_info['endpoint']}`: {result.get('message', 'Unknown error')}\n"
    
    report += "\n## 🔧 Usage Examples\n\n"
    report += "### Prometheus Metrics Collection\n"
    report += "```bash\n"
    report += f"curl {BASE_URL}/metrics\n"
    report += "```\n\n"
    
    report += "### Health Check Monitoring\n"
    report += "```bash\n"
    report += f"curl -H \"Authorization: Bearer {API_KEY}\" \\\\\n"
    report += f"     {BASE_URL}/health/detailed\n"
    report += "```\n\n"
    
    report += "### Dashboard Data Access\n"
    report += "```bash\n"
    report += f"curl -H \"Authorization: Bearer {API_KEY}\" \\\\\n"
    report += f"     {BASE_URL}/metrics/dashboard\n"
    report += "```\n\n"
    
    report += f"---\n*Report generated by BHIV HR Platform Testing Suite - {timestamp}*\n"
    
    # Write report to file
    with open("monitoring_endpoints_test_report.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
