#!/usr/bin/env python3
"""Simple robustness test for HR AI System"""

import sys
import os
import json

# Add project root to path
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_data_validation():
    """Test data validation system"""
    try:
        from app.utils.data_validator import DataValidator
        result = DataValidator.validate_data_files()
        return result["status"] == "success"
    except Exception as e:
        print(f"Data validation error: {e}")
        return False

def test_file_operations():
    """Test file operations"""
    try:
        from app.utils.helpers import load_json, save_json
        test_data = {"test": "data"}
        save_json("data/test.json", test_data)
        loaded = load_json("data/test.json")
        return loaded == test_data
    except Exception as e:
        print(f"File operations error: {e}")
        return False

def test_error_recovery():
    """Test error recovery"""
    try:
        from app.utils.error_recovery import ErrorRecovery
        health = ErrorRecovery.get_system_health()
        return health["status"] in ["healthy", "degraded"]
    except Exception as e:
        print(f"Error recovery error: {e}")
        return False

def test_communication_agents():
    """Test communication agents"""
    try:
        from app.agents.email_agent import send_email
        from app.agents.whatsapp_agent import send_whatsapp
        from app.agents.voice_agent import trigger_voice_call
        
        # Test with existing candidate
        email_result = send_email(1, "shortlisted")
        whatsapp_result = send_whatsapp(1, "shortlisted") 
        voice_result = trigger_voice_call(1, "onboarding")
        
        # All agents should return a status
        email_ok = email_result and "status" in email_result
        whatsapp_ok = whatsapp_result and "status" in whatsapp_result  
        voice_ok = voice_result and "status" in voice_result
        
        return email_ok and whatsapp_ok and voice_ok
    except Exception as e:
        print(f"Communication agents error: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI app loading"""
    try:
        from app.main import app
        return app is not None
    except Exception as e:
        print(f"FastAPI app error: {e}")
        return False

def main():
    """Run all tests"""
    print("HR AI System - Robustness Test")
    print("=" * 40)
    
    tests = [
        ("Data Validation", test_data_validation),
        ("File Operations", test_file_operations),
        ("Error Recovery", test_error_recovery),
        ("Communication Agents", test_communication_agents),
        ("FastAPI App", test_fastapi_app)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            status = "PASS" if result else "FAIL"
            print(f"{test_name}: {status}")
            results.append(result)
        except Exception as e:
            print(f"{test_name}: FAIL - {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print("=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("System is ROBUST!")
        return True
    else:
        print("System needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)