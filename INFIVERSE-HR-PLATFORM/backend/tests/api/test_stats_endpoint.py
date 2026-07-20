#!/usr/bin/env python3
"""
Quick test for the updated /v1/candidates/stats endpoint
"""

import asyncio
import httpx
import os

async def test_stats_endpoint():
    """Test the dynamic /v1/candidates/stats endpoint"""
    
    # Use local gateway URL
    gateway_service_url = "http://localhost:8000"
    api_key = os.getenv("API_KEY_SECRET", "<YOUR_API_KEY>")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("Testing /v1/candidates/stats endpoint...")
    print(f"Gateway URL: {gateway_service_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{gateway_service_url}/v1/candidates/stats",
                headers=headers
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("SUCCESS - Dynamic stats retrieved:")
                print(f"  Total Candidates: {data.get('total_candidates', 'N/A')}")
                print(f"  Active Jobs: {data.get('active_jobs', 'N/A')}")
                print(f"  Recent Matches: {data.get('recent_matches', 'N/A')}")
                print(f"  Pending Interviews: {data.get('pending_interviews', 'N/A')}")
                print(f"  New This Week: {data.get('new_candidates_this_week', 'N/A')}")
                print(f"  Total Feedback: {data.get('total_feedback_submissions', 'N/A')}")
                print(f"  Data Source: {data.get('data_source', 'N/A')}")
                print(f"  Dashboard Ready: {data.get('dashboard_ready', 'N/A')}")
            else:
                print(f"FAILED - Status: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_stats_endpoint())