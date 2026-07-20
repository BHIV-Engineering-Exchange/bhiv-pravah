"""
Quick Service Health Checker
============================
Tests each microservice endpoint individually without starting services
"""

import requests
import sys
from datetime import datetime

def test_service(name: str, url: str, timeout: int = 5) -> dict:
    """Test a single service endpoint"""
    try:
        start_time = datetime.now()
        response = requests.get(url, timeout=timeout)
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "name": name,
            "url": url,
            "status": "[OK] HEALTHY" if response.status_code == 200 else f"[X] HTTP {response.status_code}",
            "response_time_ms": round(elapsed, 2),
            "reachable": True
        }
    except requests.exceptions.ConnectionError:
        return {
            "name": name,
            "url": url,
            "status": "[X] NOT RUNNING",
            "response_time_ms": 0,
            "reachable": False
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "status": f"[X] ERROR: {str(e)}",
            "response_time_ms": 0,
            "reachable": False
        }

def main():
    print("\n" + "="*70)
    print("BHIV MICROSERVICES - INDIVIDUAL HEALTH CHECK")
    print("="*70 + "\n")
    
    services = [
        ("Prompt Runner", "http://127.0.0.1:8003/health"),
        ("Creator Core", "http://127.0.0.1:8000/"),
        ("BHIV Core", "http://127.0.0.1:8001/system/health"),
        ("Integration Bridge", "http://127.0.0.1:8004/pipeline/health"),
        ("BHIV Bucket", "http://127.0.0.1:8005/bucket/stats"),
        ("CET Service", "http://127.0.0.1:8006/health"),
        ("Sarathi Service", "http://127.0.0.1:8007/health"),
        ("Gate Service", "http://127.0.0.1:8008/health"),
    ]
    
    results = []
    for name, url in services:
        print(f"Testing {name}...", end=" ")
        result = test_service(name, url)
        results.append(result)
        print(result["status"])
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    running_count = sum(1 for r in results if r["reachable"])
    total_count = len(results)
    
    for r in results:
        status_icon = "[OK]" if r["reachable"] else "[X]"
        print(f"{status_icon} {r['name']:20s} | {r['url']:45s} | {r['status']}")
    
    print("-" * 70)
    print(f"Total: {running_count}/{total_count} services running")
    
    if running_count == total_count:
        print("\n[OK] All services are running!")
    else:
        print(f"\n[!] {total_count - running_count} services are not running")
        print("\nTo start all services, run:")
        print("  python deploy_and_test.py")
    
    return running_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
