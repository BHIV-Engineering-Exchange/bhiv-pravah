"""
Create test users for E2E testing
Run this script to create test users in your database
"""

import requests
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

BACKEND_URL = "http://localhost:3000"

TEST_USERS = [
    {
        "email": "test.student@gurukul.com",
        "password": "Test123!@#",
        "name": "Test Student",
        "role": "student"
    },
    {
        "email": "test.teacher@gurukul.com",
        "password": "Test123!@#",
        "name": "Test Teacher",
        "role": "teacher"
    },
    {
        "email": "test.admin@gurukul.com",
        "password": "Test123!@#",
        "name": "Test Admin",
        "role": "admin"
    }
]

def create_test_users():
    """Create test users via API"""
    print("Creating test users...\n")
    
    for user in TEST_USERS:
        try:
            # Register user (correct endpoint is /register, not /signup)
            response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/register",
                json={
                    "email": user["email"],
                    "password": user["password"],
                    "full_name": user["name"],  # Use full_name, not name
                    "role": user["role"].upper()  # Role should be uppercase
                }
            )
            
            if response.status_code == 200 or response.status_code == 201:
                print(f"✅ Created: {user['email']} ({user['role']})")
            elif response.status_code == 400:
                # Check if it's because user already exists
                error_text = response.text.lower()
                if "already" in error_text or "exists" in error_text:
                    print(f"⚠️  Already exists: {user['email']}")
                else:
                    print(f"❌ Failed: {user['email']} - {response.status_code}")
                    print(f"   Response: {response.text}")
            else:
                print(f"❌ Failed: {user['email']} - {response.status_code}")
                print(f"   Response: {response.text}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection error: Backend not running at {BACKEND_URL}")
            print(f"   Please start the backend first (run start-all.bat)")
            break
        except Exception as e:
            print(f"❌ Error creating {user['email']}: {e}")
    
    print("\n✅ Test users setup complete!")
    print("\nYou can now run E2E tests with:")
    print("  cd tests/e2e")
    print("  npm test")

if __name__ == "__main__":
    create_test_users()

