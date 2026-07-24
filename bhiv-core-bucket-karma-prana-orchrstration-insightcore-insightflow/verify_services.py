import requests
import json

def check_service(port, expected_service):
    """Check which service is running on a given port"""
    urls_to_try = [
        f"http://localhost:{port}/health",
        f"http://localhost:{port}/healthz",
        f"http://localhost:{port}/docs",
        f"http://localhost:{port}/openapi.json"
    ]
    
    print(f"\n{'='*60}")
    print(f"Checking Port {port} (Expected: {expected_service})")
    print(f"{'='*60}")
    
    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✅ {url}")
                
                # Try to identify service from response
                if '/openapi.json' in url:
                    data = response.json()
                    title = data.get('info', {}).get('title', 'Unknown')
                    print(f"   Service Title: {title}")
                    
                    if 'Workflow' in title and expected_service != 'Workflow Executor':
                        print(f"   ⚠️  WARNING: Found '{title}' but expected '{expected_service}'!")
                    elif 'Karma' in title and expected_service != 'Karma':
                        print(f"   ⚠️  WARNING: Found '{title}' but expected '{expected_service}'!")
                    else:
                        print(f"   ✅ Correct service!")
                elif '/health' in url or '/healthz' in url:
                    try:
                        data = response.json()
                        print(f"   Response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"   Response: {response.text[:100]}")
                break
        except requests.exceptions.RequestException as e:
            print(f"❌ {url} - {type(e).__name__}")
    else:
        print(f"❌ Port {port} - No service responding")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SERVICE PORT VERIFICATION")
    print("="*60)
    
    services = [
        (8000, "Karma"),
        (8001, "Bucket"),
        (8002, "Core"),
        (8003, "Workflow Executor")
    ]
    
    for port, expected in services:
        check_service(port, expected)
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
