"""
7-Pillar System Verification Script
Tests all services: Karma, Bucket, Core, Workflow, UAO, Insight Core
"""
import requests
import time

SERVICES = {
    "Karma": "http://localhost:8000/health",
    "Bucket": "http://localhost:8001/health",
    "Core": "http://localhost:8002/health",
    "Workflow": "http://localhost:8003/healthz",
    "UAO": "http://localhost:8004/docs",
    "Insight": "http://localhost:8005/health"
}

def test_service(name, url):
    """Test if service is running"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name:15} RUNNING on {url}")
            return True
        else:
            print(f"❌ {name:15} ERROR {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name:15} OFFLINE - {str(e)[:50]}")
        return False

def main():
    print("=" * 80)
    print("7-PILLAR SYSTEM VERIFICATION")
    print("=" * 80)
    print()
    
    results = {}
    for name, url in SERVICES.items():
        results[name] = test_service(name, url)
        time.sleep(0.5)
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    running = sum(results.values())
    total = len(results)
    
    print(f"Services Running: {running}/{total}")
    print()
    
    if running == total:
        print("✅ ALL SERVICES OPERATIONAL - System is production ready!")
        print()
        print("Next Steps:")
        print("1. Run: python test_insight_integration.py")
        print("2. Run: python test_complete_integration.py")
        return True
    else:
        print(f"❌ {total - running} service(s) not running")
        print()
        print("Start missing services:")
        for name, status in results.items():
            if not status:
                print(f"  - {name}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
