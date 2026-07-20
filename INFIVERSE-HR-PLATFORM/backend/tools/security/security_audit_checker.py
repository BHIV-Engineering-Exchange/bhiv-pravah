#!/usr/bin/env python3
"""
Security Audit and Configuration Checker
Manual verification of URLs, credentials, and data leaks
"""

import os
import re
from typing import Dict, List, Tuple

class SecurityAuditChecker:
    def __init__(self):
        # Expected production URLs
        self.expected_urls = {
            "gateway": "https://bhiv-hr-gateway-ltg0.onrender.com",
            "agent": "https://bhiv-hr-agent-nhgg.onrender.com", 
            "hr_portal": "https://bhiv-hr-portal-u670.onrender.com",
            "client_portal": "https://bhiv-hr-client-portal-3iod.onrender.com",
            "candidate_portal": "https://bhiv-hr-candidate-portal.onrender.com",
            "database": "postgresql://bhiv_user:JwvtCqKDYsVgnTiAEtSNAKaDHkksATRA@dpg-d4kjncvpm1nc738abapg-a.oregon-postgres.render.com/bhiv_hr_i7zb"
        }
        
        # Expected API key
        self.expected_api_key = "<YOUR_API_KEY>"
        
        # Files to check
        self.files_to_check = [
            "c:\\BHIV-HR-Platform\\services\\portal\\config.py",
            "c:\\BHIV-HR-Platform\\services\\portal\\app.py",
            "c:\\BHIV-HR-Platform\\services\\client_portal\\config.py",
            "c:\\BHIV-HR-Platform\\services\\client_portal\\app.py",
            "c:\\BHIV-HR-Platform\\services\\candidate_portal\\config.py",
            "c:\\BHIV-HR-Platform\\services\\candidate_portal\\app.py",
            "c:\\BHIV-HR-Platform\\services\\gateway\\dependencies.py",
            "c:\\BHIV-HR-Platform\\services\\agent\\app.py",
            "c:\\BHIV-HR-Platform\\config\\.env.render",
            "c:\\BHIV-HR-Platform\\config\\production.env",
            "c:\\BHIV-HR-Platform\\.env.example"
        ]
        
        self.issues = []
        
    def check_file_security(self, filepath: str) -> Dict:
        """Check individual file for security issues"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Cannot read file: {str(e)}"}
        
        issues = []
        
        # Check for hardcoded credentials
        credential_patterns = [
            (r'password["\']?\s*[:=]\s*["\']([^"\']+)["\']', "Hardcoded password"),
            (r'secret["\']?\s*[:=]\s*["\']([^"\']+)["\']', "Hardcoded secret"),
            (r'key["\']?\s*[:=]\s*["\']([^"\']+)["\']', "Hardcoded key"),
            (r'token["\']?\s*[:=]\s*["\']([^"\']+)["\']', "Hardcoded token")
        ]
        
        for pattern, issue_type in credential_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) > 10:  # Only flag substantial values
                    issues.append(f"{issue_type}: {match[:20]}...")
        
        # Check URLs
        url_issues = []
        for service, expected_url in self.expected_urls.items():
            if service == "database":
                continue  # Skip database URL check here
            
            # Look for incorrect URLs
            if "http" in content:
                urls_found = re.findall(r'https?://[^\s"\']+', content)
                for url in urls_found:
                    if service in url.lower() and url != expected_url:
                        url_issues.append(f"Incorrect {service} URL: {url}")
        
        # Check for database credentials exposure
        db_pattern = r'postgresql://[^"\'\\s]+'
        db_matches = re.findall(db_pattern, content)
        for match in db_matches:
            if match != self.expected_urls["database"]:
                issues.append(f"Incorrect database URL: {match}")
        
        # Check API key consistency
        api_key_pattern = r'prod_api_key_[A-Za-z0-9_-]+'
        api_matches = re.findall(api_key_pattern, content)
        for match in api_matches:
            if match != self.expected_api_key:
                issues.append(f"Incorrect API key: {match}")
        
        return {
            "credential_issues": issues,
            "url_issues": url_issues,
            "total_issues": len(issues) + len(url_issues)
        }
    
    def run_audit(self):
        """Run complete security audit"""
        print("Running Security Audit and Configuration Check...")
        print("=" * 60)
        
        total_issues = 0
        file_results = {}
        
        for filepath in self.files_to_check:
            filename = os.path.basename(filepath)
            print(f"\nChecking: {filename}")
            
            result = self.check_file_security(filepath)
            file_results[filename] = result
            
            if "error" in result:
                print(f"  ERROR: {result['error']}")
                continue
            
            if result["total_issues"] == 0:
                print("  OK: No security issues found")
            else:
                print(f"  ISSUES FOUND: {result['total_issues']}")
                for issue in result["credential_issues"]:
                    print(f"    - {issue}")
                for issue in result["url_issues"]:
                    print(f"    - {issue}")
                
                total_issues += result["total_issues"]
        
        print("\n" + "=" * 60)
        print(f"AUDIT COMPLETE: {total_issues} total issues found")
        
        # Generate detailed report
        self.generate_security_report(file_results, total_issues)
        
        return total_issues == 0
    
    def generate_security_report(self, results: Dict, total_issues: int):
        """Generate detailed security report"""
        report = f"""# Security Audit Report
Generated: 2025-10-23

## Executive Summary
- Total Files Checked: {len(self.files_to_check)}
- Total Issues Found: {total_issues}
- Security Status: {'SECURE' if total_issues == 0 else 'NEEDS ATTENTION'}

## Expected Configuration
- Gateway URL: {self.expected_urls['gateway']}
- Agent URL: {self.expected_urls['agent']}
- HR Portal URL: {self.expected_urls['hr_portal']}
- Client Portal URL: {self.expected_urls['client_portal']}
- Candidate Portal URL: {self.expected_urls['candidate_portal']}
- Database URL: {self.expected_urls['database'][:50]}...
- API Key: {self.expected_api_key[:20]}...

## File-by-File Analysis

"""
        
        for filename, result in results.items():
            if "error" in result:
                report += f"### {filename}\n- Status: ERROR\n- Issue: {result['error']}\n\n"
                continue
            
            status = "SECURE" if result["total_issues"] == 0 else "ISSUES FOUND"
            report += f"### {filename}\n- Status: {status}\n"
            
            if result["total_issues"] > 0:
                report += f"- Issues: {result['total_issues']}\n"
                for issue in result["credential_issues"]:
                    report += f"  - {issue}\n"
                for issue in result["url_issues"]:
                    report += f"  - {issue}\n"
            
            report += "\n"
        
        report += f"""## Security Recommendations

### High Priority
1. Ensure all URLs match production endpoints
2. Verify API keys are consistent across all services
3. Check database URLs are identical in all configurations

### Medium Priority
1. Use environment variables for all sensitive data
2. Implement proper secret management
3. Regular security audits

## Conclusion
{'All configurations are secure and consistent.' if total_issues == 0 else f'{total_issues} security issues need to be addressed.'}

---
*Generated by BHIV HR Platform Security Auditor*
"""
        
        with open("security_audit_report.md", 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Detailed security report saved: security_audit_report.md")

if __name__ == "__main__":
    auditor = SecurityAuditChecker()
    is_secure = auditor.run_audit()
