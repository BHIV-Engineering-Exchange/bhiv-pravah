#!/usr/bin/env python3
"""
Gateway Rectification Implementation
Implements the rectification plan step by step
"""

import re
from pathlib import Path

def implement_phase1_remove_duplicates():
    """Phase 1: Remove duplicate endpoints"""
    
    gateway_file = Path("c:\\BHIV HR PLATFORM\\services\\gateway\\app\\main.py")
    
    with open(gateway_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Phase 1: Removing duplicate endpoints...")
    
    # Step 1.1: Remove duplicate 2FA endpoints (/v1/2fa/*)
    duplicate_2fa_patterns = [
        r'@app\.post\("/v1/2fa/setup"\).*?async def setup_2fa_for_client.*?return \{[^}]*\}',
        r'@app\.post\("/v1/2fa/verify-setup"\).*?async def verify_2fa_setup.*?raise HTTPException\(status_code=401, detail="Invalid 2FA code"\)',
        r'@app\.post\("/v1/2fa/login-with-2fa"\).*?async def login_with_2fa.*?raise HTTPException\(status_code=401, detail="Invalid 2FA code"\)',
        r'@app\.get\("/v1/2fa/status/\{client_id\}"\).*?async def get_2fa_status.*?return \{[^}]*\}',
        r'@app\.post\("/v1/2fa/disable"\).*?async def disable_2fa.*?return \{[^}]*\}',
        r'@app\.post\("/v1/2fa/regenerate-backup-codes"\).*?async def regenerate_backup_codes.*?return \{[^}]*\}',
        r'@app\.get\("/v1/2fa/test-token/\{client_id\}/\{token\}"\).*?async def test_2fa_token.*?return \{[^}]*\}',
        r'@app\.get\("/v1/2fa/demo-setup"\).*?async def demo_2fa_setup.*?return \{[^}]*\}'
    ]
    
    # Step 1.2: Remove duplicate password endpoints (/v1/password/*)
    duplicate_password_patterns = [
        r'@app\.post\("/v1/password/validate"\).*?async def validate_password_strength.*?return \{[^}]*\}',
        r'@app\.post\("/v1/password/generate"\).*?async def generate_secure_password.*?return \{[^}]*\}',
        r'@app\.get\("/v1/password/policy"\).*?async def get_password_policy.*?return \{[^}]*\}',
        r'@app\.post\("/v1/password/change"\).*?async def change_password.*?return \{[^}]*\}',
        r'@app\.get\("/v1/password/strength-test"\).*?async def password_strength_testing_tool.*?return \{[^}]*\}',
        r'@app\.get\("/v1/password/security-tips"\).*?async def password_security_best_practices.*?return \{[^}]*\}'
    ]
    
    # Step 1.3: Remove duplicate CSP endpoints (/v1/csp/*)
    duplicate_csp_patterns = [
        r'@app\.get\("/v1/csp/policies"\).*?async def get_csp_policies.*?return \{[^}]*\}',
        r'@app\.get\("/v1/csp/violations"\).*?async def get_csp_violations.*?return \{[^}]*\}',
        r'@app\.post\("/v1/csp/report"\).*?async def csp_report.*?return \{[^}]*\}',
        r'@app\.get\("/v1/csp/test"\).*?async def test_csp.*?return \{[^}]*\}'
    ]
    
    # Remove duplicates
    all_patterns = duplicate_2fa_patterns + duplicate_password_patterns + duplicate_csp_patterns
    
    for pattern in all_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Clean up extra newlines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    return content

def implement_phase2_environment_security():
    """Phase 2: Add environment-based security endpoint loading"""
    
    # This will be implemented after Phase 1
    pass

def implement_phase3_add_missing():
    """Phase 3: Add missing core endpoints"""
    
    # This will be implemented after Phase 1
    pass

def count_endpoints_in_content(content):
    """Count endpoints in the content"""
    patterns = [
        r'@app\.get\(',
        r'@app\.post\(',
        r'@app\.put\(',
        r'@app\.delete\(',
        r'@app\.patch\('
    ]
    
    total = 0
    for pattern in patterns:
        total += len(re.findall(pattern, content))
    
    return total

if __name__ == "__main__":
    print("GATEWAY RECTIFICATION IMPLEMENTATION")
    print("=" * 40)
    
    # Read original file
    gateway_file = Path("c:\\BHIV HR PLATFORM\\services\\gateway\\app\\main.py")
    
    with open(gateway_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    original_count = count_endpoints_in_content(original_content)
    print(f"Original endpoint count: {original_count}")
    
    # Implement Phase 1
    modified_content = implement_phase1_remove_duplicates()
    new_count = count_endpoints_in_content(modified_content)
    
    print(f"After Phase 1 endpoint count: {new_count}")
    print(f"Endpoints removed: {original_count - new_count}")
    
    # Save the modified content
    with open(gateway_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("Phase 1 implementation complete!")
    print("Duplicate endpoints removed successfully.")