#!/usr/bin/env python3
"""
Test script for persistence and caching fixes in InsightFlow project.

Tests:
1. Q-Table event-driven persistence
2. Karma service intelligent cache invalidation
"""

import os
import sys
import asyncio
import tempfile
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def test_q_table_persistence():
    """Test Q-table event-driven persistence"""
    print("💾 Testing Q-Table Persistence...")
    
    # Mock database for testing
    mock_db = Mock()
    mock_table = Mock()
    mock_db.table.return_value = mock_table
    mock_table.select.return_value.execute.return_value.data = []
    mock_table.upsert.return_value.execute.return_value = None
    
    with patch('app.services.q_learning.get_db', return_value=mock_db):
        from app.services.q_learning import QLearningRouter
        
        # Create Q-learning router
        router = QLearningRouter()
        
        # Test 1: Initial state - no unsaved updates
        if router._unsaved_updates != 0:
            print("❌ FAIL: Initial unsaved updates should be 0")
            return False
        print("✅ PASS: Initial state correct")
        
        # Test 2: Update Q-value should increment unsaved counter
        router.update_q_value("state1", "agent1", 0.5, "state2", ["agent1", "agent2"])
        
        if router._unsaved_updates != 1:
            print(f"❌ FAIL: Expected 1 unsaved update, got {router._unsaved_updates}")
            return False
        print("✅ PASS: Unsaved updates tracked correctly")
        
        # Test 3: Multiple updates should trigger save at threshold
        router._save_threshold = 3  # Lower threshold for testing
        
        for i in range(2):  # Add 2 more updates (total 3)
            router.update_q_value(f"state{i+2}", "agent1", 0.5, f"state{i+3}", ["agent1"])
        
        # Should have triggered save and reset counter
        if router._unsaved_updates != 0:
            print(f"❌ FAIL: Expected 0 unsaved updates after threshold, got {router._unsaved_updates}")
            return False
        print("✅ PASS: Threshold-based save works")
        
        # Test 4: Force save functionality
        router.update_q_value("state_force", "agent1", 0.8, "state_next", ["agent1"])
        
        if router._unsaved_updates != 1:
            print("❌ FAIL: Should have 1 unsaved update before force save")
            return False
        
        router.force_save_q_table()
        
        if router._unsaved_updates != 0:
            print("❌ FAIL: Force save should reset unsaved updates to 0")
            return False
        print("✅ PASS: Force save works correctly")
        
        # Test 5: Time-based save (simulate)
        router._save_interval = 1  # 1 second for testing
        router._last_save_time = datetime.now() - timedelta(seconds=2)  # 2 seconds ago
        
        router.update_q_value("state_time", "agent1", 0.3, "state_time_next", ["agent1"])
        
        # Should trigger time-based save
        if router._unsaved_updates != 0:
            print("❌ FAIL: Time-based save should have been triggered")
            return False
        print("✅ PASS: Time-based save works")
        
        return True


async def test_karma_cache_invalidation():
    """Test Karma service intelligent cache invalidation"""
    print("🧠 Testing Karma Cache Invalidation...")
    
    from app.services.karma_service import KarmaServiceClient
    
    # Create karma service
    karma_service = KarmaServiceClient(
        karma_endpoint="http://test-endpoint",
        cache_ttl=300,  # 5 minutes
        enabled=True
    )
    
    # Test 1: Basic cache functionality
    agent_id = "test-agent-123"
    
    # Manually add cache entry with performance baseline
    karma_service._karma_cache[agent_id] = (0.5, datetime.utcnow(), 0.5)
    
    if not karma_service._is_cached(agent_id):
        print("❌ FAIL: Agent should be cached")
        return False
    print("✅ PASS: Basic caching works")
    
    # Test 2: Performance-based cache invalidation
    karma_service._invalidation_threshold = 0.1  # 10% change threshold
    
    # Add performance history that shows significant change
    karma_service._performance_history[agent_id] = [0.3, 0.3, 0.3, 0.3, 0.3]  # Consistent low performance
    
    # Should invalidate cache due to performance drift (0.5 baseline vs 0.3 recent avg)
    if karma_service._is_cached(agent_id):
        print("❌ FAIL: Cache should be invalidated due to performance drift")
        return False
    print("✅ PASS: Performance-based cache invalidation works")
    
    # Test 3: Update agent performance and auto-invalidation
    karma_service._karma_cache[agent_id] = (0.8, datetime.utcnow(), 0.8)  # Re-cache with high baseline
    
    # Update performance with significant change
    await karma_service.update_agent_performance(agent_id, 0.5)  # Significant drop
    
    # Add more measurements to trigger invalidation
    for score in [0.5, 0.5, 0.5]:
        await karma_service.update_agent_performance(agent_id, score)
    
    # Cache should be invalidated
    if agent_id in karma_service._karma_cache:
        print("❌ FAIL: Cache should be auto-invalidated after performance updates")
        return False
    print("✅ PASS: Auto-invalidation on performance updates works")
    
    # Test 4: Manual invalidation by performance change
    karma_service._karma_cache[agent_id] = (0.7, datetime.utcnow(), 0.7)
    
    # Trigger manual invalidation
    karma_service.invalidate_cache_by_performance_change(agent_id, 0.7, 0.4)  # 30% change
    
    if agent_id in karma_service._karma_cache:
        print("❌ FAIL: Manual invalidation should remove cache entry")
        return False
    print("✅ PASS: Manual performance-based invalidation works")
    
    # Test 5: No invalidation for small changes
    karma_service._karma_cache[agent_id] = (0.6, datetime.utcnow(), 0.6)
    
    # Small performance change (below threshold)
    karma_service.invalidate_cache_by_performance_change(agent_id, 0.6, 0.65)  # 5% change
    
    if agent_id not in karma_service._karma_cache:
        print("❌ FAIL: Small performance changes should not invalidate cache")
        return False
    print("✅ PASS: Small performance changes don't trigger invalidation")
    
    # Test 6: Enhanced metrics
    metrics = karma_service.get_metrics()
    
    required_keys = ['cache_size', 'avg_cache_age_seconds', 'performance_tracking_agents', 'invalidation_threshold']
    for key in required_keys:
        if key not in metrics:
            print(f"❌ FAIL: Missing metric key: {key}")
            return False
    
    if metrics['performance_tracking_agents'] != 1:  # Should track test-agent-123
        print(f"❌ FAIL: Expected 1 tracked agent, got {metrics['performance_tracking_agents']}")
        return False
    
    print("✅ PASS: Enhanced metrics reporting works")
    
    return True


async def test_integration_scenarios():
    """Test integration scenarios combining both fixes"""
    print("🔗 Testing Integration Scenarios...")
    
    # Mock database for Q-learning
    mock_db = Mock()
    mock_table = Mock()
    mock_db.table.return_value = mock_table
    mock_table.select.return_value.execute.return_value.data = []
    mock_table.upsert.return_value.execute.return_value = None
    
    with patch('app.services.q_learning.get_db', return_value=mock_db):
        from app.services.q_learning import QLearningRouter
        from app.services.karma_service import KarmaServiceClient
        
        # Create services
        q_router = QLearningRouter()
        karma_service = KarmaServiceClient(
            karma_endpoint="http://test-endpoint",
            enabled=True
        )
        
        # Test 1: Q-learning with frequent saves during high activity
        q_router._save_threshold = 5
        
        # Simulate high activity period
        for i in range(12):  # Should trigger 2 saves (at 5 and 10)
            q_router.update_q_value(f"state_{i}", "agent1", 0.5, f"next_state_{i}", ["agent1"])
        
        # Should have 2 unsaved updates (12 - 10)
        if q_router._unsaved_updates != 2:
            print(f"❌ FAIL: Expected 2 unsaved updates, got {q_router._unsaved_updates}")
            return False
        
        print("✅ PASS: Q-learning handles high activity with frequent saves")
        
        # Test 2: Karma cache invalidation during agent performance changes
        agent_id = "dynamic-agent"
        
        # Initial cache
        karma_service._karma_cache[agent_id] = (0.7, datetime.utcnow(), 0.7)
        
        # Simulate gradual performance degradation
        performance_scores = [0.65, 0.6, 0.55, 0.5, 0.45]
        
        for score in performance_scores:
            await karma_service.update_agent_performance(agent_id, score)
        
        # Cache should be invalidated due to significant drift
        if agent_id in karma_service._karma_cache:
            print("❌ FAIL: Cache should be invalidated after performance degradation")
            return False
        
        print("✅ PASS: Karma cache handles gradual performance changes")
        
        # Test 3: System shutdown simulation
        q_router.update_q_value("final_state", "agent1", 1.0, "end_state", ["agent1"])
        
        # Force save should work (simulating shutdown)
        q_router.force_save_q_table()
        
        if q_router._unsaved_updates != 0:
            print("❌ FAIL: Shutdown save should clear all unsaved updates")
            return False
        
        print("✅ PASS: System shutdown handling works")
        
        return True


async def run_all_tests():
    """Run all tests"""
    print("🚀 Running InsightFlow Persistence & Caching Fixes Tests\\n")
    
    tests = [
        ("Q-Table Persistence", test_q_table_persistence),
        ("Karma Cache Invalidation", test_karma_cache_invalidation),
        ("Integration Scenarios", test_integration_scenarios),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All persistence and caching fixes are working correctly!")
        return True
    else:
        print("⚠️ Some fixes need attention.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)