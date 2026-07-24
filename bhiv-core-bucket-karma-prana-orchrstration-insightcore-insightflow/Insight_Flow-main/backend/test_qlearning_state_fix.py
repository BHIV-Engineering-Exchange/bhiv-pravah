#!/usr/bin/env python3
"""
Test script to verify Q-learning state representation improvements
"""

import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_qlearning_state_representation():
    """Test enhanced Q-learning state representation"""
    
    print("🧪 Testing Q-learning state representation improvements...")
    
    try:
        from services.q_learning import QLearningRouter
        
        # Create test router
        router = QLearningRouter(learning_rate=0.1, epsilon=0.1)
        
        # Test 1: Basic state representation
        print("\n1. Testing enhanced state representation...")
        
        basic_context = {
            "input_type": "text",
            "priority": "high",
            "domain": "weather",
            "user_id": "user123"
        }
        
        state = router._get_state_representation(basic_context)
        print(f"   Basic state: {state}")
        
        # Test 2: Complex context
        print("\n2. Testing complex context...")
        
        complex_context = {
            "input_type": "image",
            "priority": "critical", 
            "domain": "medical",
            "user_id": "doctor456",
            "preferences": {"min_confidence": 0.9},
            "load_balancing": "prefer_fast"
        }
        
        complex_state = router._get_state_representation(complex_context)
        print(f"   Complex state: {complex_state}")
        
        # Test 3: State feature extraction
        print("\n3. Testing state feature extraction...")
        
        features = router._extract_state_features(complex_state)
        print(f"   Extracted features: {features}")
        
        # Test 4: Different time periods
        print("\n4. Testing time-based features...")
        
        # Mock different times by testing the logic
        current_hour = datetime.now().hour
        time_period = "night" if current_hour < 6 or current_hour > 22 else "day"
        print(f"   Current time period: {time_period} (hour: {current_hour})")
        
        # Test 5: State comparison
        print("\n5. Testing state differentiation...")
        
        context1 = {"input_type": "text", "priority": "normal"}
        context2 = {"input_type": "text", "priority": "high"}
        
        state1 = router._get_state_representation(context1)
        state2 = router._get_state_representation(context2)
        
        print(f"   Normal priority: {state1}")
        print(f"   High priority: {state2}")
        print(f"   States different: {state1 != state2}")
        
        # Test 6: Statistics with enhanced features
        print("\n6. Testing enhanced statistics...")
        
        # Add some mock Q-values to test statistics
        router.q_table[(state1, "agent1")] = 0.8
        router.q_table[(state2, "agent2")] = 0.6
        
        stats = router.get_statistics()
        print(f"   Q-table size: {stats['q_table_size']}")
        print(f"   States explored: {stats['states_explored']}")
        
        if "state_feature_distribution" in stats:
            print("   ✅ State feature distribution available")
            for feature, distribution in stats["state_feature_distribution"].items():
                print(f"     {feature}: {distribution}")
        else:
            print("   ❌ State feature distribution missing")
        
        print("\n🎉 Q-learning state representation testing completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the backend directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_qlearning_state_representation()