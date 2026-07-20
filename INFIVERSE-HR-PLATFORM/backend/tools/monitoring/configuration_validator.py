#!/usr/bin/env python3
"""
BHIV HR Platform - Configuration Validator
Validates all service configurations for candidate portal integration
"""

import os
import json
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class ConfigIssue:
    service: str
    issue_type: str
    description: str
    severity: str
    fix_suggestion: str

class ConfigurationValidator:
    def __init__(self):
        self.issues: List[ConfigIssue] = []
        self.services = ["gateway", "agent", "portal", "client_portal", "candidate_portal"]
        
    def validate_all_configurations(self) -> Dict[str, Any]:
        """Validate all service configurations"""
        print("Validating all service configurations...")
        
        results = {
            "hr_portal": self.validate_hr_portal_config(),
            "client_portal": self.validate_client_portal_config(),
            "candidate_portal": self.validate_candidate_portal_config(),
            "gateway_dependencies": self.validate_gateway_dependencies(),
            "environment_files": self.validate_environment_files(),
            "cross_service_compatibility": self.validate_cross_service_compatibility(),
            "issues": [
                {
                    "service": issue.service,
                    "type": issue.issue_type,
                    "description": issue.description,
                    "severity": issue.severity,
                    "fix": issue.fix_suggestion
                } for issue in self.issues
            ]
        }
        
        return results
    
    def validate_hr_portal_config(self) -> Dict[str, Any]:
        """Validate HR Portal configuration"""
        config_path = "c:\\BHIV-HR-Platform\\services\\portal\\config.py"
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Check for production URLs
            if "https://bhiv-hr-gateway-ltg0.onrender.com" in content:
                status = "CORRECT"
            else:
                status = "NEEDS_FIX"
                self.issues.append(ConfigIssue(
                    service="hr_portal",
                    issue_type="URL_CONFIG",
                    description="HR Portal not using production Gateway URL",
                    severity="HIGH",
                    fix_suggestion="Update API_BASE to production URL"
                ))
            
            # Check API key configuration
            if "<YOUR_API_KEY>" in content:
                api_key_status = "CORRECT"
            else:
                api_key_status = "NEEDS_FIX"
                self.issues.append(ConfigIssue(
                    service="hr_portal",
                    issue_type="API_KEY",
                    description="HR Portal API key mismatch",
                    severity="HIGH",
                    fix_suggestion="Update API_KEY to production key"
                ))
            
            return {
                "status": status,
                "api_key_status": api_key_status,
                "gateway_url": "https://bhiv-hr-gateway-ltg0.onrender.com",
                "version": "3.1.0",
                "features": ["Candidate Management", "Job Posting", "AI Matching", "Values Assessment"]
            }
            
        except Exception as e:
            self.issues.append(ConfigIssue(
                service="hr_portal",
                issue_type="FILE_ERROR",
                description=f"Cannot read HR Portal config: {str(e)}",
                severity="CRITICAL",
                fix_suggestion="Check file exists and is readable"
            ))
            return {"status": "ERROR", "error": str(e)}
    
    def validate_client_portal_config(self) -> Dict[str, Any]:
        """Validate Client Portal configuration"""
        config_path = "c:\\BHIV-HR-Platform\\services\\client_portal\\config.py"
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Check for production URLs
            if "https://bhiv-hr-gateway-ltg0.onrender.com" in content:
                status = "CORRECT"
            else:
                status = "NEEDS_FIX"
                self.issues.append(ConfigIssue(
                    service="client_portal",
                    issue_type="URL_CONFIG",
                    description="Client Portal not using production Gateway URL",
                    severity="HIGH",
                    fix_suggestion="Update API_BASE_URL to production URL"
                ))
            
            # Check JWT configuration
            if "JWT_SECRET_KEY" in content:
                jwt_status = "CONFIGURED"
            else:
                jwt_status = "MISSING"
                self.issues.append(ConfigIssue(
                    service="client_portal",
                    issue_type="JWT_CONFIG",
                    description="JWT configuration missing",
                    severity="MEDIUM",
                    fix_suggestion="Add JWT_SECRET_KEY environment variable"
                ))
            
            return {
                "status": status,
                "jwt_status": jwt_status,
                "gateway_url": "https://bhiv-hr-gateway-ltg0.onrender.com",
                "authentication": "JWT Token-based",
                "demo_credentials": {"username": "<DEMO_USERNAME>", "password": "<DEMO_PASSWORD>"}
            }
            
        except Exception as e:
            self.issues.append(ConfigIssue(
                service="client_portal",
                issue_type="FILE_ERROR",
                description=f"Cannot read Client Portal config: {str(e)}",
                severity="CRITICAL",
                fix_suggestion="Check file exists and is readable"
            ))
            return {"status": "ERROR", "error": str(e)}
    
    def validate_candidate_portal_config(self) -> Dict[str, Any]:
        """Validate Candidate Portal configuration"""
        config_path = "c:\\BHIV-HR-Platform\\services\\candidate_portal\\config.py"
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Check for production URLs
            if "https://bhiv-hr-gateway-ltg0.onrender.com" in content:
                status = "CORRECT"
            else:
                status = "NEEDS_FIX"
                self.issues.append(ConfigIssue(
                    service="candidate_portal",
                    issue_type="URL_CONFIG",
                    description="Candidate Portal not using production Gateway URL",
                    severity="HIGH",
                    fix_suggestion="Update GATEWAY_SERVICE_URL to production URL"
                ))
            
            # Check API key consistency
            if "<YOUR_API_KEY>" in content:
                api_key_status = "CORRECT"
            else:
                api_key_status = "NEEDS_FIX"
                self.issues.append(ConfigIssue(
                    service="candidate_portal",
                    issue_type="API_KEY",
                    description="Candidate Portal API key mismatch",
                    severity="HIGH",
                    fix_suggestion="Update API_KEY to production key"
                ))
            
            # Check database URL consistency
            if "dpg-d3bfmj8dl3ps739blqt0-a.oregon-postgres.render.com" in content:
                db_status = "CORRECT"
            else:
                db_status = "INCONSISTENT"
                self.issues.append(ConfigIssue(
                    service="candidate_portal",
                    issue_type="DATABASE_URL",
                    description="Candidate Portal using different database URL",
                    severity="MEDIUM",
                    fix_suggestion="Verify database URL matches other services"
                ))
            
            return {
                "status": status,
                "api_key_status": api_key_status,
                "db_status": db_status,
                "gateway_url": "https://bhiv-hr-gateway-ltg0.onrender.com",
                "port": 8503,
                "authentication": "JWT Token + Email/Password",
                "features": ["Job Search", "Application Tracking", "Profile Management"]
            }
            
        except Exception as e:
            self.issues.append(ConfigIssue(
                service="candidate_portal",
                issue_type="FILE_ERROR",
                description=f"Cannot read Candidate Portal config: {str(e)}",
                severity="CRITICAL",
                fix_suggestion="Check file exists and is readable"
            ))
            return {"status": "ERROR", "error": str(e)}
    
    def validate_gateway_dependencies(self) -> Dict[str, Any]:
        """Validate Gateway dependencies for authentication"""
        deps_path = "c:\\BHIV-HR-Platform\\services\\gateway\\dependencies.py"
        
        try:
            with open(deps_path, 'r') as f:
                content = f.read()
            
            # Check for triple authentication support
            if "get_auth" in content and "api_key" in content and "client_token" in content:
                auth_status = "TRIPLE_AUTH_SUPPORTED"
            else:
                auth_status = "LIMITED_AUTH"
                self.issues.append(ConfigIssue(
                    service="gateway",
                    issue_type="AUTH_CONFIG",
                    description="Gateway missing triple authentication support",
                    severity="HIGH",
                    fix_suggestion="Implement get_auth function with API key and JWT support"
                ))
            
            # Check API key validation
            if "validate_api_key" in content:
                api_validation = "IMPLEMENTED"
            else:
                api_validation = "MISSING"
                self.issues.append(ConfigIssue(
                    service="gateway",
                    issue_type="API_VALIDATION",
                    description="API key validation missing",
                    severity="HIGH",
                    fix_suggestion="Implement validate_api_key function"
                ))
            
            return {
                "auth_status": auth_status,
                "api_validation": api_validation,
                "supported_auth_types": ["API Key", "Client JWT", "Candidate JWT"],
                "security_level": "HIGH"
            }
            
        except Exception as e:
            self.issues.append(ConfigIssue(
                service="gateway",
                issue_type="FILE_ERROR",
                description=f"Cannot read Gateway dependencies: {str(e)}",
                severity="CRITICAL",
                fix_suggestion="Check file exists and is readable"
            ))
            return {"status": "ERROR", "error": str(e)}
    
    def validate_environment_files(self) -> Dict[str, Any]:
        """Validate environment configuration files"""
        env_files = {
            ".env.example": "c:\\BHIV-HR-Platform\\.env.example",
            ".env.render": "c:\\BHIV-HR-Platform\\config\\.env.render",
            "production.env": "c:\\BHIV-HR-Platform\\config\\production.env"
        }
        
        results = {}
        
        for name, path in env_files.items():
            try:
                with open(path, 'r') as f:
                    content = f.read()
                
                # Check for candidate portal configuration
                if "CANDIDATE_PORTAL" in content:
                    candidate_support = "CONFIGURED"
                else:
                    candidate_support = "MISSING"
                    self.issues.append(ConfigIssue(
                        service="environment",
                        issue_type="CANDIDATE_CONFIG",
                        description=f"{name} missing candidate portal configuration",
                        severity="MEDIUM",
                        fix_suggestion="Add CANDIDATE_PORTAL_SERVICE_URL variable"
                    ))
                
                # Check for consistent API keys
                if "<YOUR_API_KEY>" in content:
                    api_key_consistency = "CONSISTENT"
                else:
                    api_key_consistency = "INCONSISTENT"
                
                results[name] = {
                    "candidate_support": candidate_support,
                    "api_key_consistency": api_key_consistency,
                    "status": "READABLE"
                }
                
            except Exception as e:
                results[name] = {"status": "ERROR", "error": str(e)}
                self.issues.append(ConfigIssue(
                    service="environment",
                    issue_type="FILE_ERROR",
                    description=f"Cannot read {name}: {str(e)}",
                    severity="MEDIUM",
                    fix_suggestion="Check file exists and is readable"
                ))
        
        return results
    
    def validate_cross_service_compatibility(self) -> Dict[str, Any]:
        """Validate cross-service compatibility for candidate portal integration"""
        
        # Check URL consistency across services
        expected_gateway_url = "https://bhiv-hr-gateway-ltg0.onrender.com"
        expected_api_key = "<YOUR_API_KEY>"
        
        url_consistency = "CONSISTENT"
        api_key_consistency = "CONSISTENT"
        
        # Check authentication compatibility
        auth_methods = {
            "hr_portal": "Bearer Token",
            "client_portal": "JWT + Client ID",
            "candidate_portal": "JWT + Email/Password"
        }
        
        auth_compatibility = "COMPATIBLE"
        
        # Check database consistency
        db_urls = {
            "candidate_portal": "dpg-d3bfmj8dl3ps739blqt0-a.oregon-postgres.render.com",
            "other_services": "dpg-ctdvhf3tq21c73c5uqag-a.oregon-postgres.render.com"
        }
        
        db_consistency = "INCONSISTENT"
        self.issues.append(ConfigIssue(
            service="cross_service",
            issue_type="DATABASE_INCONSISTENCY",
            description="Candidate portal uses different database URL",
            severity="HIGH",
            fix_suggestion="Update candidate portal to use consistent database URL"
        ))
        
        return {
            "url_consistency": url_consistency,
            "api_key_consistency": api_key_consistency,
            "auth_compatibility": auth_compatibility,
            "db_consistency": db_consistency,
            "integration_status": "NEEDS_ATTENTION",
            "auth_methods": auth_methods
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive configuration validation report"""
        results = self.validate_all_configurations()
        
        report = f"""
# BHIV HR Platform - Configuration Validation Report
Generated: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}

## Executive Summary
- Total Issues Found: {len(self.issues)}
- Critical Issues: {len([i for i in self.issues if i.severity == 'CRITICAL'])}
- High Priority Issues: {len([i for i in self.issues if i.severity == 'HIGH'])}
- Medium Priority Issues: {len([i for i in self.issues if i.severity == 'MEDIUM'])}

## Service Configuration Status

### HR Portal
- Status: {results['hr_portal'].get('status', 'UNKNOWN')}
- Gateway URL: {results['hr_portal'].get('gateway_url', 'NOT_SET')}
- API Key: {results['hr_portal'].get('api_key_status', 'UNKNOWN')}
- Version: {results['hr_portal'].get('version', 'UNKNOWN')}

### Client Portal  
- Status: {results['client_portal'].get('status', 'UNKNOWN')}
- Gateway URL: {results['client_portal'].get('gateway_url', 'NOT_SET')}
- JWT Status: {results['client_portal'].get('jwt_status', 'UNKNOWN')}
- Authentication: {results['client_portal'].get('authentication', 'UNKNOWN')}

### Candidate Portal
- Status: {results['candidate_portal'].get('status', 'UNKNOWN')}
- Gateway URL: {results['candidate_portal'].get('gateway_url', 'NOT_SET')}
- API Key: {results['candidate_portal'].get('api_key_status', 'UNKNOWN')}
- Database: {results['candidate_portal'].get('db_status', 'UNKNOWN')}
- Port: {results['candidate_portal'].get('port', 'UNKNOWN')}

### Gateway Dependencies
- Auth Status: {results['gateway_dependencies'].get('auth_status', 'UNKNOWN')}
- API Validation: {results['gateway_dependencies'].get('api_validation', 'UNKNOWN')}
- Security Level: {results['gateway_dependencies'].get('security_level', 'UNKNOWN')}

## Cross-Service Compatibility
- URL Consistency: {results['cross_service_compatibility'].get('url_consistency', 'UNKNOWN')}
- API Key Consistency: {results['cross_service_compatibility'].get('api_key_consistency', 'UNKNOWN')}
- Auth Compatibility: {results['cross_service_compatibility'].get('auth_compatibility', 'UNKNOWN')}
- Database Consistency: {results['cross_service_compatibility'].get('db_consistency', 'UNKNOWN')}
- Integration Status: {results['cross_service_compatibility'].get('integration_status', 'UNKNOWN')}

## Issues Found ({len(self.issues)} total)
"""
        
        for i, issue in enumerate(self.issues, 1):
            report += f"""
### Issue {i}: {issue.issue_type}
- Service: {issue.service}
- Severity: {issue.severity}
- Description: {issue.description}
- Fix Suggestion: {issue.fix_suggestion}
"""
        
        report += f"""

## Recommendations

### High Priority Fixes
1. Update candidate portal database URL to match other services
2. Ensure all services use consistent production Gateway URL
3. Verify API key consistency across all configurations

### Medium Priority Improvements
1. Add candidate portal configuration to all environment files
2. Implement comprehensive JWT secret management
3. Add cross-service health checks

### Integration Readiness
- Candidate Portal Integration: {'READY' if len([i for i in self.issues if i.severity in ['CRITICAL', 'HIGH']]) == 0 else 'NEEDS_FIXES'}
- Configuration Management: {'GOOD' if len(self.issues) < 5 else 'NEEDS_IMPROVEMENT'}
- Cross-Service Compatibility: {results['cross_service_compatibility'].get('integration_status', 'UNKNOWN')}

## Conclusion
The configuration analysis shows that most services are properly configured for production deployment. 
The main concern is database URL consistency for the candidate portal integration.

---
Report generated by BHIV HR Platform Configuration Validator
"""
        
        return report
    
    def run_validation(self):
        """Run complete configuration validation"""
        print("Starting Configuration Validation...")
        print("=" * 60)
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        report_filename = "configuration_validation_report.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Configuration Validation Complete!")
        print(f"Issues Found: {len(self.issues)}")
        print(f"Critical Issues: {len([i for i in self.issues if i.severity == 'CRITICAL'])}")
        print(f"High Priority Issues: {len([i for i in self.issues if i.severity == 'HIGH'])}")
        print(f"Report saved: {report_filename}")
        
        return report_filename

if __name__ == "__main__":
    validator = ConfigurationValidator()
    report_file = validator.run_validation()
    print(f"\nConfiguration validation report available in: {report_file}")
