"""
Comprehensive Validation Script for Sovereign Application Runtime (SAR)

This script performs comprehensive validation of the entire framework
by testing actual API endpoints and verifying functionality.
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add the runtime-core directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FrameworkValidator:
    """Validates the Sovereign Application Runtime (SAR) components"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = "default_sar_api_key"  # Default API key for testing
        self.session = None
        self.auth_token = None
        self.test_data = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def get_headers(self, use_auth_token: bool = False):
        """Get appropriate headers for requests"""
        headers = {"Content-Type": "application/json"}
        if use_auth_token and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def test_health_check(self):
        """Test basic health check endpoint"""
        print("Testing health check endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                result = await response.json()
                assert response.status == 200
                assert "status" in result
                assert result["status"] == "healthy"
                print("✓ Health check endpoint working")
                return True
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False
    
    async def test_ready_check(self):
        """Test ready check endpoint"""
        print("Testing ready check endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/ready") as response:
                result = await response.json()
                assert response.status == 200
                assert "status" in result
                assert result["status"] == "ready"
                print("✓ Ready check endpoint working")
                return True
        except Exception as e:
            print(f"✗ Ready check failed: {e}")
            return False
    
    async def test_auth_service(self):
        """Test authentication service endpoints"""
        print("Testing authentication service...")
        success = True
        
        # Test 2FA setup
        try:
            user_id = f"test_user_{uuid.uuid4()}"
            payload = {"user_id": user_id}
            async with self.session.post(
                f"{self.base_url}/auth/2fa/setup",
                headers=self.get_headers(),
                json=payload
            ) as response:
                result = await response.json()
                assert response.status == 200
                assert "user_id" in result
                print("✓ 2FA setup endpoint working")
                
                # Store test user ID for later use
                self.test_data["test_user_id"] = user_id
        except Exception as e:
            print(f"✗ 2FA setup failed: {e}")
            success = False
        
        # Test password validation
        try:
            payload = {"password": "MySecure@Test123"}
            async with self.session.post(
                f"{self.base_url}/auth/password/validate",
                headers=self.get_headers(),
                json=payload
            ) as response:
                result = await response.json()
                assert response.status == 200
                assert "is_valid" in result
                print("✓ Password validation endpoint working")
        except Exception as e:
            print(f"✗ Password validation failed: {e}")
            success = False
        
        # Test password generation
        try:
            async with self.session.get(
                f"{self.base_url}/auth/password/generate",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                assert "generated_password" in result
                print("✓ Password generation endpoint working")
        except Exception as e:
            print(f"✗ Password generation failed: {e}")
            success = False
        
        # Test password policy
        try:
            async with self.session.get(
                f"{self.base_url}/auth/password/policy",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                assert "min_length" in result
                print("✓ Password policy endpoint working")
        except Exception as e:
            print(f"✗ Password policy failed: {e}")
            success = False
        
        return success
    
    async def test_tenant_service(self):
        """Test tenant service endpoints"""
        print("Testing tenant service...")
        success = True
        
        # Test current tenant endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/tenants/current",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                assert "tenant_id" in result
                print("✓ Current tenant endpoint working")
        except Exception as e:
            print(f"✗ Current tenant failed: {e}")
            success = False
        
        # Test tenant isolation check
        try:
            async with self.session.get(
                f"{self.base_url}/tenants/isolation-check/test_tenant",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Tenant isolation check endpoint working")
        except Exception as e:
            print(f"✗ Tenant isolation check failed: {e}")
            success = False
        
        # Test query filter endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/tenants/query-filter/users",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Query filter endpoint working")
        except Exception as e:
            print(f"✗ Query filter failed: {e}")
            success = False
        
        return success
    
    async def test_role_service(self):
        """Test role enforcement service endpoints"""
        print("Testing role enforcement service...")
        success = True
        
        # Test available roles endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/role/available-roles",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                assert "roles" in result
                print("✓ Available roles endpoint working")
        except Exception as e:
            print(f"✗ Available roles failed: {e}")
            success = False
        
        # Test current user endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/role/current",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Current user endpoint working")
        except Exception as e:
            print(f"✗ Current user failed: {e}")
            success = False
        
        # Test permissions endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/role/permissions",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Permissions endpoint working")
        except Exception as e:
            print(f"✗ Permissions failed: {e}")
            success = False
        
        # Test permission check
        try:
            payload = {"resource": "workflow", "action": "read"}
            async with self.session.post(
                f"{self.base_url}/role/check-permission",
                headers=self.get_headers(),
                json=payload
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Permission check endpoint working")
        except Exception as e:
            print(f"✗ Permission check failed: {e}")
            success = False
        
        return success
    
    async def test_audit_service(self):
        """Test audit logging service endpoints"""
        print("Testing audit logging service...")
        success = True
        
        # Test audit events endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/audit/events",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Audit events endpoint working")
        except Exception as e:
            print(f"✗ Audit events failed: {e}")
            success = False
        
        # Test audit stats endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/audit/stats",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Audit stats endpoint working")
        except Exception as e:
            print(f"✗ Audit stats failed: {e}")
            success = False
        
        # Test custom audit logging (using a valid event type)
        try:
            params = {
                "event_type": "api_access",
                "resource": "test_resource",
                "action": "test_action"
            }
            url = f"{self.base_url}/audit/log-custom"
            # Build URL with query parameters
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{param_str}"
            
            async with self.session.post(
                full_url,
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Custom audit logging endpoint working")
        except Exception as e:
            print(f"✗ Custom audit logging failed: {e}")
            success = False
        
        return success
    
    async def test_workflow_service(self):
        """Test workflow engine service endpoints"""
        print("Testing workflow engine service...")
        success = True
        
        # Test workflow definitions endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/workflow/definitions",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Workflow definitions endpoint working")
        except Exception as e:
            print(f"✗ Workflow definitions failed: {e}")
            success = False
        
        # Test workflow instances endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/workflow/instances",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Workflow instances endpoint working")
        except Exception as e:
            print(f"✗ Workflow instances failed: {e}")
            success = False
        
        # Test health check for workflow
        try:
            async with self.session.get(
                f"{self.base_url}/workflow/health",
                headers=self.get_headers()
            ) as response:
                result = await response.json()
                assert response.status == 200
                print("✓ Workflow health endpoint working")
        except Exception as e:
            print(f"✗ Workflow health failed: {e}")
            success = False
        
        return success
    
    async def run_all_tests(self):
        """Run all validation tests"""
        print("=" * 60)
        print("BHIV Application Framework - Comprehensive Validation")
        print("=" * 60)
        
        results = {}
        
        # Run all tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Ready Check", self.test_ready_check),
            ("Authentication Service", self.test_auth_service),
            ("Tenant Service", self.test_tenant_service),
            ("Role Service", self.test_role_service),
            ("Audit Service", self.test_audit_service),
            ("Workflow Service", self.test_workflow_service),
        ]
        
        for test_name, test_func in tests:
            print(f"\n--- Testing {test_name} ---")
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"✗ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Generate summary
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test_name:<30} [{status:^6}]")
        
        print("-" * 60)
        print(f"TOTAL: {passed}/{total} tests passed")
        print(f"SUCCESS RATE: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Framework is ready for production.")
            return True
        else:
            print(f"\n⚠️  {total-passed} tests failed. Framework requires attention.")
            return False


async def main():
    """Main function to run validation"""
    validator = FrameworkValidator()
    
    async with validator:
        success = await validator.run_all_tests()
        return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)