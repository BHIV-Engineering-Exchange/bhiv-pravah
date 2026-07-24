"""
KSML Adapter Usage Examples

This file demonstrates how to use the KSML adapter for external system integration.
"""

import asyncio
import json
from app.adapters.ksml_adapter import KSMLAdapter, KSMLPacketType
from app.services.ksml_service import ksml_service


def example_wrap_routing_request():
    """Example: Wrap a routing request in KSML format"""
    print("=== Example: Wrapping Routing Request ===")
    
    # Sample routing request data
    routing_data = {
        "input_data": {"text": "What is the weather today?"},
        "input_type": "text",
        "strategy": "q_learning",
        "context": {"user_preference": "detailed"}
    }
    
    # Wrap in KSML format
    ksml_packet = KSMLAdapter.wrap(routing_data, KSMLPacketType.ROUTING_REQUEST)
    
    print("Original data:")
    print(json.dumps(routing_data, indent=2))
    print("\nKSML packet:")
    print(json.dumps(ksml_packet, indent=2))
    
    return ksml_packet


def example_unwrap_ksml_packet(ksml_packet):
    """Example: Unwrap KSML packet back to original data"""
    print("\n=== Example: Unwrapping KSML Packet ===")
    
    # Unwrap KSML packet
    original_data = KSMLAdapter.unwrap(ksml_packet)
    
    print("Unwrapped data:")
    print(json.dumps(original_data, indent=2))
    
    return original_data


def example_validate_ksml_structure(ksml_packet):
    """Example: Validate KSML packet structure"""
    print("\n=== Example: Validating KSML Structure ===")
    
    is_valid = KSMLAdapter.validate_ksml_structure(ksml_packet)
    print(f"KSML packet is valid: {is_valid}")
    
    # Test with invalid packet
    invalid_packet = {"invalid": "structure"}
    is_invalid = KSMLAdapter.validate_ksml_structure(invalid_packet)
    print(f"Invalid packet is valid: {is_invalid}")


def example_bytes_conversion():
    """Example: Convert KSML to/from bytes for transmission"""
    print("\n=== Example: Bytes Conversion ===")
    
    # Sample feedback data
    feedback_data = {
        "routing_log_id": "log_123",
        "success": True,
        "latency_ms": 145.5,
        "accuracy_score": 0.88,
        "user_satisfaction": 4
    }
    
    # Convert to bytes
    ksml_bytes = KSMLAdapter.convert_to_ksml_bytes(
        feedback_data, 
        KSMLPacketType.FEEDBACK_LOG
    )
    
    print(f"KSML bytes length: {len(ksml_bytes)}")
    print(f"First 100 bytes: {ksml_bytes[:100]}...")
    
    # Convert back from bytes
    recovered_data = KSMLAdapter.convert_from_ksml_bytes(ksml_bytes)
    
    print("Recovered data:")
    print(json.dumps(recovered_data, indent=2))


def main():
    """Run all examples"""
    print("KSML Adapter Usage Examples")
    print("=" * 50)
    
    # Basic wrapping/unwrapping
    ksml_packet = example_wrap_routing_request()
    original_data = example_unwrap_ksml_packet(ksml_packet)
    
    # Validation
    example_validate_ksml_structure(ksml_packet)
    
    # Bytes conversion
    example_bytes_conversion()
    
    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    main()