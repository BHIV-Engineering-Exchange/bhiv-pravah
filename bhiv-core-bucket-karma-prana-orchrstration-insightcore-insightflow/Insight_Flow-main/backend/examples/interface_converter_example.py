"""
Interface Converter Usage Examples

This file demonstrates how to use the Interface Converter for format conversion
between InsightFlow and Core API formats.
"""

import json
from app.adapters.interface_converter import InterfaceConverter


def example_insightflow_to_core():
    """Example: Convert InsightFlow request to Core format"""
    print("=== Example: InsightFlow to Core Conversion ===")
    
    # Sample InsightFlow request
    insight_request = {
        "agent_type": "nlp",
        "context": {
            "text": "Analyze sentiment of this message",
            "language": "en"
        },
        "confidence_threshold": 0.8,
        "request_id": "req_12345"
    }
    
    print("InsightFlow Request:")
    print(json.dumps(insight_request, indent=2))
    
    # Convert to Core format
    core_request = InterfaceConverter.insight_flow_to_core(insight_request)
    
    print("\nCore Request:")
    print(json.dumps(core_request, indent=2))
    
    return core_request


def example_core_to_insightflow():
    """Example: Convert Core response to InsightFlow format"""
    print("\n=== Example: Core to InsightFlow Conversion ===")
    
    # Sample Core response
    core_response = {
        "selected_agent_id": "nlp_agent_001",
        "agent_category": "nlp",
        "confidence_level": 0.92,
        "correlation_id": "req_12345",
        "score_breakdown": {
            "routing_confidence": 0.92,
            "agent_performance": 0.88
        },
        "timestamp": "2025-01-15T10:30:00Z"
    }
    
    print("Core Response:")
    print(json.dumps(core_response, indent=2))
    
    # Convert to InsightFlow format
    insight_response = InterfaceConverter.core_to_insight_flow(core_response)
    
    print("\nInsightFlow Response:")
    print(json.dumps(insight_response, indent=2))
    
    return insight_response


def example_bidirectional_conversion():
    """Example: Bidirectional conversion"""
    print("\n=== Example: Bidirectional Conversion ===")
    
    # Start with InsightFlow format
    original_data = {
        "agent_type": "tts",
        "confidence_threshold": 0.75,
        "request_id": "req_67890"
    }
    
    print("Original InsightFlow Data:")
    print(json.dumps(original_data, indent=2))
    
    # Convert to Core format
    core_data = InterfaceConverter.bidirectional_convert(original_data, "insightflow")
    
    print("\nConverted to Core Format:")
    print(json.dumps(core_data, indent=2))


def example_validation():
    """Example: Format validation"""
    print("\n=== Example: Format Validation ===")
    
    # Valid InsightFlow request
    valid_insight = {"agent_type": "computer_vision"}
    try:
        InterfaceConverter.validate_field_mapping(valid_insight, "insightflow")
        print("[OK] Valid InsightFlow request")
    except ValueError as e:
        print(f"[ERROR] Invalid InsightFlow request: {e}")
    
    # Invalid InsightFlow request
    invalid_insight = {"wrong_field": "value"}
    try:
        InterfaceConverter.validate_field_mapping(invalid_insight, "insightflow")
        print("[OK] Valid InsightFlow request")
    except ValueError as e:
        print(f"[ERROR] Invalid InsightFlow request: {e}")
    
    # Valid Core response
    valid_core = {
        "selected_agent_id": "agent_001",
        "agent_category": "nlp",
        "confidence_level": 0.8
    }
    try:
        InterfaceConverter.validate_field_mapping(valid_core, "core")
        print("[OK] Valid Core response")
    except ValueError as e:
        print(f"[ERROR] Invalid Core response: {e}")


def main():
    """Run all examples"""
    print("Interface Converter Usage Examples")
    print("=" * 50)
    
    # Format conversions
    example_insightflow_to_core()
    example_core_to_insightflow()
    example_bidirectional_conversion()
    
    # Validation
    example_validation()
    
    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    main()