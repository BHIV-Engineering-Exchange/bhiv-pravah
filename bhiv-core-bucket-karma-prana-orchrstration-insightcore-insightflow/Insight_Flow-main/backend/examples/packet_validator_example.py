"""
Packet Validator Usage Examples

This file demonstrates how to use the Packet Validator for validating
KSML and Core format packets in InsightFlow.
"""

import json
from app.validators.packet_validator import PacketValidator, ValidationResult


def example_ksml_packet_validation():
    """Example: Validate KSML packets"""
    print("=== Example: KSML Packet Validation ===")
    
    # Valid KSML packet
    valid_ksml = {
        "meta": {
            "version": "1.0",
            "packet_type": "routing_request",
            "timestamp": "2025-01-15T10:30:00Z",
            "source": "insightflow",
            "destination": "core",
            "message_id": "msg-abc123",
            "checksum": "hash456"
        },
        "payload": {
            "data": {
                "task_type": "nlp",
                "task_context": {"text": "Analyze this text"}
            }
        }
    }
    
    print("Valid KSML Packet:")
    print(json.dumps(valid_ksml, indent=2))
    
    is_valid, errors = PacketValidator.validate_ksml_packet(valid_ksml)
    print(f"\nValidation Result: {'VALID' if is_valid else 'INVALID'}")
    if errors:
        print(f"Errors: {errors}")
    
    # Invalid KSML packet
    invalid_ksml = {
        "meta": {
            "version": "1.0",
            "packet_type": "routing_request"
            # Missing required fields
        },
        "payload": {
            "data": {"test": "data"}
        }
    }
    
    print("\n" + "-" * 40)
    print("Invalid KSML Packet:")
    print(json.dumps(invalid_ksml, indent=2))
    
    is_valid, errors = PacketValidator.validate_ksml_packet(invalid_ksml)
    print(f"\nValidation Result: {'VALID' if is_valid else 'INVALID'}")
    if errors:
        print(f"Errors: {errors}")


def example_core_request_validation():
    """Example: Validate Core routing requests"""
    print("\n=== Example: Core Request Validation ===")
    
    # Valid Core request
    valid_request = {
        "task_type": "nlp",
        "min_confidence": 0.8,
        "task_context": {"text": "Process this text"},
        "correlation_id": "req-789"
    }
    
    print("Valid Core Request:")
    print(json.dumps(valid_request, indent=2))
    
    is_valid, errors = PacketValidator.validate_core_routing_request(valid_request)
    print(f"\nValidation Result: {'VALID' if is_valid else 'INVALID'}")
    if errors:
        print(f"Errors: {errors}")
    
    # Invalid Core request
    invalid_request = {
        "task_type": "nlp",
        "min_confidence": 1.5  # Invalid range
    }
    
    print("\n" + "-" * 40)
    print("Invalid Core Request:")
    print(json.dumps(invalid_request, indent=2))
    
    is_valid, errors = PacketValidator.validate_core_routing_request(invalid_request)
    print(f"\nValidation Result: {'VALID' if is_valid else 'INVALID'}")
    if errors:
        print(f"Errors: {errors}")


def example_core_response_validation():
    """Example: Validate Core routing responses"""
    print("\n=== Example: Core Response Validation ===")
    
    # Valid Core response
    valid_response = {
        "selected_agent_id": "nlp-agent-001",
        "agent_category": "nlp",
        "confidence_level": 0.92,
        "timestamp": "2025-01-15T10:35:00Z",
        "correlation_id": "req-789"
    }
    
    print("Valid Core Response:")
    print(json.dumps(valid_response, indent=2))
    
    is_valid, errors = PacketValidator.validate_core_routing_response(valid_response)
    print(f"\nValidation Result: {'VALID' if is_valid else 'INVALID'}")
    if errors:
        print(f"Errors: {errors}")
    
    # Invalid Core response
    invalid_response = {
        "selected_agent_id": "nlp-agent-001",
        "confidence_level": -0.1  # Invalid range, missing required fields
    }
    
    print("\n" + "-" * 40)
    print("Invalid Core Response:")
    print(json.dumps(invalid_response, indent=2))
    
    is_valid, errors = PacketValidator.validate_core_routing_response(invalid_response)
    print(f"\nValidation Result: {'VALID' if is_valid else 'INVALID'}")
    if errors:
        print(f"Errors: {errors}")


def example_routing_decision_validation():
    """Example: Validate routing decisions"""
    print("\n=== Example: Routing Decision Validation ===")
    
    # Valid routing decision
    valid_decision = {
        "agent_selected": "nlp-agent-001",
        "confidence_score": 0.88,
        "routing_reason": "Best performance match",
        "execution_time_ms": 125.5
    }
    
    print("Valid Routing Decision:")
    print(json.dumps(valid_decision, indent=2))
    
    is_valid, errors = PacketValidator.validate_routing_decision(valid_decision)
    print(f"\nValidation Result: {'VALID' if is_valid else 'INVALID'}")
    if errors:
        print(f"Errors: {errors}")
    
    # Invalid routing decision
    invalid_decision = {
        "routing_reason": "Best match",
        "confidence_score": 2.0  # Invalid range, missing agent_selected
    }
    
    print("\n" + "-" * 40)
    print("Invalid Routing Decision:")
    print(json.dumps(invalid_decision, indent=2))
    
    is_valid, errors = PacketValidator.validate_routing_decision(invalid_decision)
    print(f"\nValidation Result: {'VALID' if is_valid else 'INVALID'}")
    if errors:
        print(f"Errors: {errors}")


def main():
    """Run all validation examples"""
    print("Packet Validator Usage Examples")
    print("=" * 50)
    
    # Run all examples
    example_ksml_packet_validation()
    example_core_request_validation()
    example_core_response_validation()
    example_routing_decision_validation()
    
    print("\n" + "=" * 50)
    print("All validation examples completed!")


if __name__ == "__main__":
    main()