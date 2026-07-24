# examples/dashboard_api_usage.py
"""
Example usage of Dashboard API endpoints.

Demonstrates how to retrieve performance metrics, accuracy data, and agent statistics.
"""

import asyncio
import aiohttp
import json
from datetime import datetime


class DashboardAPIClient:
    """Client for InsightFlow Dashboard API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", token: str = None):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if token else None
        }
    
    async def get_performance_metrics(self, hours: int = 24):
        """Get performance metrics"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/dashboard/metrics/performance",
                params={"hours": hours}
            ) as response:
                return await response.json()
    
    async def get_routing_accuracy(self, hours: int = 24):
        """Get routing accuracy metrics"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/dashboard/metrics/accuracy",
                params={"hours": hours}
            ) as response:
                return await response.json()
    
    async def get_agent_performance(self, hours: int = 24):
        """Get agent performance metrics"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/dashboard/metrics/agents",
                params={"hours": hours}
            ) as response:
                return await response.json()
    



async def main():
    """Example usage of dashboard API endpoints"""
    
    # Initialize client (replace with actual token)
    client = DashboardAPIClient(token="your-jwt-token-here")
    
    print("=== InsightFlow Dashboard API Examples ===\n")
    
    try:
        # 1. Get performance metrics
        print("1. Getting performance metrics (last 24 hours)...")
        performance = await client.get_performance_metrics(hours=24)
        
        if performance.get('total_decisions') is not None:
            print(f"Total decisions: {performance.get('total_decisions', 0)}")
            print(f"Average confidence: {performance.get('average_confidence', 0):.2f}")
            print(f"Average response time: {performance.get('avg_response_time_ms', 0):.1f}ms")
            
            # Show confidence distribution
            dist = performance.get('confidence_distribution', {})
            print("Confidence distribution:")
            for range_key, count in dist.items():
                print(f"  {range_key}: {count} decisions")
            
            # Show top agents
            top_agents = performance.get('top_agents', [])
            print("Top agents:")
            for agent in top_agents[:3]:
                print(f"  {agent['agent_id']}: {agent['count']} decisions")
        print()
        
        # 2. Get routing accuracy
        print("2. Getting routing accuracy...")
        accuracy = await client.get_routing_accuracy(hours=24)
        
        if accuracy.get('total_decisions') is not None:
            print(f"Total decisions: {accuracy.get('total_decisions', 0)}")
            print(f"High confidence decisions: {accuracy.get('high_confidence_decisions', 0)}")
            print(f"Accuracy percentage: {accuracy.get('accuracy_percentage', 0):.1f}%")
        print()
        
        # 3. Get agent performance
        print("3. Getting agent performance...")
        agents = await client.get_agent_performance(hours=24)
        
        if isinstance(agents, list):
            print(f"Found {len(agents)} agents:")
            
            for agent in agents[:5]:  # Show top 5
                print(f"  {agent['agent_id']}:")
                print(f"    Decisions: {agent['total_decisions']}")
                print(f"    Avg confidence: {agent['avg_confidence']:.2f}")
                print(f"    Range: {agent['min_confidence']:.2f} - {agent['max_confidence']:.2f}")
        print()
        
        # 4. Compare different time windows
        print("4. Comparing different time windows...")
        
        time_windows = [1, 6, 24, 72]  # 1h, 6h, 24h, 72h
        
        for hours in time_windows:
            perf = await client.get_performance_metrics(hours=hours)
            if perf.get('total_decisions') is not None:
                print(f"  Last {hours}h: {perf.get('total_decisions', 0)} decisions, "
                      f"avg confidence: {perf.get('average_confidence', 0):.2f}")
        print()
        
        print("=== Dashboard examples completed successfully ===")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure the server is running and you have a valid token")


def analyze_performance_trends(performance_data):
    """Analyze performance trends from dashboard data"""
    if not performance_data.get('total_decisions'):
        print("No performance data to analyze")
        return
    
    metrics = performance_data
    
    print("=== Performance Analysis ===")
    print(f"Total decisions: {metrics.get('total_decisions', 0)}")
    print(f"Average confidence: {metrics.get('average_confidence', 0):.2f}")
    print(f"Confidence range: {metrics.get('min_confidence', 0):.2f} - {metrics.get('max_confidence', 0):.2f}")
    print(f"Average response time: {metrics.get('avg_response_time_ms', 0):.1f}ms")
    print()
    
    # Analyze confidence distribution
    dist = metrics.get('confidence_distribution', {})
    total = sum(dist.values())
    
    if total > 0:
        print("Confidence Distribution Analysis:")
        high_confidence = dist.get('0.75-1.0', 0)
        medium_confidence = dist.get('0.5-0.75', 0)
        low_confidence = dist.get('0-0.5', 0)
        
        print(f"  High confidence (0.75-1.0): {high_confidence} ({high_confidence/total*100:.1f}%)")
        print(f"  Medium confidence (0.5-0.75): {medium_confidence} ({medium_confidence/total*100:.1f}%)")
        print(f"  Low confidence (0-0.5): {low_confidence} ({low_confidence/total*100:.1f}%)")
        
        if high_confidence / total >= 0.7:
            print("  ✓ Good: High confidence rate >= 70%")
        elif high_confidence / total >= 0.5:
            print("  ⚠ Fair: High confidence rate 50-70%")
        else:
            print("  ✗ Poor: High confidence rate < 50%")
    print()
    
    # Analyze top agents
    top_agents = metrics.get('top_agents', [])
    if top_agents:
        print("Top Agent Analysis:")
        total_decisions = metrics.get('total_decisions', 0)
        
        for i, agent in enumerate(top_agents[:3], 1):
            percentage = (agent['count'] / total_decisions * 100) if total_decisions > 0 else 0
            print(f"  #{i} {agent['agent_id']}: {agent['count']} decisions ({percentage:.1f}%)")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
    
    # Example of performance analysis (uncomment to use with real data)
    # sample_performance = {
    #     "success": True,
    #     "metrics": {
    #         "total_decisions": 150,
    #         "average_confidence": 0.82,
    #         "min_confidence": 0.65,
    #         "max_confidence": 0.95,
    #         "confidence_distribution": {
    #             "0-0.25": 5,
    #             "0.25-0.5": 15,
    #             "0.5-0.75": 45,
    #             "0.75-1.0": 85
    #         },
    #         "avg_response_time_ms": 42.1,
    #         "top_agents": [
    #             {"agent_id": "nlp-001", "count": 65},
    #             {"agent_id": "nlp-002", "count": 45},
    #             {"agent_id": "cv-001", "count": 40}
    #         ]
    #     }
    # }
    # analyze_performance_trends(sample_performance)