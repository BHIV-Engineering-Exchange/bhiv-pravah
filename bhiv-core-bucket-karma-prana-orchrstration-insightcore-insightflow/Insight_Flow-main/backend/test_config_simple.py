#!/usr/bin/env python3
"""
Simple test for configuration file handling
"""

import os
import tempfile
import yaml

def test_config_methods():
    """Test the configuration loading methods directly"""
    
    # Import the class directly to avoid circular imports
    import sys
    sys.path.insert(0, 'app')
    
    from ml.weighted_scoring import WeightedScoringEngine
    
    print("🧪 Testing configuration file handling methods...")
    
    # Create a test instance
    engine = WeightedScoringEngine.__new__(WeightedScoringEngine)
    
    # Test 1: Default config
    print("\n1. Testing default configuration...")
    default_config = engine._default_config()
    print(f"✅ Default config generated: {len(default_config)} keys")
    
    # Test 2: Config path finding
    print("\n2. Testing config path finding...")
    config_path = engine._find_config_path()
    if config_path:
        print(f"✅ Config file found at: {config_path}")
    else:
        print("ℹ️ No config file found, will use defaults")
    
    # Test 3: Load existing config
    print("\n3. Testing config loading...")
    if config_path and os.path.exists(config_path):
        config = engine._load_config(config_path)
        print(f"✅ Config loaded successfully: {len(config)} keys")
        print(f"   Scoring weights: {config.get('scoring_weights', {})}")
    else:
        print("ℹ️ Loading default config")
        config = engine._load_config(None)
        print(f"✅ Default config loaded: {len(config)} keys")
    
    # Test 4: Weight normalization
    print("\n4. Testing weight normalization...")
    test_weights = {'a': 0.3, 'b': 0.4, 'c': 0.2}  # Sum = 0.9
    normalized = engine._normalize_weights(test_weights)
    total = sum(normalized.values())
    print(f"✅ Weights normalized: {normalized} (sum: {total:.3f})")
    
    print("\n🎉 Configuration methods testing completed!")

if __name__ == "__main__":
    test_config_methods()