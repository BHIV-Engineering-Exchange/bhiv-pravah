#!/usr/bin/env python3
"""
Test script to verify STP error handling improvements
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_stp_error_handling():
    """Test STP error handling with various failure scenarios"""
    
    print("🧪 Testing STP error handling improvements...")
    
    try:
        from services.stp_service import STPService
        from middleware.stp_middleware import STPMiddleware, STPLayerError
        
        # Test 1: Normal STP service operation
        print("\n1. Testing normal STP service operation...")
        stp_service = STPService()
        
        # Test routing decision wrapping
        routing_decision = {
            "agent_id": "test-agent",
            "confidence_score": 0.85,
            "request_id": "test-123"
        }
        
        try:
            wrapped = await stp_service.wrap_routing_decision(routing_decision)
            if "stp_wrapping_failed" in wrapped:
                print(f"❌ Wrapping failed: {wrapped.get('stp_error')}")
            else:
                print(f"✅ Routing decision wrapped successfully")
        except Exception as e:
            print(f"❌ Wrapping error: {e}")
        
        # Test 2: Simulate wrapping failure by disabling STP
        print("\n2. Testing STP wrapping failure handling...")
        
        # Create a middleware that will fail
        class FailingSTPMiddleware(STPMiddleware):
            def wrap(self, *args, **kwargs):
                raise STPLayerError("Simulated wrapping failure")
        
        # Replace middleware temporarily
        original_middleware = stp_service.stp_middleware
        stp_service.stp_middleware = FailingSTPMiddleware()
        
        try:
            wrapped = await stp_service.wrap_routing_decision(routing_decision)
            if wrapped.get("stp_wrapping_failed"):
                print(f"✅ Failure handled gracefully: {wrapped.get('stp_error')}")
                print(f"   Original data preserved: {wrapped.get('agent_id')}")
            else:
                print(f"❌ Failure not properly handled")
        except Exception as e:
            print(f"❌ Unhandled exception: {e}")
        
        # Restore original middleware
        stp_service.stp_middleware = original_middleware
        
        # Test 3: Check metrics tracking
        print("\n3. Testing metrics tracking...")
        metrics = stp_service.get_stp_metrics()
        print(f"✅ Metrics available: {list(metrics.keys())}")
        
        if "wrapping_failures" in metrics:
            print(f"   Wrapping failures: {metrics['wrapping_failures']}")
            print(f"   Fallback responses: {metrics['fallback_responses']}")
        
        # Test 4: Check failure rate monitoring
        print("\n4. Testing failure rate monitoring...")
        failure_status = stp_service.check_failure_rates()
        print(f"✅ Failure rate status: {failure_status['status']}")
        print(f"   Current failure rate: {failure_status['failure_rate']:.1%}")
        
        if failure_status['alerts']:
            for alert in failure_status['alerts']:
                print(f"   Alert: {alert['message']}")
        
        print("\n🎉 STP error handling testing completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the backend directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_stp_error_handling())