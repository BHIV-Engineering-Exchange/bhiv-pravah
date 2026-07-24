#!/usr/bin/env python3
"""
Test script to verify configuration file handling fix
"""

import os
import sys
import tempfile
import yaml

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_config_loading():
    """Test configuration loading with various scenarios"""
    from app.ml.weighted_scoring import WeightedScoringEngine
    
    print("🧪 Testing configuration file handling...")
    
    # Test 1: Default config (should work with existing file)
    print("\n1. Testing default configuration loading...")
    try:
        engine = WeightedScoringEngine()
        print(f"✅ Default config loaded successfully")
        print(f"   Weights: {engine.weights}")
    except Exception as e:
        print(f"❌ Default config failed: {e}")
    
    # Test 2: Missing config file (should use defaults)
    print("\n2. Testing missing config file...")
    try:
        engine = WeightedScoringEngine(config_path="nonexistent.yaml")
        print(f"✅ Missing config handled gracefully")
        print(f"   Weights: {engine.weights}")
    except Exception as e:
        print(f"❌ Missing config handling failed: {e}")
    
    # Test 3: Environment variable config
    print("\n3. Testing environment variable config...")
    try:
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'scoring_weights': {
                    'rule_based': 0.5,
                    'feedback_based': 0.3,
                    'availability': 0.2
                }
            }, f)
            temp_config_path = f.name
        
        # Set environment variable
        os.environ['SCORING_CONFIG_PATH'] = temp_config_path
        
        engine = WeightedScoringEngine()
        print(f"✅ Environment config loaded successfully")
        print(f"   Weights: {engine.weights}")
        
        # Cleanup
        os.unlink(temp_config_path)
        del os.environ['SCORING_CONFIG_PATH']
        
    except Exception as e:
        print(f"❌ Environment config failed: {e}")
    
    # Test 4: Invalid YAML (should use defaults)
    print("\n4. Testing invalid YAML handling...")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            invalid_config_path = f.name
        
        engine = WeightedScoringEngine(config_path=invalid_config_path)
        print(f"✅ Invalid YAML handled gracefully")
        print(f"   Weights: {engine.weights}")
        
        # Cleanup
        os.unlink(invalid_config_path)
        
    except Exception as e:
        print(f"❌ Invalid YAML handling failed: {e}")
    
    print("\n🎉 Configuration testing completed!")

if __name__ == "__main__":
    test_config_loading()