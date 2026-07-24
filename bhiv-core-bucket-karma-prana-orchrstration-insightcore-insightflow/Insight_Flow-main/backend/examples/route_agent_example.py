"""
Example: /route-agent Endpoint Usage

Demonstrates how to use the enhanced /route-agent endpoint with weighted scoring
for both v1 and v2 request formats.
"""

import asyncio
import httpx
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


async def demo_route_agent_endpoint():
    """Demonstrate route-agent endpoint usage"""
    
    print("=== /route-agent Endpoint Demo ===\n")
    
    async with httpx.AsyncClient() as client:
        
        # 1. Basic v1 format request
        print("1. Basic v1 Format Request:")
        
        v1_request = {
            "agent_type": "nlp",
            "confidence_threshold": 0.5,
            "context": {
                "priority": "high",
                "domain": "customer_service"
            },
            "request_id": "demo-v1-001"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/routing/route-agent",
                json=v1_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: Selected agent {data['agent_id']}")
                print(f"   📊 Confidence: {data['confidence_score']:.3f}")
                print(f"   🔍 Reasoning: {data['routing_reasoning']}")
                
                # Show score breakdown
                breakdown = data['score_breakdown']
                print(f"   📈 Score Breakdown:")
                print(f"     - Rule-based: {breakdown['rule_based_score']:.2f} × {breakdown['rule_weight']:.1f}")
                print(f"     - Feedback: {breakdown['feedback_based_score']:.2f} × {breakdown['feedback_weight']:.1f}")
                print(f"     - Availability: {breakdown['availability_score']:.2f} × {breakdown['availability_weight']:.1f}")
                
                # Show alternatives
                if data['alternative_agents']:
                    print(f"   🔄 Alternatives:")
                    for alt in data['alternative_agents']:
                        print(f"     - {alt['agent_id']}: {alt['confidence_score']:.3f}")
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        print()
        
        # 2. v2 format request
        print("2. v2 Format Request:")
        
        v2_request = {
            "task_type": "nlp",  # v2 uses task_type
            "confidence_threshold": 0.7,
            "context": {
                "priority": "medium",
                "user_type": "premium"
            },
            "correlation_id": "demo-v2-002"  # v2 uses correlation_id
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/routing/route-agent",
                json=v2_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: Selected agent {data['agent_id']}")
                print(f"   📊 Confidence: {data['confidence_score']:.3f}")
                print(f"   🕒 Timestamp: {data['timestamp']}")
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        print()
        
        # 3. High confidence threshold test
        print("3. High Confidence Threshold Test:")
        
        high_threshold_request = {
            "agent_type": "nlp",
            "confidence_threshold": 0.95,  # Very high threshold
            "context": {},
            "request_id": "demo-high-threshold"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/routing/route-agent",
                json=high_threshold_request
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: Found high-confidence agent {data['agent_id']}")
                print(f"   📊 Confidence: {data['confidence_score']:.3f}")
            elif response.status_code == 503:
                print(f"   ⚠️  Expected: No agent meets high confidence threshold")
                print(f"   📄 Response: {response.json()['detail']}")
            else:
                print(f"   ❌ Unexpected error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        print()
        
        # 4. Invalid agent type test
        print("4. Invalid Agent Type Test:")
        
        invalid_request = {
            "agent_type": "nonexistent_type",
            "confidence_threshold": 0.5,
            "request_id": "demo-invalid"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/routing/route-agent",
                json=invalid_request
            )
            
            if response.status_code == 404:
                print(f"   ✅ Expected: No agents available for invalid type")
                print(f"   📄 Response: {response.json()['detail']}")
            else:
                print(f"   ❌ Unexpected response: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        print()
        
        # 5. Missing agent type test
        print("5. Missing Agent Type Test:")
        
        missing_type_request = {
            "confidence_threshold": 0.5,
            "context": {},
            "request_id": "demo-missing-type"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/routing/route-agent",
                json=missing_type_request
            )
            
            if response.status_code == 400:
                print(f"   ✅ Expected: Missing agent_type error")
                print(f"   📄 Response: {response.json()['detail']}")
            else:
                print(f"   ❌ Unexpected response: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    print("\n=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("✅ Weighted scoring with rule-based, feedback, and availability scores")
    print("✅ Support for both v1 and v2 request formats")
    print("✅ Confidence threshold filtering")
    print("✅ Alternative agent suggestions")
    print("✅ Detailed score breakdown and reasoning")
    print("✅ Proper error handling for edge cases")


def demo_request_formats():
    """Show example request and response formats"""
    
    print("\n=== Request/Response Format Examples ===\n")
    
    print("v1 Request Format:")
    v1_example = {
        "agent_type": "nlp",
        "confidence_threshold": 0.75,
        "context": {
            "priority": "high",
            "domain": "customer_service",
            "user_id": "user123"
        },
        "request_id": "req-001"
    }
    print(json.dumps(v1_example, indent=2))
    
    print("\nv2 Request Format:")
    v2_example = {
        "task_type": "nlp",
        "confidence_threshold": 0.75,
        "context": {
            "priority": "high",
            "domain": "customer_service",
            "user_profile": {"tier": "premium"}
        },
        "correlation_id": "corr-001"
    }
    print(json.dumps(v2_example, indent=2))
    
    print("\nResponse Format:")
    response_example = {
        "agent_id": "nlp-001",
        "confidence_score": 0.87,
        "score_breakdown": {
            "rule_based_score": 0.80,
            "feedback_based_score": 0.90,
            "availability_score": 0.85,
            "rule_weight": 0.4,
            "feedback_weight": 0.4,
            "availability_weight": 0.2
        },
        "alternative_agents": [
            {"agent_id": "nlp-002", "confidence_score": 0.82},
            {"agent_id": "nlp-003", "confidence_score": 0.78}
        ],
        "routing_reasoning": "Selected nlp-001 based on weighted scoring: rule=0.80, feedback=0.90, availability=0.85",
        "request_id": "req-001",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    print(json.dumps(response_example, indent=2))


if __name__ == "__main__":
    demo_request_formats()
    print("\n" + "="*50)
    asyncio.run(demo_route_agent_endpoint())