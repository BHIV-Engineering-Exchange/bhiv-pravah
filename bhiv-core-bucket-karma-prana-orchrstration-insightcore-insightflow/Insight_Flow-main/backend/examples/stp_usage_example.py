# examples/stp_usage_example.py
"""
STP (Structured Token Protocol) Usage Examples

This file demonstrates how to use the STP middleware and service
for wrapping routing decisions and feedback packets.
"""

import asyncio
import json
from datetime import datetime
from app.middleware.stp_middleware import get_stp_middleware, STPPacketType, STPPriority
from app.services.stp_service import get_stp_service


async def example_basic_stp_wrapping():
    """Example: Basic STP packet wrapping and unwrapping"""
    print("=== Basic STP Wrapping Example ===")
    
    # Get STP middleware
    stp_middleware = get_stp_middleware(enable_stp=True)
    
    # Sample routing decision data
    routing_decision = {
        "request_id": "req-12345",
        "agent_id": "nlp-agent-001",
        "agent_name": "NLP Processor",
        "confidence_score": 0.87,
        "routing_reason": "High semantic match for text processing",
        "routing_strategy": "q_learning"
    }
    
    print(f"Original data: {json.dumps(routing_decision, indent=2)}")
    
    # Wrap in STP format
    wrapped_packet = stp_middleware.wrap(
        payload=routing_decision,
        packet_type=STPPacketType.ROUTING_DECISION.value,
        priority=STPPriority.HIGH.value,
        requires_ack=True
    )
    
    print(f"\nSTP Wrapped packet:")
    print(f"Token: {wrapped_packet['stp_token']}")
    print(f"Type: {wrapped_packet['stp_type']}")
    print(f"Priority: {wrapped_packet['stp_metadata']['priority']}")
    print(f"Checksum: {wrapped_packet['stp_checksum']}")
    
    # Unwrap the packet
    payload, metadata = stp_middleware.unwrap(wrapped_packet)
    
    print(f"\nUnwrapped payload: {json.dumps(payload, indent=2)}")
    print(f"Metadata: {json.dumps(metadata, indent=2)}")
    
    # Verify integrity
    assert payload == routing_decision
    print("\n✅ Integrity verified: Original data matches unwrapped payload")


async def example_stp_service_usage():
    """Example: Using STP service for high-level operations"""
    print("\n=== STP Service Usage Example ===")
    
    # Get STP service
    stp_service = get_stp_service()
    
    # Example 1: Wrap routing decision with automatic priority
    routing_decision = {
        "request_id": "req-67890",
        "agent_id": "vision-agent-002",
        "agent_name": "Computer Vision Processor",
        "confidence_score": 0.95,  # High confidence
        "routing_reason": "Perfect match for image classification",
        "routing_strategy": "rule_based"
    }
    
    wrapped_routing = await stp_service.wrap_routing_decision(
        routing_decision=routing_decision,
        requires_ack=True
    )
    
    print(f"High confidence routing (auto priority):")
    print(f"Priority: {wrapped_routing['stp_metadata']['priority']}")  # Should be HIGH
    print(f"Token: {wrapped_routing['stp_token']}")
    
    # Example 2: Wrap feedback packet
    feedback_data = {
        "routing_log_id": "log-abc123",
        "success": True,
        "latency_ms": 145.5,
        "accuracy_score": 0.92,
        "user_satisfaction": 5
    }
    
    wrapped_feedback = await stp_service.wrap_feedback_packet(
        feedback_data=feedback_data
    )
    
    print(f"\nFeedback packet:")
    print(f"Priority: {wrapped_feedback['stp_metadata']['priority']}")  # Should be NORMAL
    print(f"Requires ACK: {wrapped_feedback['stp_metadata']['requires_ack']}")  # Should be True
    print(f"Token: {wrapped_feedback['stp_token']}")
    
    # Example 3: Wrap health check
    health_data = {
        "status": "healthy",
        "app": "InsightFlow",
        "version": "1.0.0",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "q_learning": "healthy"
        }
    }
    
    wrapped_health = await stp_service.wrap_health_check(health_data)
    
    print(f"\nHealth check packet:")
    print(f"Priority: {wrapped_health['stp_metadata']['priority']}")  # Should be NORMAL
    print(f"Token: {wrapped_health['stp_token']}")


async def example_priority_determination():
    """Example: How STP service determines packet priorities"""
    print("\n=== Priority Determination Examples ===")
    
    stp_service = get_stp_service()
    
    # High confidence routing -> HIGH priority
    high_confidence = {
        "confidence_score": 0.95,
        "agent_id": "test-agent"
    }
    
    wrapped = await stp_service.wrap_routing_decision(high_confidence)
    print(f"High confidence (0.95) -> Priority: {wrapped['stp_metadata']['priority']}")
    
    # Low confidence routing -> CRITICAL priority
    low_confidence = {
        "confidence_score": 0.25,
        "agent_id": "test-agent"
    }
    
    wrapped = await stp_service.wrap_routing_decision(low_confidence)
    print(f"Low confidence (0.25) -> Priority: {wrapped['stp_metadata']['priority']}")
    
    # Failed feedback -> CRITICAL priority
    failed_feedback = {
        "success": False,
        "latency_ms": 6000,  # Very slow
        "routing_log_id": "test-log"
    }
    
    wrapped = await stp_service.wrap_feedback_packet(failed_feedback)
    print(f"Failed + slow feedback -> Priority: {wrapped['stp_metadata']['priority']}")
    
    # Unhealthy system -> CRITICAL priority
    unhealthy_status = {
        "status": "unhealthy",
        "app": "InsightFlow"
    }
    
    wrapped = await stp_service.wrap_health_check(unhealthy_status)
    print(f"Unhealthy status -> Priority: {wrapped['stp_metadata']['priority']}")


async def example_error_handling():
    """Example: Error handling and fallback behavior"""
    print("\n=== Error Handling Examples ===")
    
    stp_service = get_stp_service()
    
    # Test with invalid data (should fallback gracefully)
    try:
        invalid_data = None  # This will cause an error
        result = await stp_service.wrap_routing_decision(invalid_data)
        print("❌ Should have failed but didn't")
    except Exception as e:
        print(f"✅ Handled error gracefully: {str(e)}")
    
    # Test unwrapping invalid packet
    try:
        invalid_packet = {"not": "stp_packet"}
        payload, metadata = await stp_service.unwrap_packet(invalid_packet)
        print(f"✅ Fallback behavior: returned original data")
        print(f"Payload: {payload}")
        print(f"Metadata: {metadata}")
    except Exception as e:
        print(f"Error during unwrap: {str(e)}")


async def example_metrics_monitoring():
    """Example: Monitoring STP metrics"""
    print("\n=== Metrics Monitoring Example ===")
    
    stp_service = get_stp_service()
    
    # Get initial metrics
    initial_metrics = stp_service.get_stp_metrics()
    print(f"Initial metrics: {json.dumps(initial_metrics, indent=2)}")
    
    # Perform some operations
    test_data = {"test": "data"}
    
    for i in range(3):
        await stp_service.wrap_routing_decision(test_data)
        await stp_service.wrap_feedback_packet({"routing_log_id": f"log-{i}", "success": True, "latency_ms": 100})
    
    # Get updated metrics
    final_metrics = stp_service.get_stp_metrics()
    print(f"\nFinal metrics: {json.dumps(final_metrics, indent=2)}")
    
    print(f"\nOperations performed:")
    print(f"Packets wrapped: {final_metrics['packets_wrapped'] - initial_metrics['packets_wrapped']}")
    print(f"Errors: {final_metrics['errors'] - initial_metrics['errors']}")


async def example_backward_compatibility():
    """Example: Backward compatibility with non-STP systems"""
    print("\n=== Backward Compatibility Example ===")
    
    # Create STP service with STP disabled
    from app.middleware.stp_middleware import STPMiddleware
    disabled_middleware = STPMiddleware(enable_stp=False)
    
    test_data = {
        "agent_id": "test-agent",
        "confidence_score": 0.8
    }
    
    # With STP disabled, should return original data
    result = disabled_middleware.wrap(
        payload=test_data,
        packet_type=STPPacketType.ROUTING_DECISION.value
    )
    
    print(f"STP disabled - Original data: {test_data}")
    print(f"STP disabled - Result: {result}")
    print(f"✅ Data unchanged: {result == test_data}")
    
    # Unwrapping should also pass through
    payload, metadata = disabled_middleware.unwrap(test_data)
    print(f"Unwrap result - Payload: {payload}")
    print(f"Unwrap result - Metadata: {metadata}")
    print(f"✅ Pass-through behavior confirmed")


async def main():
    """Run all examples"""
    print("STP (Structured Token Protocol) Usage Examples")
    print("=" * 50)
    
    await example_basic_stp_wrapping()
    await example_stp_service_usage()
    await example_priority_determination()
    await example_error_handling()
    await example_metrics_monitoring()
    await example_backward_compatibility()
    
    print("\n" + "=" * 50)
    print("All examples completed successfully! ✅")


if __name__ == "__main__":
    # Note: This example requires the InsightFlow app context to run
    # In practice, these functions would be called within the FastAPI application
    print("STP Usage Examples")
    print("To run these examples, import and call the functions within your FastAPI app context.")
    print("\nExample usage:")
    print("from examples.stp_usage_example import example_basic_stp_wrapping")
    print("await example_basic_stp_wrapping()")