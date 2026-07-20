#!/usr/bin/env python3
"""
Load candidate data from CSV into local Docker database
"""

import pandas as pd
import psycopg2
import os
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bhiv_hr',
    'user': 'bhiv_user',
    'password': 'bhiv_local_password_2025'
}

def load_candidates_from_csv():
    """Load candidates from CSV file into database"""
    try:
        # Read CSV data
        df = pd.read_csv('data/candidates.csv')
        print(f"Found {len(df)} candidates in CSV")
        print(f"Found {len(df)} candidates in CSV")
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Insert candidates
        inserted = 0
        for _, row in df.iterrows():
            try:
                # Map experience to years - FIXED FIELD NAME
                exp_years = 0
                if 'experience_years' in row and pd.notna(row['experience_years']):
                    exp_years = int(row['experience_years'])
                else:
                    exp_years = 0
                
                # Insert candidate
                cursor.execute("""
                    INSERT INTO candidates (
                        name, email, phone, location, experience_years, 
                        technical_skills, seniority_level, education_level, 
                        resume_path, status, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                """, (
                    row['name'],
                    row['email'] if pd.notna(row['email']) else f"{row['name'].lower().replace(' ', '')}@example.com",
                    row['phone'] if pd.notna(row['phone']) else '',
                    row['location'] if pd.notna(row['location']) else 'Mumbai',
                    exp_years,
                    row['technical_skills'] if pd.notna(row['technical_skills']) else '',  # FIXED
                    row['seniority_level'] if pd.notna(row['seniority_level']) else 'Junior',  # FIXED
                    row['education_level'] if pd.notna(row['education_level']) else 'Bachelors',  # FIXED
                    row['resume_path'] if pd.notna(row['resume_path']) else '',  # FIXED
                    'applied',
                    datetime.now(),
                    datetime.now()
                ))
                inserted += 1
            except Exception as e:
                print(f"Error inserting {row['name']}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Successfully inserted {inserted} candidates")
        return inserted
        
    except Exception as e:
        print(f"Error loading candidates: {e}")
        return 0

def verify_data():
    """Verify the loaded data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM candidates")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT name, email, technical_skills FROM candidates LIMIT 5")
        samples = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"\nDatabase verification:")
        print(f"Total candidates: {count}")
        print(f"Sample candidates:")
        for name, email, skills in samples:
            print(f"  - {name} ({email}) - {skills[:50]}...")
        
        return count
        
    except Exception as e:
        print(f"Error verifying data: {e}")
        return 0

if __name__ == "__main__":
    print("Loading candidates into local Docker database...")
    inserted = load_candidates_from_csv()
    
    if inserted > 0:
        verify_data()
        print(f"\nSuccess! {inserted} candidates loaded.")
        print("Now test the Agent service:")
        print('curl -H "Authorization: Bearer <YOUR_API_KEY>" -X POST -H "Content-Type: application/json" -d \'{"job_id": 1}\' http://localhost:9000/match')
    else:
        print("Failed to load candidates")