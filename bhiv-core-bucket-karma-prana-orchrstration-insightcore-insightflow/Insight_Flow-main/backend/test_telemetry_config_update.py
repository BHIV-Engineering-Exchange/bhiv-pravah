#!/usr/bin/env python3
"""
Test Telemetry Configuration Update

Verifies that the updated telemetry configuration works correctly
and maintains backward compatibility.
"""

import os
from app.core.config import Settings
from app.telemetry_bus.telemetry_security import get_telemetry_signer


def test_configuration_loading():
    """Test that telemetry configuration loads correctly"""
    print("⚙️  Testing configuration loading...")
    
    try:
        # Test with environment variables
        os.environ['ENABLE_TELEMETRY_SIGNING'] = 'true'
        os.environ['TELEMETRY_MAX_TIMESTAMP_DRIFT'] = '10'
        os.environ['TELEMETRY_SIGNATURE_TIMEOUT'] = '8'
        
        # Create settings instance
        settings = Settings()
        
        # Verify primary settings
        assert settings.ENABLE_TELEMETRY_SIGNING is True
        assert settings.TELEMETRY_MAX_TIMESTAMP_DRIFT == 10
        assert settings.TELEMETRY_SIGNATURE_TIMEOUT == 8
        
        print("✅ Primary configuration loaded correctly")
        print(f"   ENABLE_TELEMETRY_SIGNING: {settings.ENABLE_TELEMETRY_SIGNING}")
        print(f"   TELEMETRY_MAX_TIMESTAMP_DRIFT: {settings.TELEMETRY_MAX_TIMESTAMP_DRIFT}")
        print(f"   TELEMETRY_SIGNATURE_TIMEOUT: {settings.TELEMETRY_SIGNATURE_TIMEOUT}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False
    
    finally:
        # Clean up environment
        for key in ['ENABLE_TELEMETRY_SIGNING', 'TELEMETRY_MAX_TIMESTAMP_DRIFT', 'TELEMETRY_SIGNATURE_TIMEOUT']:
            if key in os.environ:
                del os.environ[key]


def test_backward_compatibility():
    """Test backward compatibility with old configuration names"""
    print("\n🔄 Testing backward compatibility...")
    
    try:
        # Test with old configuration names
        os.environ['TELEMETRY_PACKET_SIGNING'] = 'true'
        
        settings = Settings()
        
        # Should still work with old names
        assert settings.TELEMETRY_PACKET_SIGNING is True
        
        print("✅ Backward compatibility maintained")
        print(f"   TELEMETRY_PACKET_SIGNING: {settings.TELEMETRY_PACKET_SIGNING}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False
    
    finally:
        # Clean up environment
        if 'TELEMETRY_PACKET_SIGNING' in os.environ:
            del os.environ['TELEMETRY_PACKET_SIGNING']


def test_configuration_validation():
    """Test configuration validation"""
    print("\n🛡️  Testing configuration validation...")
    
    try:
        # Test valid values
        os.environ['TELEMETRY_MAX_TIMESTAMP_DRIFT'] = '30'
        os.environ['TELEMETRY_SIGNATURE_TIMEOUT'] = '15'
        
        settings = Settings()
        
        assert 1 <= settings.TELEMETRY_MAX_TIMESTAMP_DRIFT <= 60
        assert 1 <= settings.TELEMETRY_SIGNATURE_TIMEOUT <= 30
        
        print("✅ Configuration validation working")
        print(f"   Valid drift: {settings.TELEMETRY_MAX_TIMESTAMP_DRIFT}")
        print(f"   Valid timeout: {settings.TELEMETRY_SIGNATURE_TIMEOUT}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    
    finally:
        # Clean up environment
        for key in ['TELEMETRY_MAX_TIMESTAMP_DRIFT', 'TELEMETRY_SIGNATURE_TIMEOUT']:
            if key in os.environ:
                del os.environ[key]


def test_signer_configuration_integration():
    """Test that signer uses configuration correctly"""
    print("\n🔐 Testing signer configuration integration...")
    
    try:
        # Set configuration
        os.environ['TELEMETRY_MAX_TIMESTAMP_DRIFT'] = '15'
        os.environ['SOVEREIGN_JWT_SECRET'] = 'test-secret-key-for-configuration-testing-32chars'
        
        # Get signer (will use configuration)
        signer = get_telemetry_signer()
        
        # Verify signer uses configuration
        assert signer.max_drift == 15
        
        print("✅ Signer configuration integration working")
        print(f"   Signer max drift: {signer.max_drift}")
        
        return True
        
    except Exception as e:
        print(f"❌ Signer configuration integration failed: {e}")
        return False
    
    finally:
        # Clean up environment
        for key in ['TELEMETRY_MAX_TIMESTAMP_DRIFT', 'SOVEREIGN_JWT_SECRET']:
            if key in os.environ:
                del os.environ[key]
        
        # Reset global signer
        import app.telemetry_bus.telemetry_security
        app.telemetry_bus.telemetry_security._telemetry_signer = None


def test_default_values():
    """Test default configuration values"""
    print("\n📋 Testing default values...")
    
    try:
        # Clear any existing environment variables
        env_keys = [
            'ENABLE_TELEMETRY_SIGNING', 'TELEMETRY_PACKET_SIGNING',
            'TELEMETRY_MAX_TIMESTAMP_DRIFT', 'TELEMETRY_SIGNATURE_TIMEOUT'
        ]
        
        original_values = {}
        for key in env_keys:
            if key in os.environ:
                original_values[key] = os.environ[key]
                del os.environ[key]
        
        try:
            settings = Settings()
            
            # Check defaults
            assert settings.ENABLE_TELEMETRY_SIGNING is True  # Default enabled
            assert settings.TELEMETRY_PACKET_SIGNING is False  # Backward compatibility default
            assert settings.TELEMETRY_MAX_TIMESTAMP_DRIFT == 5
            assert settings.TELEMETRY_SIGNATURE_TIMEOUT == 5
            
            print("✅ Default values correct")
            print(f"   Default ENABLE_TELEMETRY_SIGNING: {settings.ENABLE_TELEMETRY_SIGNING}")
            print(f"   Default TELEMETRY_MAX_TIMESTAMP_DRIFT: {settings.TELEMETRY_MAX_TIMESTAMP_DRIFT}")
            
            return True
            
        finally:
            # Restore original environment
            for key, value in original_values.items():
                os.environ[key] = value
        
    except Exception as e:
        print(f"❌ Default values test failed: {e}")
        return False


def main():
    """Run all configuration tests"""
    print("🚀 Testing Telemetry Configuration Updates")
    print("=" * 50)
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Backward Compatibility", test_backward_compatibility),
        ("Configuration Validation", test_configuration_validation),
        ("Signer Configuration Integration", test_signer_configuration_integration),
        ("Default Values", test_default_values),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All configuration updates working correctly!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the configuration.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)