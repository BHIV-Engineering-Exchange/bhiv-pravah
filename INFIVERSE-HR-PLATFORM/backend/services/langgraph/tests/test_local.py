#!/usr/bin/env python3
"""
Local testing script for BHIV LangGraph Service
"""
import asyncio
import httpx
import json
from datetime import datetime

LANGGRAPH_URL = "http://localhost:9001"

async def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LANGGRAPH_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS: Health check passed: {data['status']}")
                return True
            else:
                print(f"ERROR: Health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"ERROR: Health check error: {e}")
        return False

async def test_workflow():
    """Test workflow endpoint"""
    print("Testing workflow endpoint...")
    
    payload = {
        "candidate_id": 1,
        "job_id": 1,
        "application_id": 1,
        "candidate_email": "test@example.com",
        "candidate_phone": "+1234567890",
        "candidate_name": "Test Candidate",
        "job_title": "Software Engineer",
        "job_description": "Develop backend APIs"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LANGGRAPH_URL}/workflows/application/start",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS: Workflow started: {data['workflow_id']}")
                return data['workflow_id']
            else:
                print(f"ERROR: Workflow failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
    except Exception as e:
        print(f"ERROR: Workflow error: {e}")
        return None

async def test_workflow_status(workflow_id: str):
    """Test workflow status endpoint"""
    print(f"Testing workflow status for {workflow_id}...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LANGGRAPH_URL}/workflows/{workflow_id}/status")
            
            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS: Workflow status: {data['current_stage']} - {data['application_status']}")
                return True
            else:
                print(f"ERROR: Status check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"ERROR: Status check error: {e}")
        return False

async def main():
    """Run all tests"""
    print("BHIV LangGraph Service - Local Testing")
    print("=" * 50)
    
    # Test 1: Health check
    health_ok = await test_health()
    if not health_ok:
        print("ERROR: Service not healthy. Make sure it's running on port 9001")
        return
    
    print()
    
    # Test 2: Start workflow
    workflow_id = await test_workflow()
    if not workflow_id:
        print("ERROR: Workflow test failed")
        return
    
    print()
    
    # Wait a bit for workflow to process
    print("Waiting 3 seconds for workflow to process...")
    await asyncio.sleep(3)
    
    # Test 3: Check workflow status
    await test_workflow_status(workflow_id)
    
    print()
    print("SUCCESS: All tests completed!")
    print(f"Service running at: {LANGGRAPH_URL}")
    print(f"API docs: {LANGGRAPH_URL}/docs")

if __name__ == "__main__":
    asyncio.run(main())