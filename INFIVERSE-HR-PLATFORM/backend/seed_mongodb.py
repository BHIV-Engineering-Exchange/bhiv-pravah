"""
MongoDB Seed Data Script for BHIV HR Platform
Seeds initial data into MongoDB Atlas collections
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from bson import ObjectId
import random

# Load environment variables
load_dotenv()

# Get connection string
uri = os.getenv("DATABASE_URL")
db_name = os.getenv("MONGODB_DB_NAME", "bhiv_hr")

if not uri:
    print("❌ DATABASE_URL not found in environment variables")
    exit(1)

print(f"🔗 Connecting to MongoDB Atlas...")
client = MongoClient(uri, serverSelectionTimeoutMS=10000)
db = client[db_name]

def seed_jobs():
    """Seed jobs collection"""
    print("\n📋 Seeding jobs collection...")
    
    jobs = [
        {
            "title": "Senior Python Developer",
            "department": "Engineering",
            "location": "Remote",
            "experience_level": "Senior",
            "requirements": "Python, Django, FastAPI, PostgreSQL, MongoDB, REST APIs, 5+ years experience",
            "description": "We are looking for a senior Python developer to join our engineering team and build scalable web applications.",
            "client_code": "TECH001",
            "employment_type": "Full-time",
            "salary_range": "$120,000 - $150,000",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "AI/ML Engineer",
            "department": "Data Science",
            "location": "Hybrid",
            "experience_level": "Mid-Senior",
            "requirements": "Python, TensorFlow, PyTorch, Scikit-learn, NLP, Computer Vision, 3+ years experience",
            "description": "Join our AI team to build cutting-edge machine learning models for HR automation.",
            "client_code": "AI002",
            "employment_type": "Full-time",
            "salary_range": "$130,000 - $160,000",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Frontend Developer",
            "department": "Engineering",
            "location": "Remote",
            "experience_level": "Mid",
            "requirements": "React, TypeScript, Tailwind CSS, Next.js, 2+ years experience",
            "description": "Looking for a frontend developer to build beautiful and responsive user interfaces.",
            "client_code": "TECH001",
            "employment_type": "Full-time",
            "salary_range": "$90,000 - $120,000",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "DevOps Engineer",
            "department": "Infrastructure",
            "location": "Remote",
            "experience_level": "Senior",
            "requirements": "Docker, Kubernetes, AWS, CI/CD, Terraform, 4+ years experience",
            "description": "Seeking a DevOps engineer to manage our cloud infrastructure and deployment pipelines.",
            "client_code": "INFRA003",
            "employment_type": "Full-time",
            "salary_range": "$110,000 - $140,000",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "HR Manager",
            "department": "Human Resources",
            "location": "On-site",
            "experience_level": "Senior",
            "requirements": "HR Management, Recruitment, Employee Relations, HRIS, 5+ years experience",
            "description": "Looking for an experienced HR Manager to lead our people operations.",
            "client_code": "HR004",
            "employment_type": "Full-time",
            "salary_range": "$80,000 - $100,000",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    result = db.jobs.insert_many(jobs)
    print(f"   ✅ Inserted {len(result.inserted_ids)} jobs")
    return result.inserted_ids

def seed_candidates(job_ids):
    """Seed candidates collection"""
    print("\n👥 Seeding candidates collection...")
    
    skills_pool = [
        "Python", "JavaScript", "TypeScript", "React", "Node.js", "Django", "FastAPI",
        "MongoDB", "PostgreSQL", "AWS", "Docker", "Kubernetes", "TensorFlow", "PyTorch",
        "Machine Learning", "NLP", "REST APIs", "GraphQL", "Git", "CI/CD"
    ]
    
    candidates = []
    for i in range(1, 21):  # Create 20 candidates
        selected_skills = random.sample(skills_pool, random.randint(4, 8))
        candidates.append({
            "name": f"Candidate {i}",
            "email": f"candidate{i}@example.com",
            "phone": f"+91-98{random.randint(10000000, 99999999)}",
            "skills": selected_skills,
            "technical_skills": ", ".join(selected_skills),
            "experience_years": random.randint(1, 10),
            "current_company": f"Company {chr(64 + (i % 26) + 1)}",
            "current_role": random.choice(["Developer", "Engineer", "Analyst", "Manager", "Lead"]),
            "education": random.choice(["B.Tech", "M.Tech", "MBA", "B.Sc", "M.Sc"]),
            "location": random.choice(["Mumbai", "Bangalore", "Delhi", "Hyderabad", "Pune", "Remote"]),
            "resume_text": f"Experienced professional with expertise in {', '.join(selected_skills[:3])}",
            "status": random.choice(["active", "shortlisted", "interviewed", "hired"]),
            "match_score": random.randint(50, 100),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            "updated_at": datetime.utcnow()
        })
    
    result = db.candidates.insert_many(candidates)
    print(f"   ✅ Inserted {len(result.inserted_ids)} candidates")
    return result.inserted_ids

def seed_job_applications(job_ids, candidate_ids):
    """Seed job_applications collection"""
    print("\n📝 Seeding job_applications collection...")
    
    applications = []
    for candidate_id in candidate_ids[:15]:  # First 15 candidates apply
        job_id = random.choice(job_ids)
        applications.append({
            "candidate_id": candidate_id,
            "job_id": job_id,
            "status": random.choice(["pending", "reviewed", "shortlisted", "rejected", "hired"]),
            "match_score": random.randint(50, 100),
            "applied_at": datetime.utcnow() - timedelta(days=random.randint(0, 20)),
            "updated_at": datetime.utcnow(),
            "notes": "Application submitted via portal"
        })
    
    result = db.job_applications.insert_many(applications)
    print(f"   ✅ Inserted {len(result.inserted_ids)} job applications")
    return result.inserted_ids

def seed_clients():
    """Seed clients collection"""
    print("\n🏢 Seeding clients collection...")
    
    clients = [
        {
            "company_name": "TechCorp Solutions",
            "email": "hr@techcorp.com",
            "phone": "+91-9876543210",
            "industry": "Technology",
            "client_code": "TECH001",
            "contact_person": "John Smith",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "company_name": "AI Innovations Ltd",
            "email": "hiring@aiinnovations.com",
            "phone": "+91-9876543211",
            "industry": "Artificial Intelligence",
            "client_code": "AI002",
            "contact_person": "Sarah Johnson",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "company_name": "CloudInfra Services",
            "email": "talent@cloudinfra.com",
            "phone": "+91-9876543212",
            "industry": "Cloud Infrastructure",
            "client_code": "INFRA003",
            "contact_person": "Mike Wilson",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    result = db.clients.insert_many(clients)
    print(f"   ✅ Inserted {len(result.inserted_ids)} clients")
    return result.inserted_ids

def seed_users():
    """Seed users collection (HR users)"""
    print("\n👤 Seeding users collection...")
    
    users = [
        {
            "username": "admin",
            "email": "admin@bhiv.hr",
            "role": "admin",
            "name": "System Admin",
            "status": "active",
            "password_hash": "hashed_password_placeholder",  # In production, use proper hashing
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "username": "hr_manager",
            "email": "hr.manager@bhiv.hr",
            "role": "hr_manager",
            "name": "HR Manager",
            "status": "active",
            "password_hash": "hashed_password_placeholder",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "username": "recruiter1",
            "email": "recruiter@bhiv.hr",
            "role": "recruiter",
            "name": "Recruiter One",
            "status": "active",
            "password_hash": "hashed_password_placeholder",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    result = db.users.insert_many(users)
    print(f"   ✅ Inserted {len(result.inserted_ids)} users")
    return result.inserted_ids

def seed_interviews(job_ids, candidate_ids):
    """Seed interviews collection"""
    print("\n📅 Seeding interviews collection...")
    
    interviews = []
    for i, candidate_id in enumerate(candidate_ids[:5]):  # 5 interviews
        interviews.append({
            "candidate_id": candidate_id,
            "job_id": random.choice(job_ids),
            "interviewer": f"Interviewer {i + 1}",
            "scheduled_at": datetime.utcnow() + timedelta(days=random.randint(1, 14)),
            "duration_minutes": random.choice([30, 45, 60]),
            "interview_type": random.choice(["technical", "hr", "cultural_fit", "final"]),
            "status": random.choice(["scheduled", "completed", "cancelled"]),
            "notes": "Interview scheduled via system",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
    
    result = db.interviews.insert_many(interviews)
    print(f"   ✅ Inserted {len(result.inserted_ids)} interviews")
    return result.inserted_ids

def seed_feedback(candidate_ids):
    """Seed feedback collection"""
    print("\n💬 Seeding feedback collection...")
    
    feedback_entries = []
    for candidate_id in candidate_ids[:10]:  # 10 feedback entries
        feedback_entries.append({
            "candidate_id": candidate_id,
            "feedback_type": random.choice(["interview", "assessment", "cultural_fit"]),
            "score": random.randint(1, 5),
            "comments": "Good candidate with relevant experience",
            "reviewer": f"Reviewer {random.randint(1, 5)}",
            "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 10)),
            "updated_at": datetime.utcnow()
        })
    
    result = db.feedback.insert_many(feedback_entries)
    print(f"   ✅ Inserted {len(result.inserted_ids)} feedback entries")
    return result.inserted_ids

def seed_rl_data(candidate_ids, job_ids):
    """Seed RL-related collections"""
    print("\n🤖 Seeding RL collections...")
    
    # RL Predictions
    predictions = []
    for i in range(10):
        predictions.append({
            "candidate_id": random.choice(candidate_ids),
            "job_id": random.choice(job_ids),
            "rl_score": random.uniform(50, 100),
            "confidence_level": random.uniform(60, 95),
            "decision_type": random.choice(["recommend", "review", "reject"]),
            "features": {
                "skill_match": random.uniform(0.5, 1.0),
                "experience_score": random.uniform(0.4, 1.0),
                "education_score": random.uniform(0.5, 1.0)
            },
            "model_version": "v1.0.0",
            "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 10))
        })
    
    if predictions:
        result = db.rl_predictions.insert_many(predictions)
        print(f"   ✅ Inserted {len(result.inserted_ids)} RL predictions")
    
    # RL Feedback
    rl_feedback = []
    for pred in predictions[:5]:
        rl_feedback.append({
            "prediction_id": pred.get("_id"),
            "feedback_source": random.choice(["hr", "system", "candidate"]),
            "actual_outcome": random.choice(["hired", "shortlisted", "rejected"]),
            "feedback_score": random.randint(1, 5),
            "reward_signal": random.uniform(-1, 1),
            "feedback_notes": "Feedback recorded",
            "created_at": datetime.utcnow()
        })
    
    if rl_feedback:
        result = db.rl_feedback.insert_many(rl_feedback)
        print(f"   ✅ Inserted {len(result.inserted_ids)} RL feedback entries")

def seed_workflows():
    """Seed workflows collection"""
    print("\n🔄 Seeding workflows collection...")
    
    workflows = [
        {
            "workflow_id": f"WF_{ObjectId()}",
            "workflow_type": "application_screening",
            "status": "completed",
            "candidate_id": None,  # Will be linked
            "job_id": None,
            "started_at": datetime.utcnow() - timedelta(hours=2),
            "completed_at": datetime.utcnow() - timedelta(hours=1),
            "result": {"status": "success", "action": "shortlisted"}
        },
        {
            "workflow_id": f"WF_{ObjectId()}",
            "workflow_type": "interview_scheduling",
            "status": "in_progress",
            "candidate_id": None,
            "job_id": None,
            "started_at": datetime.utcnow() - timedelta(minutes=30),
            "completed_at": None,
            "result": None
        }
    ]
    
    result = db.workflows.insert_many(workflows)
    print(f"   ✅ Inserted {len(result.inserted_ids)} workflows")

def seed_additional_collections(candidate_ids, job_ids):
    """Seed additional collections needed for full platform functionality"""
    print("\n📋 Seeding additional collections...")
    
    # 1. Offers collection
    offers = [
        {
            "candidate_id": candidate_ids[0],
            "job_id": job_ids[0],
            "offer_amount": 135000,
            "currency": "USD",
            "start_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "status": "pending",
            "benefits": ["Health Insurance", "401k", "Remote Work"],
            "notes": "Initial offer for senior position",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "candidate_id": candidate_ids[1],
            "job_id": job_ids[1],
            "offer_amount": 145000,
            "currency": "USD",
            "start_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
            "status": "accepted",
            "benefits": ["Health Insurance", "Stock Options", "Flexible Hours"],
            "notes": "AI/ML position offer",
            "created_at": datetime.utcnow() - timedelta(days=5),
            "updated_at": datetime.utcnow()
        }
    ]
    db.offers.insert_many(offers)
    print("   ✅ Offers collection seeded")
    
    # 2. Audit logs collection
    audit_logs = [
        {
            "action": "user_login",
            "resource": "auth",
            "resource_id": "admin",
            "user_id": "system",
            "details": {"ip": "127.0.0.1", "method": "POST"},
            "timestamp": datetime.utcnow()
        },
        {
            "action": "candidate_created",
            "resource": "candidates",
            "resource_id": str(candidate_ids[0]),
            "user_id": "hr_admin",
            "details": {"source": "manual_entry"},
            "timestamp": datetime.utcnow() - timedelta(hours=2)
        }
    ]
    db.audit_logs.insert_many(audit_logs)
    print("   ✅ Audit logs collection seeded")
    
    # 3. Matching cache collection
    matching_cache = [
        {
            "job_id": job_ids[0],
            "candidate_id": candidate_ids[0],
            "match_score": 87.5,
            "skill_match": 92.0,
            "experience_match": 85.0,
            "cultural_fit": 82.0,
            "algorithm_version": "v2.1",
            "cached_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
    ]
    db.matching_cache.insert_many(matching_cache)
    print("   ✅ Matching cache collection seeded")
    
    # 4. Company scoring preferences
    company_preferences = [
        {
            "client_code": "TECH001",
            "company_name": "Tech Innovations Inc",
            "skill_weight": 40,
            "experience_weight": 30,
            "cultural_fit_weight": 20,
            "education_weight": 10,
            "priority_skills": ["Python", "FastAPI", "MongoDB"],
            "min_experience_years": 3,
            "preferred_locations": ["Remote", "San Francisco", "New York"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "client_code": "AI002",
            "company_name": "AI Solutions Ltd",
            "skill_weight": 45,
            "experience_weight": 25,
            "cultural_fit_weight": 20,
            "education_weight": 10,
            "priority_skills": ["Machine Learning", "TensorFlow", "Python"],
            "min_experience_years": 2,
            "preferred_locations": ["Remote", "Hybrid"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    db.company_scoring_preferences.insert_many(company_preferences)
    print("   ✅ Company scoring preferences collection seeded")
    
    # 5. RL Model Performance
    rl_model_performance = [
        {
            "model_version": "v1.0.0",
            "accuracy": 0.87,
            "precision_score": 0.85,
            "recall_score": 0.89,
            "f1_score": 0.87,
            "average_reward": 0.72,
            "total_predictions": 150,
            "evaluation_date": datetime.utcnow() - timedelta(days=7),
            "created_at": datetime.utcnow() - timedelta(days=7)
        },
        {
            "model_version": "v1.1.0",
            "accuracy": 0.91,
            "precision_score": 0.89,
            "recall_score": 0.92,
            "f1_score": 0.90,
            "average_reward": 0.78,
            "total_predictions": 320,
            "evaluation_date": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
    ]
    db.rl_model_performance.insert_many(rl_model_performance)
    print("   ✅ RL model performance collection seeded")
    
    # 6. RL Training Data
    rl_training_data = [
        {
            "candidate_features": {"skills": ["Python", "FastAPI"], "experience_years": 5},
            "job_features": {"requirements": ["Python", "Django"], "level": "Senior"},
            "matching_score": 85.0,
            "actual_outcome": "hired",
            "reward": 1.0,
            "feature_vector": [0.8, 0.9, 0.7, 0.85],
            "created_at": datetime.utcnow() - timedelta(days=30)
        },
        {
            "candidate_features": {"skills": ["JavaScript", "React"], "experience_years": 3},
            "job_features": {"requirements": ["React", "TypeScript"], "level": "Mid"},
            "matching_score": 78.0,
            "actual_outcome": "shortlisted",
            "reward": 0.5,
            "feature_vector": [0.7, 0.8, 0.6, 0.75],
            "created_at": datetime.utcnow() - timedelta(days=15)
        }
    ]
    db.rl_training_data.insert_many(rl_training_data)
    print("   ✅ RL training data collection seeded")
    
    # 7. Schema version
    schema_version = [
        {
            "version": "4.3.0",
            "description": "MongoDB migration with RL + Feedback Agent tables",
            "applied_at": datetime.utcnow()
        }
    ]
    db.schema_version.insert_many(schema_version)
    print("   ✅ Schema version collection seeded")
    
    # 8. Rate limits (empty but indexed)
    db.rate_limits.create_index([("client_ip", 1), ("endpoint", 1)])
    db.rate_limits.create_index("expires_at", expireAfterSeconds=0)
    print("   ✅ Rate limits collection initialized")
    
    # 9. CSP violations (empty but indexed)
    db.csp_violations.create_index("timestamp")
    print("   ✅ CSP violations collection initialized")

def create_indexes():
    """Create indexes for better query performance"""
    print("\n🔍 Creating indexes...")
    
    # Candidates indexes
    db.candidates.create_index("email", unique=True)
    db.candidates.create_index("status")
    db.candidates.create_index("created_at")
    print("   ✅ Candidates indexes created")
    
    # Jobs indexes
    db.jobs.create_index("status")
    db.jobs.create_index("client_code")
    db.jobs.create_index("created_at")
    print("   ✅ Jobs indexes created")
    
    # Job applications indexes
    db.job_applications.create_index([("candidate_id", 1), ("job_id", 1)])
    db.job_applications.create_index("status")
    print("   ✅ Job applications indexes created")
    
    # Clients indexes
    db.clients.create_index("email", unique=True)
    db.clients.create_index("client_code", unique=True)
    print("   ✅ Clients indexes created")
    
    # Users indexes
    db.users.create_index("email", unique=True)
    db.users.create_index("username", unique=True)
    print("   ✅ Users indexes created")
    
    # RL indexes
    db.rl_predictions.create_index([("candidate_id", 1), ("job_id", 1)])
    db.rl_predictions.create_index("created_at")
    db.rl_feedback.create_index("prediction_id")
    print("   ✅ RL indexes created")

def main():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 BHIV HR Platform - MongoDB Seed Data Script")
    print("=" * 60)
    
    # Check if data already exists
    existing_jobs = db.jobs.count_documents({})
    if existing_jobs > 0:
        print(f"\n⚠️  Database already has {existing_jobs} jobs.")
        response = input("Do you want to drop existing data and reseed? (y/N): ")
        if response.lower() != 'y':
            print("❌ Seeding cancelled.")
            return
        
        # Drop all collections
        print("\n🗑️  Dropping existing collections...")
        for collection in ["jobs", "candidates", "job_applications", "clients", 
                          "users", "interviews", "feedback", "rl_predictions", 
                          "rl_feedback", "workflows", "audit_logs"]:
            db[collection].drop()
        print("   ✅ Collections dropped")
    
    # Seed data
    job_ids = seed_jobs()
    candidate_ids = seed_candidates(job_ids)
    seed_job_applications(job_ids, candidate_ids)
    seed_clients()
    seed_users()
    seed_interviews(job_ids, candidate_ids)
    seed_feedback(candidate_ids)
    seed_rl_data(candidate_ids, job_ids)
    seed_workflows()
    
    # Seed missing collections
    seed_additional_collections(candidate_ids, job_ids)
    
    # Create indexes
    create_indexes()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ SEEDING COMPLETE!")
    print("=" * 60)
    
    # Show collection counts
    print("\n📊 Collection Summary:")
    collections = ["jobs", "candidates", "job_applications", "clients", 
                  "users", "interviews", "feedback", "rl_predictions", 
                  "rl_feedback", "workflows", "offers", "audit_logs",
                  "matching_cache", "company_scoring_preferences",
                  "rl_model_performance", "rl_training_data", "schema_version"]
    
    for collection in collections:
        count = db[collection].count_documents({})
        print(f"   • {collection}: {count} documents")
    
    print("\n🎉 Database is ready for testing!")
    print("   Next: Run the services and test API endpoints")

if __name__ == "__main__":
    main()
