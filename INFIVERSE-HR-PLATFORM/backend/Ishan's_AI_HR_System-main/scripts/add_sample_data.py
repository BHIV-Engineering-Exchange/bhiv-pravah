import requests
import json
import sys
import os

API_BASE = "http://localhost:5000"

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Sample candidates data
sample_candidates = [
    {
        "name": "John Smith",
        "email": "john.smith@email.com",
        "phone": "+91-9876543210",
        "skills": ["Python", "FastAPI", "Machine Learning", "SQL"]
    },
    {
        "name": "Sarah Johnson",
        "email": "sarah.j@email.com", 
        "phone": "+91-9876543211",
        "skills": ["React", "JavaScript", "Node.js", "MongoDB"]
    },
    {
        "name": "Mike Chen",
        "email": "mike.chen@email.com",
        "phone": "+91-9876543212", 
        "skills": ["Java", "Spring Boot", "Microservices", "Docker"]
    },
    {
        "name": "Emily Davis",
        "email": "emily.davis@email.com",
        "phone": "+91-9876543213",
        "skills": ["Data Science", "Python", "TensorFlow", "Analytics"]
    },
    {
        "name": "Alex Rodriguez",
        "email": "alex.r@email.com",
        "phone": "+91-9876543214",
        "skills": ["DevOps", "AWS", "Kubernetes", "CI/CD"]
    }
]

# Sample feedback data
sample_feedback = [
    {
        "candidate_id": 1,
        "feedback_score": 4,
        "comment": "Strong technical skills, good communication",
        "actual_outcome": "accept"
    },
    {
        "candidate_id": 2,
        "feedback_score": 5,
        "comment": "Excellent frontend skills, team player",
        "actual_outcome": "accept"
    },
    {
        "candidate_id": 3,
        "feedback_score": 3,
        "comment": "Good technical knowledge, needs improvement in soft skills",
        "actual_outcome": "reconsider"
    },
    {
        "candidate_id": 4,
        "feedback_score": 5,
        "comment": "Outstanding data science expertise",
        "actual_outcome": "accept"
    },
    {
        "candidate_id": 5,
        "feedback_score": 2,
        "comment": "Limited experience, not suitable for senior role",
        "actual_outcome": "reject"
    }
]

def add_sample_data():
    print("🚀 Adding sample data to HR-AI System...")
    
    # Add candidates
    print("\n👥 Adding sample candidates...")
    for i, candidate in enumerate(sample_candidates, 1):
        try:
            response = requests.post(f"{API_BASE}/candidate/add", json=candidate)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Added candidate {i}: {candidate['name']} (ID: {result.get('candidate_id')})")
            else:
                print(f"❌ Failed to add candidate {i}: {response.text}")
        except Exception as e:
            print(f"❌ Error adding candidate {i}: {e}")
    
    # Add feedback
    print("\n💬 Adding sample feedback...")
    for i, feedback in enumerate(sample_feedback, 1):
        try:
            response = requests.post(f"{API_BASE}/feedback/hr_feedback", json=feedback)
            if response.status_code == 200:
                print(f"✅ Added feedback {i} for candidate {feedback['candidate_id']}")
            else:
                print(f"❌ Failed to add feedback {i}: {response.text}")
        except Exception as e:
            print(f"❌ Error adding feedback {i}: {e}")
    
    print("\n🎉 Sample data added successfully!")
    print("📊 You can now view the data in the dashboard at: http://localhost:8501")

if __name__ == "__main__":
    add_sample_data()