#!/usr/bin/env python3
"""Test HR Portal with actual input/output operations"""

import asyncio
import httpx
import json

API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
BASE_URL = "http://localhost:8000"

async def test_job_creation():
    """Test creating a job and verify output"""
    job_data = {
        "title": "Test Software Engineer",
        "department": "Engineering", 
        "location": "Remote",
        "experience_level": "Mid",
        "requirements": "Python, FastAPI",
        "description": "Test job for HTTP client verification",
        "client_id": 1
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/v1/jobs", json=job_data, headers=HEADERS, timeout=10.0)
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get("job_id")
            print(f"PASS Job Creation: Created job ID {job_id}")
            return job_id
        else:
            print(f"FAIL Job Creation: {response.status_code} - {response.text}")
            return None

async def test_candidate_upload():
    """Test uploading candidates and verify output"""
    candidates_data = {
        "candidates": [
            {
                "name": "Test Candidate 1",
                "email": "test1@example.com",
                "cv_url": "https://example.com/cv1.pdf",
                "phone": "+1234567890",
                "experience_years": 3,
                "status": "applied",
                "job_id": 1,
                "location": "Mumbai",
                "technical_skills": "Python, JavaScript",
                "designation": "Software Developer",
                "education_level": "Masters"
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/v1/candidates/bulk", json=candidates_data, headers=HEADERS, timeout=10.0)
        
        if response.status_code == 200:
            print("PASS Candidate Upload: Successfully uploaded test candidate")
            return True
        else:
            print(f"FAIL Candidate Upload: {response.status_code} - {response.text}")
            return False

async def test_candidate_search():
    """Test searching candidates and verify output"""
    params = {"job_id": 1, "q": "Python"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/v1/candidates/search", params=params, headers=HEADERS, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            count = len(candidates)
            print(f"PASS Candidate Search: Found {count} candidates")
            return count > 0
        else:
            print(f"FAIL Candidate Search: {response.status_code} - {response.text}")
            return False

async def test_interview_scheduling():
    """Test scheduling interview and verify output"""
    interview_data = {
        "candidate_id": 1,
        "job_id": 1,
        "interview_date": "2025-12-05 10:00:00",
        "interviewer": "Test Interviewer",
        "notes": "Test interview scheduling"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/v1/interviews", json=interview_data, headers=HEADERS, timeout=10.0)
        
        if response.status_code == 200:
            result = response.json()
            interview_id = result.get("interview_id", "Unknown")
            print(f"PASS Interview Scheduling: Created interview ID {interview_id}")
            return True
        else:
            print(f"FAIL Interview Scheduling: {response.status_code} - {response.text}")
            return False

async def test_communication():
    """Test communication system and verify output"""
    notification_data = {
        "candidate_name": "Test User",
        "candidate_email": "shashankmishra0411@gmail.com",
        "candidate_phone": "+919284967526", 
        "job_title": "Test Position",
        "message": "HTTP client test notification",
        "channels": ["email"],
        "application_status": "test"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:9001/tools/send-notification", json=notification_data, headers=HEADERS, timeout=15.0)
        
        if response.status_code == 200:
            result = response.json()
            print(f"PASS Communication: Notification sent successfully")
            print(f"  Response: {json.dumps(result, indent=2)[:100]}...")
            return True
        else:
            print(f"FAIL Communication: {response.status_code} - {response.text}")
            return False

async def main():
    print("Testing HR Portal Input/Output Operations")
    print("=" * 50)
    
    tests = [
        ("Job Creation", test_job_creation()),
        ("Candidate Upload", test_candidate_upload()),
        ("Candidate Search", test_candidate_search()),
        ("Interview Scheduling", test_interview_scheduling()),
        ("Communication", test_communication())
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\nTesting {test_name}...")
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR {test_name}: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("All HTTP client fixes verified with real data!")
    else:
        print("Some operations need attention")

if __name__ == "__main__":
    asyncio.run(main())