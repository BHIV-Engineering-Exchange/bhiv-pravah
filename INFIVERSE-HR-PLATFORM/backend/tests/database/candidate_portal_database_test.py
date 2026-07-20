#!/usr/bin/env python3
"""
Candidate Portal Database Testing
Tests candidate registration, authentication, and data flow
"""

import psycopg2
import bcrypt
import requests
import json
from datetime import datetime
import uuid

# Database connection
DATABASE_URL = "postgresql://bhiv_user:JwvtCqKDYsVgnTiAEtSNAKaDHkksATRA@dpg-d4kjncvpm1nc738abapg-a.oregon-postgres.render.com/bhiv_hr_i7zb"
GATEWAY_SERVICE_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"

def generate_unique_credentials():
    """Generate unique test credentials"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": f"Test Candidate {unique_id}",
        "email": f"test.candidate.{unique_id}@example.com",
        "password": f"TestPass123!{unique_id}",
        "phone": f"+1-555-{unique_id[:4]}",
        "location": f"Test City {unique_id[:4]}",
        "experience_years": 3,
        "technical_skills": "Python, JavaScript, React, SQL, AWS",
        "education_level": "Bachelor's",
        "seniority_level": "Mid"
    }

def test_direct_database_candidate_creation():
    """Test direct database candidate creation"""
    print("Testing Direct Database Candidate Creation")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Generate unique credentials
        test_data = generate_unique_credentials()
        
        # Hash password
        password_hash = bcrypt.hashpw(test_data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert candidate directly into database
        insert_query = """
            INSERT INTO candidates (name, email, phone, location, experience_years, technical_skills, 
                                  education_level, seniority_level, password_hash, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'applied', NOW())
            RETURNING id, name, email, created_at
        """
        
        cursor.execute(insert_query, (
            test_data["name"],
            test_data["email"],
            test_data["phone"],
            test_data["location"],
            test_data["experience_years"],
            test_data["technical_skills"],
            test_data["education_level"],
            test_data["seniority_level"],
            password_hash
        ))
        
        result = cursor.fetchone()
        candidate_id = result[0]
        
        conn.commit()
        
        print(f"✅ Direct Database Insert: SUCCESS")
        print(f"   Candidate ID: {candidate_id}")
        print(f"   Name: {result[1]}")
        print(f"   Email: {result[2]}")
        print(f"   Created: {result[3]}")
        
        # Verify data integrity
        verify_query = """
            SELECT name, email, phone, location, experience_years, technical_skills, 
                   education_level, seniority_level, password_hash, status
            FROM candidates WHERE id = %s
        """
        cursor.execute(verify_query, (candidate_id,))
        verify_result = cursor.fetchone()
        
        print(f"✅ Data Verification:")
        print(f"   Name: {verify_result[0]}")
        print(f"   Email: {verify_result[1]}")
        print(f"   Phone: {verify_result[2]}")
        print(f"   Location: {verify_result[3]}")
        print(f"   Experience: {verify_result[4]} years")
        print(f"   Skills: {verify_result[5][:50]}...")
        print(f"   Education: {verify_result[6]}")
        print(f"   Seniority: {verify_result[7]}")
        print(f"   Password Hash: {'✅ Present' if verify_result[8] else '❌ Missing'}")
        print(f"   Status: {verify_result[9]}")
        
        cursor.close()
        conn.close()
        
        return candidate_id, test_data
        
    except Exception as e:
        print(f"❌ Direct Database Test: FAILED - {e}")
        return None, None

def test_candidate_registration_api():
    """Test candidate registration through API"""
    print("\nTesting Candidate Registration API")
    
    try:
        # Generate unique credentials
        test_data = generate_unique_credentials()
        
        # Call registration API
        response = requests.post(
            f"{GATEWAY_SERVICE_URL}/v1/candidate/register",
            json=test_data,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ API Registration: SUCCESS")
                print(f"   Candidate ID: {data.get('candidate_id')}")
                print(f"   Message: {data.get('message')}")
                
                # Verify in database
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT name, email, phone, location, experience_years, technical_skills,
                           education_level, seniority_level, password_hash, status
                    FROM candidates WHERE id = %s
                """, (data.get('candidate_id'),))
                
                db_result = cursor.fetchone()
                if db_result:
                    print(f"✅ Database Sync Verification:")
                    print(f"   Name: {db_result[0]} {'✅' if db_result[0] == test_data['name'] else '❌'}")
                    print(f"   Email: {db_result[1]} {'✅' if db_result[1] == test_data['email'] else '❌'}")
                    print(f"   Phone: {db_result[2]} {'✅' if db_result[2] == test_data['phone'] else '❌'}")
                    print(f"   Location: {db_result[3]} {'✅' if db_result[3] == test_data['location'] else '❌'}")
                    print(f"   Experience: {db_result[4]} {'✅' if db_result[4] == test_data['experience_years'] else '❌'}")
                    print(f"   Skills: {db_result[5][:30]}... {'✅' if db_result[5] == test_data['technical_skills'] else '❌'}")
                    print(f"   Education: {db_result[6]} {'✅' if db_result[6] == test_data['education_level'] else '❌'}")
                    print(f"   Seniority: {db_result[7]} {'✅' if db_result[7] == test_data['seniority_level'] else '❌'}")
                    print(f"   Password Hash: {'✅ Present' if db_result[8] else '❌ Missing'}")
                    print(f"   Status: {db_result[9]}")
                
                cursor.close()
                conn.close()
                
                return data.get('candidate_id'), test_data
            else:
                print(f"❌ API Registration: FAILED - {data.get('error')}")
                return None, None
        else:
            print(f"❌ API Registration: FAILED - Status {response.status_code}")
            print(f"   Response: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ API Registration Test: FAILED - {e}")
        return None, None

def test_candidate_login_api(test_data):
    """Test candidate login through API"""
    print("\nTesting Candidate Login API")
    
    try:
        login_data = {
            "email": test_data["email"],
            "password": test_data["password"]
        }
        
        response = requests.post(
            f"{GATEWAY_SERVICE_URL}/v1/candidate/login",
            json=login_data,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Login API: SUCCESS")
                print(f"   Message: {data.get('message')}")
                print(f"   Token: {'✅ Present' if data.get('token') else '❌ Missing'}")
                
                candidate = data.get("candidate", {})
                print(f"✅ Candidate Data Retrieved:")
                print(f"   ID: {candidate.get('id')}")
                print(f"   Name: {candidate.get('name')}")
                print(f"   Email: {candidate.get('email')}")
                print(f"   Location: {candidate.get('location')}")
                print(f"   Experience: {candidate.get('experience_years')} years")
                print(f"   Skills: {candidate.get('technical_skills', '')[:50]}...")
                
                return data.get("token"), candidate
            else:
                print(f"❌ Login API: FAILED - {data.get('error')}")
                return None, None
        else:
            print(f"❌ Login API: FAILED - Status {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"❌ Login API Test: FAILED - {e}")
        return None, None

def test_job_application_flow(candidate_id, token):
    """Test job application flow"""
    print("\nTesting Job Application Flow")
    
    try:
        # First, get available jobs
        response = requests.get(f"{GATEWAY_SERVICE_URL}/v1/jobs", timeout=10)
        if response.status_code == 200:
            jobs_data = response.json()
            jobs = jobs_data.get("jobs", [])
            
            if jobs:
                job_id = jobs[0]["id"]
                print(f"✅ Available Jobs: {len(jobs)} found")
                print(f"   Testing with Job: {jobs[0]['title']} (ID: {job_id})")
                
                # Apply for job
                application_data = {
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "cover_letter": "Test application through candidate portal"
                }
                
                headers = {"Authorization": f"Bearer {token}"}
                app_response = requests.post(
                    f"{GATEWAY_SERVICE_URL}/v1/candidate/apply",
                    json=application_data,
                    headers=headers,
                    timeout=15
                )
                
                if app_response.status_code == 200:
                    app_data = app_response.json()
                    if app_data.get("success"):
                        print(f"✅ Job Application: SUCCESS")
                        print(f"   Application ID: {app_data.get('application_id')}")
                        
                        # Verify in database
                        conn = psycopg2.connect(DATABASE_URL)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT ja.id, ja.candidate_id, ja.job_id, ja.status, ja.applied_date,
                                   j.title as job_title
                            FROM job_applications ja
                            LEFT JOIN jobs j ON ja.job_id = j.id
                            WHERE ja.candidate_id = %s AND ja.job_id = %s
                        """, (candidate_id, job_id))
                        
                        app_result = cursor.fetchone()
                        if app_result:
                            print(f"✅ Application Database Verification:")
                            print(f"   Application ID: {app_result[0]}")
                            print(f"   Candidate ID: {app_result[1]}")
                            print(f"   Job ID: {app_result[2]}")
                            print(f"   Status: {app_result[3]}")
                            print(f"   Applied Date: {app_result[4]}")
                            print(f"   Job Title: {app_result[5]}")
                        
                        cursor.close()
                        conn.close()
                        return True
                    else:
                        print(f"❌ Job Application: FAILED - {app_data.get('error')}")
                        return False
                else:
                    print(f"❌ Job Application: FAILED - Status {app_response.status_code}")
                    return False
            else:
                print("❌ No jobs available for testing")
                return False
        else:
            print(f"❌ Jobs API: FAILED - Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Job Application Test: FAILED - {e}")
        return False

def test_profile_update(candidate_id, token):
    """Test profile update functionality"""
    print("\nTesting Profile Update")
    
    try:
        update_data = {
            "name": "Updated Test Name",
            "phone": "+1-555-9999",
            "location": "Updated City",
            "technical_skills": "Python, JavaScript, React, SQL, AWS, Docker, Kubernetes"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(
            f"{GATEWAY_SERVICE_URL}/v1/candidate/profile/{candidate_id}",
            json=update_data,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Profile Update: SUCCESS")
                
                # Verify in database
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT name, phone, location, technical_skills, updated_at
                    FROM candidates WHERE id = %s
                """, (candidate_id,))
                
                result = cursor.fetchone()
                if result:
                    print(f"✅ Updated Profile Verification:")
                    print(f"   Name: {result[0]} {'✅' if result[0] == update_data['name'] else '❌'}")
                    print(f"   Phone: {result[1]} {'✅' if result[1] == update_data['phone'] else '❌'}")
                    print(f"   Location: {result[2]} {'✅' if result[2] == update_data['location'] else '❌'}")
                    print(f"   Skills: {result[3][:50]}... {'✅' if result[3] == update_data['technical_skills'] else '❌'}")
                    print(f"   Updated At: {result[4]}")
                
                cursor.close()
                conn.close()
                return True
            else:
                print(f"❌ Profile Update: FAILED - {data.get('error')}")
                return False
        else:
            print(f"❌ Profile Update: FAILED - Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Profile Update Test: FAILED - {e}")
        return False

def main():
    """Run all candidate portal database tests"""
    print("BHIV HR Platform - Candidate Portal Database Testing")
    print("=" * 70)
    
    results = []
    
    # Test 1: Direct Database Creation
    print("\n" + "="*50)
    candidate_id_direct, test_data_direct = test_direct_database_candidate_creation()
    results.append(("Direct Database Creation", candidate_id_direct is not None))
    
    # Test 2: API Registration
    print("\n" + "="*50)
    candidate_id_api, test_data_api = test_candidate_registration_api()
    results.append(("API Registration", candidate_id_api is not None))
    
    if candidate_id_api and test_data_api:
        # Test 3: Login API
        token, candidate_data = test_candidate_login_api(test_data_api)
        results.append(("Login API", token is not None))
        
        if token and candidate_data:
            # Test 4: Job Application Flow
            app_success = test_job_application_flow(candidate_data.get("id"), token)
            results.append(("Job Application Flow", app_success))
            
            # Test 5: Profile Update
            profile_success = test_profile_update(candidate_data.get("id"), token)
            results.append(("Profile Update", profile_success))
    
    # Summary
    print("\n" + "=" * 70)
    print("CANDIDATE PORTAL DATABASE TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("All Candidate Portal database tests PASSED!")
        print("Values are properly stored and synced in database")
        print("Pipeline is working correctly")
        return True
    else:
        print("Some Candidate Portal database tests FAILED!")
        return False

if __name__ == "__main__":
    main()
