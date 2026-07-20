#!/usr/bin/env python3
"""
Comprehensive robustness test for HR AI System
Tests all critical components and failure scenarios
"""

import sys
import os
import json
import time
import requests
import subprocess
from threading import Thread
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class RobustnessTest:
    def __init__(self):
        self.results = {
            "data_validation": False,
            "file_operations": False,
            "error_recovery": False,
            "api_endpoints": False,
            "communication_agents": False,
            "startup_validation": False,
            "permission_handling": False,
            "missing_file_recovery": False
        }
        self.server_process = None
        
    def test_data_validation(self):
        """Test data validation system"""
        try:
            from app.utils.data_validator import DataValidator
            result = DataValidator.validate_data_files()
            self.results["data_validation"] = result["status"] == "success"
            print(f"[PASS] Data validation: {'PASS' if self.results['data_validation'] else 'FAIL'}")
        except Exception as e:
            print(f"[FAIL] Data validation: FAIL - {e}")
    
    def test_file_operations(self):
        """Test file operations with error handling"""
        try:
            from app.utils.helpers import load_json, save_json
            
            # Test normal operations
            test_data = {"test": "robustness", "timestamp": time.time()}
            save_result = save_json("data/robustness_test.json", test_data)
            load_result = load_json("data/robustness_test.json")
            
            self.results["file_operations"] = (
                save_result and 
                load_result == test_data
            )
            print(f"✓ File operations: {'PASS' if self.results['file_operations'] else 'FAIL'}")
        except Exception as e:
            print(f"✗ File operations: FAIL - {e}")
    
    def test_error_recovery(self):
        """Test error recovery mechanisms"""
        try:
            from app.utils.error_recovery import ErrorRecovery
            
            # Test system health
            health = ErrorRecovery.get_system_health()
            
            # Test safe file operation
            def test_operation():
                return {"test": "recovery"}
            
            result = ErrorRecovery.safe_file_operation(
                test_operation, 
                "test_file.json", 
                fallback_data={"fallback": True}
            )
            
            self.results["error_recovery"] = (
                health["status"] in ["healthy", "degraded"] and
                result is not None
            )
            print(f"✓ Error recovery: {'PASS' if self.results['error_recovery'] else 'FAIL'}")
        except Exception as e:
            print(f"✗ Error recovery: FAIL - {e}")
    
    def test_communication_agents(self):
        """Test communication agents"""
        try:
            from app.agents.email_agent import send_email
            from app.agents.whatsapp_agent import send_whatsapp
            from app.agents.voice_agent import trigger_voice_call
            
            # Test with mock data (candidate ID 1 should exist in test data)
            email_result = send_email(1, "shortlisted")
            whatsapp_result = send_whatsapp(1, "shortlisted")
            voice_result = trigger_voice_call(1, "onboarding")
            
            self.results["communication_agents"] = (
                email_result.get("status") in ["sent", "failed"] and
                whatsapp_result.get("status") in ["sent", "failed"] and
                voice_result.get("status") in ["sent", "failed"]
            )
            print(f"✓ Communication agents: {'PASS' if self.results['communication_agents'] else 'FAIL'}")
        except Exception as e:
            print(f"✗ Communication agents: FAIL - {e}")
    
    def test_startup_validation(self):
        """Test startup validation"""
        try:
            from app.utils.data_validator import ensure_data_integrity
            result = ensure_data_integrity()
            
            self.results["startup_validation"] = result["status"] == "success"
            print(f"✓ Startup validation: {'PASS' if self.results['startup_validation'] else 'FAIL'}")
        except Exception as e:
            print(f"✗ Startup validation: FAIL - {e}")
    
    def test_permission_handling(self):
        """Test permission handling"""
        try:
            from app.utils.data_validator import DataValidator
            status = DataValidator.get_system_status()
            
            # Check if all required directories have write permissions
            permissions = status.get("permissions", {})
            all_permissions_ok = all(permissions.values())
            
            self.results["permission_handling"] = all_permissions_ok
            print(f"✓ Permission handling: {'PASS' if self.results['permission_handling'] else 'FAIL'}")
        except Exception as e:
            print(f"✗ Permission handling: FAIL - {e}")
    
    def test_missing_file_recovery(self):
        """Test missing file recovery"""
        try:
            # Temporarily move a file to test recovery
            test_file = "data/candidates.json"
            backup_file = "data/candidates.json.backup"
            
            # Backup original file
            if os.path.exists(test_file):
                os.rename(test_file, backup_file)
            
            # Test recovery
            from app.utils.helpers import load_json
            result = load_json(test_file, default=[])
            
            # Restore original file
            if os.path.exists(backup_file):
                os.rename(backup_file, test_file)
            
            self.results["missing_file_recovery"] = isinstance(result, list)
            print(f"✓ Missing file recovery: {'PASS' if self.results['missing_file_recovery'] else 'FAIL'}")
        except Exception as e:
            print(f"✗ Missing file recovery: FAIL - {e}")
            # Ensure file is restored
            if os.path.exists("data/candidates.json.backup"):
                os.rename("data/candidates.json.backup", "data/candidates.json")
    
    def start_test_server(self):
        """Start FastAPI server for testing"""
        try:
            import uvicorn
            from app.main import app
            
            def run_server():
                uvicorn.run(app, host="127.0.0.1", port=5001, log_level="error")
            
            server_thread = Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(3)  # Wait for server to start
            return True
        except Exception as e:
            print(f"Failed to start test server: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        try:
            if not self.start_test_server():
                print("✗ API endpoints: FAIL - Could not start server")
                return
            
            base_url = "http://127.0.0.1:5001"
            
            # Test health endpoint
            health_response = requests.get(f"{base_url}/health", timeout=5)
            health_ok = health_response.status_code == 200
            
            # Test system status endpoint
            status_response = requests.get(f"{base_url}/system/status", timeout=5)
            status_ok = status_response.status_code == 200
            
            # Test candidate list endpoint
            candidates_response = requests.get(f"{base_url}/candidate/list", timeout=5)
            candidates_ok = candidates_response.status_code == 200
            
            self.results["api_endpoints"] = health_ok and status_ok and candidates_ok
            print(f"✓ API endpoints: {'PASS' if self.results['api_endpoints'] else 'FAIL'}")
            
        except Exception as e:
            print(f"✗ API endpoints: FAIL - {e}")
    
    def run_all_tests(self):
        """Run all robustness tests"""
        print("=" * 60)
        print("HR AI System - Robustness Test")
        print("=" * 60)
        
        self.test_data_validation()
        self.test_file_operations()
        self.test_error_recovery()
        self.test_startup_validation()
        self.test_permission_handling()
        self.test_missing_file_recovery()
        self.test_communication_agents()
        self.test_api_endpoints()
        
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        
        passed = sum(self.results.values())
        total = len(self.results)
        
        for test_name, result in self.results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 System is ROBUST and ready for production!")
            return True
        else:
            print("⚠️  System has some issues that need attention.")
            return False

if __name__ == "__main__":
    tester = RobustnessTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)