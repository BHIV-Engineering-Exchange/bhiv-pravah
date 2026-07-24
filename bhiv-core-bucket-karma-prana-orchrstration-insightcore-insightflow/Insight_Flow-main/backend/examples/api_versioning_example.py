"""
API Versioning Usage Examples

This file demonstrates how to use the API versioning and backward compatibility
features in InsightFlow.
"""

import json
from app.services.compatibility_service import CompatibilityService


def example_version_detection():
    """Example: Detect API version from request data"""
    print("=== Example: API Version Detection ===")
    
    service = CompatibilityService()
    
    # Legacy v1 format
    v1_request = {
        "input_data": {"text": "Analyze this text"},
        "input_type": "text",
        "strategy": "q_learning"
    }
    
    print("Legacy v1 Request:")
    print(json.dumps(v1_request, indent=2))
    version = service.detect_api_version(v1_request)
    print(f"Detected Version: {version}")
    
    # Core v2 format
    v2_request = {
        "task_type": "nlp",
        "min_confidence": 0.8,
        "task_context": {"text": "Analyze this text"},
        "correlation_id": "req-123"
    }
    
    print("\nCore v2 Request:")
    print(json.dumps(v2_request, indent=2))
    version = service.detect_api_version(v2_request)
    print(f"Detected Version: {version}")
    
    # KSML format
    ksml_request = {
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
    
    print("\nKSML Request:")
    print(json.dumps(ksml_request, indent=2))
    version = service.detect_api_version(ksml_request)
    print(f"Detected Version: {version}")


def example_format_conversion():
    """Example: Convert between API formats"""
    print("\n=== Example: Format Conversion ===")
    
    service = CompatibilityService()
    
    # Convert v2 to v1
    v2_data = {
        "task_type": "nlp",
        "min_confidence": 0.8,
        "task_context": {"text": "Hello world"},
        "correlation_id": "req-456"
    }
    
    print("Original v2 Data:")
    print(json.dumps(v2_data, indent=2))
    
    try:
        v1_data = service.convert_to_legacy_format(v2_data, "v2")
        print("\nConverted to v1 Format:")
        print(json.dumps(v1_data, indent=2))
        
        # Convert back to v2
        v2_converted = service.convert_from_legacy_format(v1_data, "v2")
        print("\nConverted back to v2 Format:")
        print(json.dumps(v2_converted, indent=2))
        
    except Exception as e:
        print(f"Conversion error: {e}")


def example_version_compatibility():
    """Example: Check version compatibility"""
    print("\n=== Example: Version Compatibility ===")
    
    service = CompatibilityService()
    
    # Test data
    test_cases = [
        {
            "data": {"input_data": {"text": "test"}, "input_type": "text"},
            "expected": "v1",
            "description": "v1 data with v1 expectation"
        },
        {
            "data": {"task_type": "nlp", "min_confidence": 0.8},
            "expected": "v1",
            "description": "v2 data with v1 expectation (convertible)"
        },
        {
            "data": {"input_data": {"text": "test"}, "input_type": "text"},
            "expected": "v2",
            "description": "v1 data with v2 expectation (convertible)"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {case['description']}")
        print(f"Data: {json.dumps(case['data'])}")
        
        is_compatible, message = service.validate_version_compatibility(
            case['data'], case['expected']
        )
        
        print(f"Compatible: {is_compatible}")
        if message:
            print(f"Message: {message}")


def example_version_info():
    """Example: Get API version information"""
    print("\n=== Example: Version Information ===")
    
    service = CompatibilityService()
    
    version_info = service.get_version_info()
    
    print("API Version Information:")
    print(json.dumps(version_info, indent=2))


def main():
    """Run all API versioning examples"""
    print("API Versioning Usage Examples")
    print("=" * 50)
    
    # Run all examples
    example_version_detection()
    example_format_conversion()
    example_version_compatibility()
    example_version_info()
    
    print("\n" + "=" * 50)
    print("All API versioning examples completed!")


if __name__ == "__main__":
    main()