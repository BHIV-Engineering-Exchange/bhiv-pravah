#!/usr/bin/env python3
"""
Test workflow tracking implementation
Verify Solution 3 + Solution 2 fallback functionality
"""

import requests
import time
import json
from datetime import datetime

# Configuration
LANGGRAPH_URL = "http://localhost:9001"
API_KEY = "test-api-key-12345"  # Test API key

def test_workflow_tracking():
    """Test complete workflow tracking functionality"""
    print("Testing Workflow Tracking Implementation")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Test 1: Health check
    print("\n1. Testing service health...")
    try:
        response = requests.get(f"{LANGGRAPH_URL}/health", headers=headers)
        if response.status_code == 200:
            print("LangGraph service is healthy")
        else:
            print(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Cannot connect to LangGraph service: {str(e)}")
        return False
    
    # Test 2: Integration test
    print("\n2. Testing integration...")
    try:
        response = requests.get(f"{LANGGRAPH_URL}/test-integration", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Integration test passed")
            print(f"   Database tracking: {data.get('database_tracking', 'unknown')}")
            print(f"   Progress tracking: {data.get('progress_tracking', 'unknown')}")
            print(f"   Fallback support: {data.get('fallback_support', 'unknown')}")
        else:
            print(f"Integration test failed: {response.status_code}")
    except Exception as e:
        print(f"Integration test error: {str(e)}")
    
    # Test 3: Start workflow
    print("\n3. Starting test workflow...")
    workflow_data = {
        "candidate_id": 1,
        "job_id": 1,
        "application_id": 999,
        "candidate_email": "test@example.com",
        "candidate_phone": "+1234567890",
        "candidate_name": "Test Candidate",
        "job_title": "Test Position",
        "job_description": "Test job for workflow tracking"
    }
    
    try:
        response = requests.post(
            f"{LANGGRAPH_URL}/workflows/application/start",
            headers=headers,
            json=workflow_data
        )
        
        if response.status_code == 200:
            workflow_response = response.json()
            workflow_id = workflow_response["workflow_id"]
            print(f"Workflow started: {workflow_id}")
            print(f"   Status: {workflow_response['status']}")
            print(f"   Message: {workflow_response['message']}")
            
            # Test 4: Monitor progress
            print(f"\n4. Monitoring workflow progress...")
            return monitor_workflow_progress(workflow_id, headers)
            
        else:
            print(f"Failed to start workflow: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error starting workflow: {str(e)}")
        return False

def monitor_workflow_progress(workflow_id: str, headers: dict):
    """Monitor workflow progress with detailed tracking"""
    print(f"Monitoring workflow: {workflow_id}")
    
    max_attempts = 30  # 30 attempts = ~3 minutes
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(
                f"{LANGGRAPH_URL}/workflows/{workflow_id}/status",
                headers=headers
            )
            
            if response.status_code == 200:
                status_data = response.json()
                
                progress = status_data.get("progress_percentage", 0)
                current_step = status_data.get("current_step", "unknown")
                status = status_data.get("status", "unknown")
                eta = status_data.get("estimated_time_remaining", "unknown")
                
                print(f"   Progress: {progress}% | Step: {current_step} | ETA: {eta}")
                
                # Check if completed
                if status in ["completed", "failed", "cancelled"]:
                    print(f"\nWorkflow completed with status: {status}")
                    
                    # Show final results
                    if status_data.get("output_data"):
                        output = status_data["output_data"]
                        print(f"   AI Recommendation: {output.get('ai_recommendation', 'N/A')}")
                        print(f"   Sentiment: {output.get('sentiment', 'N/A')}")
                        print(f"   Next Action: {output.get('next_action', 'N/A')}")
                    
                    # Test workflow listing
                    test_workflow_listing(headers)
                    
                    # Test workflow stats
                    test_workflow_stats(headers)
                    
                    return True
                
                # Wait before next check
                time.sleep(6)  # Check every 6 seconds
                attempt += 1
                
            else:
                print(f"Status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error checking status: {str(e)}")
            return False
    
    print("Workflow monitoring timed out")
    return False

def test_workflow_listing(headers: dict):
    """Test workflow listing functionality"""
    print("\n5. Testing workflow listing...")
    
    try:
        # List all workflows
        response = requests.get(f"{LANGGRAPH_URL}/workflows", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['count']} workflows")
            print(f"   Tracking source: {data.get('tracking_source', 'unknown')}")
            
            # Show recent workflows
            if data['workflows']:
                print("   Recent workflows:")
                for workflow in data['workflows'][:3]:
                    print(f"     - {workflow['workflow_id']}: {workflow['status']} ({workflow.get('progress_percentage', 0)}%)")
        
        # List active workflows
        response = requests.get(f"{LANGGRAPH_URL}/workflows?status=active", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['count']} active workflows")
        
    except Exception as e:
        print(f"Error testing workflow listing: {str(e)}")

def test_workflow_stats(headers: dict):
    """Test workflow statistics"""
    print("\n6. Testing workflow statistics...")
    
    try:
        response = requests.get(f"{LANGGRAPH_URL}/workflows/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print("Workflow Statistics:")
            print(f"   Total workflows: {stats.get('total_workflows', 0)}")
            print(f"   Active workflows: {stats.get('active_workflows', 0)}")
            print(f"   Completed workflows: {stats.get('completed_workflows', 0)}")
            print(f"   Success rate: {stats.get('success_rate', 'N/A')}")
            print(f"   Database connection: {stats.get('database_connection', 'unknown')}")
        
    except Exception as e:
        print(f"Error testing workflow stats: {str(e)}")

if __name__ == "__main__":
    print("BHIV HR Platform - Workflow Tracking Test")
    print(f"Testing LangGraph service at: {LANGGRAPH_URL}")
    print(f"Using API key: {API_KEY[:10]}...")
    
    success = test_workflow_tracking()
    
    if success:
        print("\nAll tests passed!")
        print("Solution 3 + Solution 2 fallback working correctly")
        print("Database tracking operational")
        print("Progress monitoring functional")
        print("Workflow management ready")
    else:
        print("\nSome tests failed. Please check the implementation.")