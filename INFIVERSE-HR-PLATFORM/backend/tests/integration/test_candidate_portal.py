#!/usr/bin/env python3
"""
BHIV HR Platform - Candidate Portal API Testing
Tests candidate registration, login, profile management, and job applications
"""

import requests
import json
import time
from datetime import datetime

# Configuration
GATEWAY_URL = "http://localhost:8000"  # Local development
# GATEWAY_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"  # Production
API_KEY = "<YOUR_API_KEY>"

def make_request(endpoint, method="GET", data=None, token=None):
    """Make API request with proper headers"""
    url = f"{GATEWAY_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token or API_KEY}"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e)}

def test_candidate_registration():
    """Test candidate registration"""
    print("Testing Candidate Registration...")
    
    candidate_data = {
        "name": "John Doe",
        "email": f"john.doe.{int(time.time())}@example.com",  # Unique email
        "password": "SecurePass123!",
        "phone": "+1 (555) 123-4567",
        "location": "New York, NY",
        "experience_years": 5,
        "technical_skills": "Python, JavaScript, React, SQL, AWS",
        "education_level": "Bachelor's",
        "seniority_level": "Mid"
    }
    
    status, response = make_request("/v1/candidate/register", "POST", candidate_data)
    
    if status == 200 and response.get("success"):
        print(f"Registration successful: {response['message']}")
        print(f"   Candidate ID: {response['candidate_id']}")
        return candidate_data["email"], response["candidate_id"]
    else:
        print(f"Registration failed: {response}")
        return None, None

def test_candidate_login(email):
    """Test candidate login"""
    print("Testing Candidate Login...")
    
    login_data = {
        "email": email,
        "password": "SecurePass123!"
    }
    
    status, response = make_request("/v1/candidate/login", "POST", login_data)
    
    if status == 200 and response.get("success"):
        print(f"Login successful: {response['message']}")
        print(f"   Token: {response['token'][:50]}...")
        print(f"   Candidate: {response['candidate']['name']}")
        return response["token"], response["candidate"]
    else:
        print(f"Login failed: {response}")
        return None, None

def test_profile_update(candidate_id, token):
    """Test profile update"""
    print("Testing Profile Update...")
    
    update_data = {
        "name": "John Doe Updated",
        "phone": "+1 (555) 987-6543",
        "location": "San Francisco, CA",
        "experience_years": 6,
        "technical_skills": "Python, JavaScript, React, SQL, AWS, Docker, Kubernetes",
        "seniority_level": "Senior"
    }
    
    status, response = make_request(f"/v1/candidate/profile/{candidate_id}", "PUT", update_data, token)
    
    if status == 200 and response.get("success"):
        print(f"Profile update successful: {response['message']}")
    else:
        print(f"Profile update failed: {response}")

def test_job_application(candidate_id, token):
    """Test job application"""
    print("Testing Job Application...")
    
    # First, get available jobs
    status, jobs_response = make_request("/v1/jobs", "GET", token=token)
    
    if status == 200 and jobs_response.get("jobs"):
        job_id = jobs_response["jobs"][0]["id"]
        job_title = jobs_response["jobs"][0]["title"]
        print(f"   Applying for: {job_title} (ID: {job_id})")
        
        application_data = {
            "candidate_id": candidate_id,
            "job_id": job_id,
            "cover_letter": "I am very interested in this position and believe my skills align well with the requirements."
        }
        
        status, response = make_request("/v1/candidate/apply", "POST", application_data, token)
        
        if status == 200 and response.get("success"):
            print(f"Application successful: {response['message']}")
            print(f"   Application ID: {response['application_id']}")
            return response["application_id"]
        else:
            print(f"Application failed: {response}")
    else:
        print(f"Could not get jobs: {jobs_response}")
    
    return None

def test_get_applications(candidate_id, token):
    """Test getting candidate applications"""
    print("Testing Get Applications...")
    
    status, response = make_request(f"/v1/candidate/applications/{candidate_id}", "GET", token=token)
    
    if status == 200:
        applications = response.get("applications", [])
        print(f"Retrieved {len(applications)} applications")
        
        for app in applications:
            print(f"   - {app['job_title']} at {app['company']} ({app['status']})")
    else:
        print(f"Failed to get applications: {response}")

def test_job_search():
    """Test job search functionality"""
    print("Testing Job Search...")
    
    # Test basic job listing
    status, response = make_request("/v1/jobs", "GET")
    
    if status == 200:
        jobs = response.get("jobs", [])
        print(f"Found {len(jobs)} available jobs")
        
        for job in jobs[:3]:  # Show first 3 jobs
            print(f"   - {job['title']} in {job['location']} ({job['experience_level']})")
    else:
        print(f"Job search failed: {response}")

def run_candidate_portal_tests():
    """Run all candidate portal tests"""
    print("BHIV HR Platform - Candidate Portal API Testing")
    print("=" * 60)
    
    # Test 1: Job Search (no auth required)
    test_job_search()
    print()
    
    # Test 2: Candidate Registration
    email, candidate_id = test_candidate_registration()
    if not email or not candidate_id:
        print("Registration failed, stopping tests")
        return
    print()
    
    # Test 3: Candidate Login
    token, candidate = test_candidate_login(email)
    if not token or not candidate:
        print("Login failed, stopping tests")
        return
    print()
    
    # Test 4: Profile Update
    test_profile_update(candidate_id, token)
    print()
    
    # Test 5: Job Application
    application_id = test_job_application(candidate_id, token)
    print()
    
    # Test 6: Get Applications
    test_get_applications(candidate_id, token)
    print()
    
    print("All Candidate Portal tests completed!")
    print(f"Test Summary:")
    print(f"   - Candidate ID: {candidate_id}")
    print(f"   - Email: {email}")
    print(f"   - Token: {token[:30]}...")
    if application_id:
        print(f"   - Application ID: {application_id}")

if __name__ == "__main__":
    run_candidate_portal_tests()
