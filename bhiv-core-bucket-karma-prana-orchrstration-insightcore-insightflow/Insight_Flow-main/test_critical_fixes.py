#!/usr/bin/env python3
"""
Test script for critical fixes in InsightFlow project.

Tests:
1. STP Checksum Validation with rejection option
2. Routing Decision Logger atomic file writing
3. Weighted Scoring Engine robust normalization
"""

import asyncio
import json
import math
import tempfile
import os
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.middleware.stp_middleware import STPMiddleware, STPLayerError
from app.utils.routing_decision_logger import RoutingDecisionLogger
from app.ml.weighted_scoring import WeightedScoringEngine


def test_stp_checksum_validation():
    """Test STP checksum validation with strict mode"""
    print("🔐 Testing STP Checksum Validation...")
    
    # Test 1: Strict mode should reject corrupted packets
    stp_strict = STPMiddleware(enable_stp=True, strict_checksum=True)
    
    # Create valid packet
    payload = {"test": "data"}
    packet = stp_strict.wrap(payload, "routing_decision")
    
    # Corrupt the checksum
    packet["stp_checksum"] = "corrupted_checksum"
    
    try:
        stp_strict.unwrap(packet)
        print("❌ FAIL: Strict mode should have rejected corrupted packet")
        return False
    except STPLayerError as e:
        if "checksum failure" in str(e):
            print("✅ PASS: Strict mode correctly rejected corrupted packet")
        else:
            print(f"❌ FAIL: Wrong error type: {e}")
            return False
    
    # Test 2: Lenient mode should warn but continue
    stp_lenient = STPMiddleware(enable_stp=True, strict_checksum=False)
    
    try:
        payload_back, metadata = stp_lenient.unwrap(packet)
        print("✅ PASS: Lenient mode processed corrupted packet with warning")
    except Exception as e:
        print(f"❌ FAIL: Lenient mode should not reject: {e}")
        return False
    
    # Test 3: Check metrics
    metrics = stp_strict.get_metrics()
    if metrics["checksum_failures"] > 0:
        print("✅ PASS: Checksum failures tracked in metrics")
    else:
        print("❌ FAIL: Checksum failures not tracked")
        return False
    
    return True


def test_atomic_file_writing():
    """Test atomic file writing in routing decision logger"""
    print("📝 Testing Atomic File Writing...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create logger with temp directory
        logger = RoutingDecisionLogger(log_dir=temp_dir, log_file="test_routing.jsonl")
        
        # Test 1: Normal logging
        success = logger.log_decision(
            agent_selected="test-agent",
            confidence_score=0.85,
            request_id="test-123",
            context={"priority": "high"},
            reasoning="Test decision"
        )
        
        if not success:
            print("❌ FAIL: Basic logging failed")
            return False
        
        # Test 2: Verify file exists and has content
        log_file = Path(temp_dir) / "test_routing.jsonl"
        if not log_file.exists():
            print("❌ FAIL: Log file not created")
            return False
        
        with open(log_file, 'r') as f:
            content = f.read().strip()
            if not content:
                print("❌ FAIL: Log file is empty")
                return False
        
        # Test 3: Verify JSON structure
        try:
            log_entry = json.loads(content)
            required_fields = ["timestamp", "agent_selected", "confidence_score"]
            for field in required_fields:
                if field not in log_entry:
                    print(f"❌ FAIL: Missing field {field} in log entry")
                    return False
        except json.JSONDecodeError:
            print("❌ FAIL: Invalid JSON in log file")
            return False
        
        # Test 4: Multiple writes (atomic behavior)
        for i in range(5):
            logger.log_decision(
                agent_selected=f"agent-{i}",
                confidence_score=0.5 + i * 0.1,
                request_id=f"req-{i}",
                context={"test": i}
            )
        
        # Verify all entries are present
        with open(log_file, 'r') as f:
            lines = f.readlines()
            if len(lines) != 6:  # 1 initial + 5 new
                print(f"❌ FAIL: Expected 6 log entries, got {len(lines)}")
                return False
        
        print("✅ PASS: Atomic file writing works correctly")
        return True


def test_robust_normalization():
    """Test robust normalization in weighted scoring engine"""
    print("⚖️ Testing Robust Normalization...")
    
    # Create scoring engine with default config
    engine = WeightedScoringEngine(config_path=None)
    
    # Test 1: Normal scores
    confidence = engine.calculate_confidence(
        agent_id="test-agent",
        rule_based_score=0.8,
        feedback_score=0.7,
        availability_score=0.9
    )
    
    if not (0.0 <= confidence.final_score <= 1.0):
        print(f"❌ FAIL: Normal scores out of range: {confidence.final_score}")
        return False
    
    # Test 2: Edge case - NaN values
    try:
        confidence = engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=float('nan'),
            feedback_score=0.7,
            availability_score=0.9
        )
        if confidence.final_score != confidence.final_score:  # NaN check
            print("❌ FAIL: NaN not handled properly")
            return False
    except Exception as e:
        print(f"❌ FAIL: Exception with NaN input: {e}")
        return False
    
    # Test 3: Edge case - Infinite values
    try:
        confidence = engine.calculate_confidence(
            agent_id="test-agent",
            rule_based_score=float('inf'),
            feedback_score=0.7,
            availability_score=0.9
        )
        if not (0.0 <= confidence.final_score <= 1.0):
            print(f"❌ FAIL: Infinite values not normalized: {confidence.final_score}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Exception with infinite input: {e}")
        return False
    
    # Test 4: Out of range values
    confidence = engine.calculate_confidence(
        agent_id="test-agent",
        rule_based_score=2.5,  # Way out of range
        feedback_score=-0.5,   # Negative
        availability_score=1.8  # Above 1.0
    )
    
    if not (0.0 <= confidence.final_score <= 1.0):
        print(f"❌ FAIL: Out of range values not normalized: {confidence.final_score}")
        return False
    
    # Test 5: Extreme values requiring sigmoid normalization
    # This should trigger sigmoid normalization internally
    extreme_score = 5.0
    normalized = engine._normalize_score(extreme_score)
    
    if not (0.0 <= normalized <= 1.0):
        print(f"❌ FAIL: Extreme value not normalized: {normalized}")
        return False
    
    # Test 6: Verify score breakdown
    breakdown = confidence.get_breakdown()
    if "final_score" not in breakdown or "components" not in breakdown:
        print("❌ FAIL: Score breakdown missing required fields")
        return False
    
    print("✅ PASS: Robust normalization handles all edge cases")
    return True


async def run_all_tests():
    """Run all tests"""
    print("🚀 Running InsightFlow Critical Fixes Tests\n")
    
    tests = [
        ("STP Checksum Validation", test_stp_checksum_validation),
        ("Atomic File Writing", test_atomic_file_writing),
        ("Robust Normalization", test_robust_normalization),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
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
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All critical fixes are working correctly!")
        return True
    else:
        print("⚠️ Some fixes need attention.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)