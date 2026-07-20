#!/usr/bin/env python3
"""
Precise Database URL Verification
"""

def check_production_db_urls():
    """Check only the production database URLs in service configs"""
    
    # Expected production database URL from Render
    expected_url = "postgresql://bhiv_user:JwvtCqKDYsVgnTiAEtSNAKaDHkksATRA@dpg-d4kjncvpm1nc738abapg-a.oregon-postgres.render.com/bhiv_hr_i7zb"
    
    services = {
        "Client Portal": "c:\\BHIV-HR-Platform\\services\\client_portal\\config.py",
        "Candidate Portal": "c:\\BHIV-HR-Platform\\services\\candidate_portal\\config.py",
        "Render Config": "c:\\BHIV-HR-Platform\\config\\.env.render"
    }
    
    print("Production Database URL Verification:")
    print("=" * 60)
    print(f"Expected URL: {expected_url}")
    print("=" * 60)
    
    all_correct = True
    
    for service, path in services.items():
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            if expected_url in content:
                print(f"OK {service}: CORRECT")
            else:
                print(f"ERROR {service}: INCORRECT or MISSING")
                all_correct = False
                
        except Exception as e:
            print(f"ERROR {service}: {str(e)}")
            all_correct = False
    
    print("=" * 60)
    if all_correct:
        print("OK ALL SERVICES USE CORRECT PRODUCTION DATABASE URL")
    else:
        print("ERROR SOME SERVICES HAVE INCORRECT DATABASE URLS")
    
    return all_correct

if __name__ == "__main__":
    check_production_db_urls()
