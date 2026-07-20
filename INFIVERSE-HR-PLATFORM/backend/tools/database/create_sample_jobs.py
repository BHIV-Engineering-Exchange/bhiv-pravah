#!/usr/bin/env python3
"""
Create sample job postings for BHIV HR Platform
"""

import psycopg2
from datetime import datetime, timedelta

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bhiv_hr',
    'user': 'bhiv_user',
    'password': 'bhiv_local_password_2025'
}

SAMPLE_JOBS = [
    {
        'title': 'Senior Python Developer',
        'description': 'Looking for experienced Python developer with FastAPI, Django, and cloud experience.',
        'requirements': 'Python, FastAPI, Django, AWS, PostgreSQL, 5+ years experience',
        'location': 'Mumbai',
        'experience_required': 5,
        'employment_type': 'Full-time'
    },
    {
        'title': 'Full Stack JavaScript Developer',
        'description': 'React/Node.js developer for modern web applications.',
        'requirements': 'JavaScript, React, Node.js, MongoDB, 3+ years experience',
        'location': 'Bangalore',
        'experience_required': 3,
        'employment_type': 'Full-time'
    },
    {
        'title': 'Data Scientist',
        'description': 'AI/ML engineer for data analysis and machine learning projects.',
        'requirements': 'Python, Machine Learning, TensorFlow, Pandas, NumPy, 4+ years experience',
        'location': 'Hyderabad',
        'experience_required': 4,
        'employment_type': 'Full-time'
    },
    {
        'title': 'DevOps Engineer',
        'description': 'Cloud infrastructure and deployment automation specialist.',
        'requirements': 'AWS, Docker, Kubernetes, Jenkins, Git, 3+ years experience',
        'location': 'Delhi',
        'experience_required': 3,
        'employment_type': 'Full-time'
    },
    {
        'title': 'Junior Java Developer',
        'description': 'Entry-level Java developer for enterprise applications.',
        'requirements': 'Java, Spring Boot, MySQL, 1-2 years experience',
        'location': 'Pune',
        'experience_required': 1,
        'employment_type': 'Full-time'
    }
]

def create_sample_jobs():
    """Create sample job postings"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get or create a client
        cursor.execute("SELECT client_id FROM clients LIMIT 1")
        client = cursor.fetchone()
        
        if not client:
            # Create a sample client
            cursor.execute("""
                INSERT INTO clients (client_id, client_name, company_name, password_hash, email, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                'DEMO001',
                'Demo Client',
                'Tech Solutions Inc',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInG2',
                'demo@company.com',
                'active'
            ))
            client_id = cursor.fetchone()[0]
        else:
            client_id = client[0]
        
        # Insert sample jobs
        inserted = 0
        for job in SAMPLE_JOBS:
            try:
                cursor.execute("""
                    INSERT INTO jobs (
                        client_id, title, description, requirements, location,
                        department, experience_level, employment_type, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f'CLIENT{client_id}',
                    job['title'],
                    job['description'],
                    job['requirements'],
                    job['location'],
                    'Engineering',  # department field
                    f"{job['experience_required']}+ years",  # experience_level field
                    job['employment_type'],
                    'active'
                ))
                inserted += 1
            except Exception as e:
                print(f"Error inserting job {job['title']}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Successfully created {inserted} sample jobs")
        return inserted
        
    except Exception as e:
        print(f"Error creating jobs: {e}")
        return 0

def verify_jobs():
    """Verify created jobs"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM jobs")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, title, location, experience_level FROM jobs LIMIT 5")
        samples = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"\nJob verification:")
        print(f"Total jobs: {count}")
        print(f"Sample jobs:")
        for job_id, title, location, exp in samples:
            print(f"  - Job {job_id}: {title} in {location} ({exp}+ years)")
        
        return count
        
    except Exception as e:
        print(f"Error verifying jobs: {e}")
        return 0

if __name__ == "__main__":
    print("Creating sample job postings...")
    inserted = create_sample_jobs()
    
    if inserted > 0:
        verify_jobs()
        print(f"\nSuccess! {inserted} jobs created.")
        print("\nNext: Test AI matching with:")
        print('curl -X POST "http://localhost:9000/match" -H "Content-Type: application/json" -d \'{"job_id": 1}\'')
    else:
        print("Failed to create jobs")