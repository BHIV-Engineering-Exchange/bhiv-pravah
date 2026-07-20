#!/usr/bin/env python3
"""Verify actual data changes from HTTP client tests"""

import asyncio
import httpx

API_KEY = "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

async def verify_data():
    async with httpx.AsyncClient() as client:
        # Check jobs
        jobs_response = await client.get("http://localhost:8000/v1/jobs", headers=HEADERS)
        if jobs_response.status_code == 200:
            jobs = jobs_response.json().get('jobs', [])
            test_jobs = [j for j in jobs if 'Test Software Engineer' in j.get('title', '')]
            print(f"Jobs: {len(jobs)} total, {len(test_jobs)} test jobs created")
        
        # Check candidates  
        candidates_response = await client.get("http://localhost:8000/v1/candidates/search?job_id=1", headers=HEADERS)
        if candidates_response.status_code == 200:
            candidates = candidates_response.json().get('candidates', [])
            test_candidates = [c for c in candidates if 'Test Candidate' in c.get('name', '')]
            print(f"Candidates: {len(candidates)} total, {len(test_candidates)} test candidates")
        
        # Check interviews
        interviews_response = await client.get("http://localhost:8000/v1/interviews", headers=HEADERS)
        if interviews_response.status_code == 200:
            interviews = interviews_response.json().get('interviews', [])
            test_interviews = [i for i in interviews if 'Test Interviewer' in i.get('interviewer', '')]
            print(f"Interviews: {len(interviews)} total, {len(test_interviews)} test interviews")

if __name__ == "__main__":
    asyncio.run(verify_data())