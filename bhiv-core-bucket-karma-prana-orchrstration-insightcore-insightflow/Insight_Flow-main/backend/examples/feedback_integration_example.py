"""
Example: Feedback Score Service Integration

Demonstrates how the feedback score service integrates with the routing system
to provide real-time agent performance scores from Core.
"""

import asyncio
import logging
from app.core.dependencies import get_feedback_service
from app.services.decision_engine import decision_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_feedback_integration():
    """Demonstrate feedback service integration"""
    
    print("=== Feedback Score Service Integration Demo ===\n")
    
    # Get feedback service via dependency injection
    feedback_service = get_feedback_service()
    print(f"Using feedback service URL: {feedback_service.core_feedback_url}")
    
    # 1. Health Check
    print("1. Checking Core feedback service health...")
    is_healthy = await feedback_service.health_check()
    print(f"   Core service status: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}\n")
    
    # 2. Get agent scores
    print("2. Retrieving agent performance scores...")
    agent_ids = ["agent-nlp-1", "agent-tts-1", "agent-cv-1"]
    
    try:
        scores = await feedback_service.get_agent_scores(agent_ids)
        print("   Agent Scores:")
        for agent_id, score in scores.items():
            print(f"   - {agent_id}: {score:.3f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # 3. Demonstrate routing with feedback scores
    print("3. Routing request with feedback score integration...")
    
    try:
        routing_result = await decision_engine.route_request(
            input_data={"text": "What is the weather today?"},
            input_type="text",
            context={"user_id": "demo_user"},
            strategy="rule_based"  # Uses feedback scores
        )
        
        print("   Routing Result:")
        print(f"   - Selected Agent: {routing_result['agent_name']}")
        print(f"   - Confidence: {routing_result['confidence_score']:.3f}")
        print(f"   - Reason: {routing_result['routing_reason']}")
        
    except Exception as e:
        print(f"   Routing Error: {e}")
    
    print()
    
    # 4. Show service metrics
    print("4. Feedback service metrics:")
    metrics = feedback_service.get_metrics()
    for key, value in metrics.items():
        print(f"   - {key}: {value}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(demo_feedback_integration())