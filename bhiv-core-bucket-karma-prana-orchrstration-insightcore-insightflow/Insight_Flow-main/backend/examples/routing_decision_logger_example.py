"""
Example: Routing Decision Logger Usage

Demonstrates how to use the routing decision logger for audit trails,
analytics, and debugging routing decisions.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from app.utils.routing_decision_logger import get_routing_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_routing_decision_logger():
    """Demonstrate routing decision logger functionality"""
    
    print("=== Routing Decision Logger Demo ===\n")
    
    # Get logger instance
    routing_logger = get_routing_logger()
    
    # 1. Log basic routing decisions
    print("1. Logging Basic Routing Decisions:")
    
    basic_decisions = [
        {
            "agent_selected": "nlp-001",
            "confidence_score": 0.87,
            "request_id": "req-001",
            "context": {"agent_type": "nlp", "priority": "high", "user_id": "user123"},
            "reasoning": "Best NLP agent for high priority task"
        },
        {
            "agent_selected": "tts-001", 
            "confidence_score": 0.92,
            "request_id": "req-002",
            "context": {"agent_type": "tts", "priority": "normal", "user_id": "user456"},
            "reasoning": "Excellent TTS performance"
        },
        {
            "agent_selected": "nlp-002",
            "confidence_score": 0.75,
            "request_id": "req-003", 
            "context": {"agent_type": "nlp", "priority": "low"},
            "reasoning": "Backup NLP agent selected"
        }
    ]
    
    for decision in basic_decisions:
        success = routing_logger.log_decision(**decision)
        print(f"   ✅ Logged: {decision['agent_selected']} (confidence: {decision['confidence_score']:.2f})")
    
    print()
    
    # 2. Log detailed decisions with score breakdown
    print("2. Logging Detailed Decisions with Score Breakdown:")
    
    detailed_decision = {
        "agent_selected": "nlp-003",
        "confidence_score": 0.89,
        "request_id": "req-004",
        "context": {
            "agent_type": "nlp",
            "priority": "high",
            "user_id": "premium_user789",
            "domain": "customer_service"
        },
        "score_breakdown": {
            "rule_based": {"score": 0.85, "weight": 0.4, "weighted_value": 0.34},
            "feedback_based": {"score": 0.95, "weight": 0.4, "weighted_value": 0.38},
            "availability": {"score": 0.90, "weight": 0.2, "weighted_value": 0.18}
        },
        "alternatives": [
            {"agent_id": "nlp-001", "confidence": 0.82},
            {"agent_id": "nlp-004", "confidence": 0.78}
        ],
        "response_time_ms": 42.5,
        "reasoning": "Premium user gets best available NLP agent with excellent feedback scores"
    }
    
    success = routing_logger.log_decision(**detailed_decision)
    print(f"   ✅ Logged detailed decision: {detailed_decision['agent_selected']}")
    print(f"   📊 Score breakdown: {len(detailed_decision['score_breakdown'])} components")
    print(f"   🔄 Alternatives: {len(detailed_decision['alternatives'])} agents")
    print(f"   ⏱️  Response time: {detailed_decision['response_time_ms']}ms")
    
    print()
    
    # 3. Query routing decisions
    print("3. Querying Routing Decisions:")
    
    # Query all decisions
    all_decisions = routing_logger.query_decisions(limit=10)
    print(f"   📋 Total decisions logged: {len(all_decisions)}")
    
    # Query decisions for specific agent
    nlp_decisions = routing_logger.query_decisions(agent_id="nlp-001", limit=5)
    print(f"   🎯 Decisions for nlp-001: {len(nlp_decisions)}")
    
    # Show recent decisions
    print(f"   📅 Recent decisions:")
    for decision in all_decisions[-3:]:
        print(f"     - {decision['timestamp']}: {decision['agent_selected']} "
              f"(confidence: {decision['confidence_score']:.2f})")
    
    print()
    
    # 4. Get statistics
    print("4. Routing Statistics:")
    
    # Overall statistics
    overall_stats = routing_logger.get_statistics()
    if "error" not in overall_stats:
        print(f"   📊 Overall Statistics:")
        print(f"     - Total decisions: {overall_stats['total_decisions']}")
        print(f"     - Average confidence: {overall_stats['avg_confidence']:.3f}")
        print(f"     - Confidence range: {overall_stats['min_confidence']:.2f} - {overall_stats['max_confidence']:.2f}")
        print(f"     - Unique agents: {overall_stats['unique_agents']}")
        
        if "avg_response_time_ms" in overall_stats:
            print(f"     - Average response time: {overall_stats['avg_response_time_ms']:.1f}ms")
            print(f"     - Max response time: {overall_stats['max_response_time_ms']:.1f}ms")
    
    # Agent-specific statistics
    nlp_stats = routing_logger.get_statistics(agent_id="nlp-001")
    if "error" not in nlp_stats and nlp_stats['total_decisions'] > 0:
        print(f"   🎯 NLP-001 Statistics:")
        print(f"     - Decisions: {nlp_stats['total_decisions']}")
        print(f"     - Average confidence: {nlp_stats['avg_confidence']:.3f}")
    
    print()
    
    # 5. Demonstrate log file format
    print("5. Log File Format (JSON Lines):")
    
    if routing_logger.log_file.exists():
        print(f"   📁 Log file: {routing_logger.log_file}")
        
        # Show last few lines
        with open(routing_logger.log_file, 'r') as f:
            lines = f.readlines()
            
        print(f"   📄 Sample log entries:")
        for i, line in enumerate(lines[-2:], 1):
            if line.strip():
                entry = json.loads(line)
                print(f"     Entry {i}:")
                print(f"       Timestamp: {entry['timestamp']}")
                print(f"       Agent: {entry['agent_selected']}")
                print(f"       Confidence: {entry['confidence_score']}")
                print(f"       Context: {entry['context_summary']}")
                print(f"       Reasoning: {entry['decision_reasoning']}")
                print()
    
    # 6. Cleanup demonstration
    print("6. Log Cleanup:")
    
    # Show current log count
    current_decisions = routing_logger.query_decisions(limit=1000)
    print(f"   📊 Current log entries: {len(current_decisions)}")
    
    # Demonstrate cleanup (won't delete anything since logs are recent)
    deleted_count = routing_logger.cleanup_old_logs()
    print(f"   🧹 Cleaned up {deleted_count} old entries")
    print(f"   ⚙️  Retention period: {routing_logger.retention_days} days")
    
    print("\n=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("✅ Basic decision logging with context")
    print("✅ Detailed logging with score breakdowns")
    print("✅ Querying decisions with filters")
    print("✅ Statistical analysis of routing patterns")
    print("✅ JSON Lines format for easy processing")
    print("✅ Automatic log cleanup and retention")


def demo_log_analysis():
    """Demonstrate log analysis capabilities"""
    
    print("\n=== Log Analysis Demo ===\n")
    
    routing_logger = get_routing_logger()
    
    # Analyze agent performance from logs
    print("1. Agent Performance Analysis:")
    
    decisions = routing_logger.query_decisions(limit=1000)
    if decisions:
        # Group by agent
        agent_performance = {}
        for decision in decisions:
            agent_id = decision["agent_selected"]
            confidence = decision["confidence_score"]
            
            if agent_id not in agent_performance:
                agent_performance[agent_id] = {
                    "count": 0,
                    "total_confidence": 0,
                    "confidences": []
                }
            
            agent_performance[agent_id]["count"] += 1
            agent_performance[agent_id]["total_confidence"] += confidence
            agent_performance[agent_id]["confidences"].append(confidence)
        
        # Calculate averages and show top performers
        for agent_id, perf in agent_performance.items():
            avg_confidence = perf["total_confidence"] / perf["count"]
            min_conf = min(perf["confidences"])
            max_conf = max(perf["confidences"])
            
            print(f"   🤖 {agent_id}:")
            print(f"     - Selections: {perf['count']}")
            print(f"     - Avg confidence: {avg_confidence:.3f}")
            print(f"     - Range: {min_conf:.2f} - {max_conf:.2f}")
    
    print()
    
    # Analyze routing patterns
    print("2. Routing Pattern Analysis:")
    
    if decisions:
        # Time-based analysis
        hourly_counts = {}
        for decision in decisions:
            timestamp = decision["timestamp"]
            hour = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        if hourly_counts:
            peak_hour = max(hourly_counts, key=hourly_counts.get)
            print(f"   📈 Peak routing hour: {peak_hour}:00 ({hourly_counts[peak_hour]} decisions)")
        
        # Context analysis
        context_patterns = {}
        for decision in decisions:
            context_summary = decision.get("context_summary", "unknown")
            context_patterns[context_summary] = context_patterns.get(context_summary, 0) + 1
        
        print(f"   🏷️  Common context patterns:")
        for pattern, count in sorted(context_patterns.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"     - {pattern}: {count} times")
    
    print("\n=== Analysis Complete ===")


if __name__ == "__main__":
    demo_routing_decision_logger()
    demo_log_analysis()