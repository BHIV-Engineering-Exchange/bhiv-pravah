# examples/admin_api_usage.py
"""
Example usage of Admin API endpoints.

Demonstrates how to query routing logs, get statistics, and manage system health.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta


class AdminAPIClient:
    """Client for InsightFlow Admin API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", token: str = None):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}" if token else None
        }
    
    async def get_routing_logs(
        self,
        agent_id: str = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 100
    ):
        """Get routing decision logs"""
        params = {"limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/admin/routing-logs",
                headers=self.headers,
                params=params
            ) as response:
                return await response.json()
    
    async def get_routing_statistics(self, agent_id: str = None):
        """Get routing statistics"""
        params = {}
        if agent_id:
            params["agent_id"] = agent_id
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/admin/routing-statistics",
                headers=self.headers,
                params=params
            ) as response:
                return await response.json()
    
    async def cleanup_logs(self):
        """Clean up old logs"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/admin/cleanup-logs",
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def get_system_health(self):
        """Get system health status"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/admin/system-health",
                headers=self.headers
            ) as response:
                return await response.json()


async def main():
    """Example usage of admin API endpoints"""
    
    # Initialize client (replace with actual token)
    client = AdminAPIClient(token="your-jwt-token-here")
    
    print("=== InsightFlow Admin API Examples ===\n")
    
    try:
        # 1. Get recent routing logs
        print("1. Getting recent routing logs...")
        logs = await client.get_routing_logs(limit=10)
        print(f"Found {logs.get('count', 0)} recent decisions")
        
        if logs.get('decisions'):
            latest = logs['decisions'][0]
            print(f"Latest decision: {latest['agent_selected']} "
                  f"(confidence: {latest['confidence_score']:.2f})")
        print()
        
        # 2. Get logs for specific agent
        print("2. Getting logs for specific agent...")
        agent_logs = await client.get_routing_logs(
            agent_id="nlp-001",
            limit=5
        )
        print(f"Found {agent_logs.get('count', 0)} decisions for nlp-001")
        print()
        
        # 3. Get logs for date range
        print("3. Getting logs for last 24 hours...")
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
        today = datetime.utcnow().isoformat() + "Z"
        
        date_logs = await client.get_routing_logs(
            date_from=yesterday,
            date_to=today,
            limit=20
        )
        print(f"Found {date_logs.get('count', 0)} decisions in last 24h")
        print()
        
        # 4. Get overall statistics
        print("4. Getting routing statistics...")
        stats = await client.get_routing_statistics()
        if stats.get('statistics'):
            s = stats['statistics']
            print(f"Total decisions: {s.get('total_decisions', 0)}")
            print(f"Average confidence: {s.get('avg_confidence', 0):.2f}")
            print(f"Unique agents: {s.get('unique_agents', 0)}")
            if 'avg_response_time_ms' in s:
                print(f"Average response time: {s['avg_response_time_ms']:.1f}ms")
        print()
        
        # 5. Get statistics for specific agent
        print("5. Getting statistics for specific agent...")
        agent_stats = await client.get_routing_statistics(agent_id="nlp-001")
        if agent_stats.get('statistics'):
            s = agent_stats['statistics']
            print(f"NLP-001 decisions: {s.get('total_decisions', 0)}")
            print(f"NLP-001 avg confidence: {s.get('avg_confidence', 0):.2f}")
        print()
        
        # 6. Get system health
        print("6. Checking system health...")
        health = await client.get_system_health()
        if health.get('success'):
            print(f"System status: {health.get('system_status', 'unknown')}")
            services = health.get('services', {})
            for service, info in services.items():
                print(f"  {service}: {info.get('status', 'unknown')}")
        print()
        
        # 7. Cleanup old logs (uncomment to run)
        # print("7. Cleaning up old logs...")
        # cleanup = await client.cleanup_logs()
        # if cleanup.get('success'):
        #     print(f"Deleted {cleanup.get('deleted_entries', 0)} old entries")
        # print()
        
        print("=== Examples completed successfully ===")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure the server is running and you have a valid token")


def analyze_routing_patterns(logs_data):
    """Analyze routing patterns from logs"""
    if not logs_data.get('decisions'):
        print("No decisions to analyze")
        return
    
    decisions = logs_data['decisions']
    
    # Agent usage frequency
    agent_counts = {}
    confidence_scores = []
    response_times = []
    
    for decision in decisions:
        agent = decision.get('agent_selected', 'unknown')
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        if 'confidence_score' in decision:
            confidence_scores.append(decision['confidence_score'])
        
        if 'response_time_ms' in decision:
            response_times.append(decision['response_time_ms'])
    
    print("=== Routing Pattern Analysis ===")
    print(f"Total decisions analyzed: {len(decisions)}")
    print()
    
    print("Agent usage:")
    for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(decisions)) * 100
        print(f"  {agent}: {count} ({percentage:.1f}%)")
    print()
    
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        min_confidence = min(confidence_scores)
        max_confidence = max(confidence_scores)
        print(f"Confidence scores:")
        print(f"  Average: {avg_confidence:.2f}")
        print(f"  Range: {min_confidence:.2f} - {max_confidence:.2f}")
        print()
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        print(f"Response times:")
        print(f"  Average: {avg_time:.1f}ms")
        print(f"  Range: {min_time:.1f}ms - {max_time:.1f}ms")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
    
    # Example of pattern analysis (uncomment to use with real data)
    # sample_logs = {
    #     "decisions": [
    #         {"agent_selected": "nlp-001", "confidence_score": 0.85, "response_time_ms": 45.2},
    #         {"agent_selected": "nlp-002", "confidence_score": 0.78, "response_time_ms": 52.1},
    #         {"agent_selected": "nlp-001", "confidence_score": 0.92, "response_time_ms": 38.7}
    #     ]
    # }
    # analyze_routing_patterns(sample_logs)