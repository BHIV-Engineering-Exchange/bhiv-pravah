import os
import pandas as pd
import requests
import json
from pathlib import Path
import hashlib
from datetime import datetime

class DatabaseSyncManager:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.api_key = "myverysecureapikey123"
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        self.resume_folder = "resume"
        self.csv_file = "data/candidates.csv"
        
    def get_resume_files(self):
        """Get all resume files from folder"""
        if not os.path.exists(self.resume_folder):
            return set()
        
        resume_files = set()
        for file_path in Path(self.resume_folder).iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx', '.doc', '.txt']:
                resume_files.add(file_path.name)
        return resume_files
    
    def get_csv_candidates(self):
        """Get candidates from CSV"""
        if not os.path.exists(self.csv_file):
            return pd.DataFrame()
        return pd.read_csv(self.csv_file)
    
    def get_database_candidates(self):
        """Get all candidates from database"""
        try:
            response = requests.get(f"{self.api_base}/v1/candidates/search", headers=self.headers)
            if response.status_code == 200:
                return response.json().get('candidates', [])
        except:
            pass
        return []
    
    def clean_database(self):
        """Remove candidates from database that don't have corresponding resume files"""
        print("Cleaning database...")
        
        resume_files = self.get_resume_files()
        db_candidates = self.get_database_candidates()
        
        if not resume_files:
            print("No resume files found - skipping cleanup")
            return
        
        removed_count = 0
        for candidate in db_candidates:
            # Check if candidate has corresponding resume file
            candidate_resume = candidate.get('resume_name', '')
            if candidate_resume and candidate_resume not in resume_files:
                try:
                    # Delete candidate from database
                    delete_url = f"{self.api_base}/v1/candidates/{candidate['id']}"
                    response = requests.delete(delete_url, headers=self.headers)
                    if response.status_code == 200:
                        removed_count += 1
                        print(f"  Removed: {candidate['name']} (no resume file: {candidate_resume})")
                except:
                    pass
        
        print(f"Database cleanup complete - removed {removed_count} orphaned candidates")
    
    def clean_csv(self):
        """Remove candidates from CSV that don't have corresponding resume files"""
        print("Cleaning CSV...")
        
        resume_files = self.get_resume_files()
        df = self.get_csv_candidates()
        
        if df.empty:
            print("No CSV data found")
            return
        
        initial_count = len(df)
        df_clean = df[df['resume_name'].isin(resume_files)]
        removed_count = initial_count - len(df_clean)
        
        if removed_count > 0:
            df_clean.to_csv(self.csv_file, index=False)
            print(f"CSV cleanup complete - removed {removed_count} entries without resume files")
        else:
            print("CSV is already clean")
    
    def sync_new_resumes(self):
        """Process and sync new resume files"""
        print("Syncing new resumes...")
        
        resume_files = self.get_resume_files()
        df = self.get_csv_candidates()
        
        if df.empty:
            existing_resumes = set()
        else:
            existing_resumes = set(df['resume_name'].tolist())
        
        new_resumes = resume_files - existing_resumes
        
        if not new_resumes:
            print("No new resumes to process")
            return
        
        print(f"Found {len(new_resumes)} new resume files:")
        for resume in sorted(new_resumes):
            print(f"  - {resume}")
        
        # Process new resumes
        from comprehensive_resume_extractor import ComprehensiveResumeExtractor
        extractor = ComprehensiveResumeExtractor()
        
        # Process only new files
        new_candidates = []
        for file_path in Path(self.resume_folder).iterdir():
            if file_path.name in new_resumes:
                print(f"Processing: {file_path.name}")
                text = extractor.extract_text_content(file_path)
                if text.strip():
                    candidate_data = extractor.deep_content_analysis(text, file_path.name)
                    new_candidates.append(candidate_data)
        
        if new_candidates:
            # Append to existing CSV
            new_df = pd.DataFrame(new_candidates)
            if not df.empty:
                df = pd.concat([df, new_df], ignore_index=True)
            else:
                df = new_df
            
            df.to_csv(self.csv_file, index=False)
            print(f"Added {len(new_candidates)} new candidates to CSV")
            
            # Upload to database
            self.upload_candidates_to_db(new_candidates)
        
    def upload_candidates_to_db(self, candidates):
        """Upload candidates to database"""
        print("Uploading to database...")
        
        db_candidates = []
        for candidate in candidates:
            # Convert experience to years
            exp_years = 0
            if candidate.get('experience'):
                exp_str = str(candidate['experience']).lower()
                if 'year' in exp_str:
                    try:
                        exp_years = int(''.join(filter(str.isdigit, exp_str)))
                    except:
                        exp_years = 0
                elif exp_str == 'fresher':
                    exp_years = 0
            
            db_candidate = {
                "name": candidate.get('name', 'Unknown'),
                "email": candidate.get('email', ''),
                "phone": candidate.get('phone', ''),
                "location": candidate.get('location', ''),
                "experience_years": exp_years,
                "technical_skills": candidate.get('skills', ''),
                "seniority_level": "Entry-level" if exp_years == 0 else ("Senior" if exp_years >= 3 else "Junior"),
                "education_level": candidate.get('education', ''),
                "designation": candidate.get('designation', ''),
                "status": "applied"
            }
            db_candidates.append(db_candidate)
        
        # Upload in batches
        batch_size = 10
        total_uploaded = 0
        
        for i in range(0, len(db_candidates), batch_size):
            batch = db_candidates[i:i+batch_size]
            try:
                response = requests.post(
                    f"{self.api_base}/v1/candidates/bulk",
                    headers=self.headers,
                    json={"candidates": batch},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    uploaded = result.get('count', 0)
                    total_uploaded += uploaded
                    print(f"  Batch {i//batch_size + 1}: Uploaded {uploaded} candidates")
            except Exception as e:
                print(f"  Batch {i//batch_size + 1}: Error - {str(e)}")
        
        print(f"Uploaded {total_uploaded} new candidates to global pool (no job_id pre-allocation)")
    
    def full_sync(self):
        """Perform complete database synchronization"""
        print("Starting Full Database Synchronization")
        print("=" * 50)
        
        # Step 1: Clean database
        self.clean_database()
        
        # Step 2: Clean CSV
        self.clean_csv()
        
        # Step 3: Sync new resumes
        self.sync_new_resumes()
        
        # Step 4: Verify sync
        self.verify_sync()
        
        print("=" * 50)
        print("Full synchronization complete!")
    
    def verify_sync(self):
        """Verify synchronization status"""
        print("Verifying synchronization...")
        
        resume_files = self.get_resume_files()
        df = self.get_csv_candidates()
        db_candidates = self.get_database_candidates()
        
        print(f"Resume files: {len(resume_files)}")
        print(f"CSV candidates: {len(df)}")
        print(f"Database candidates: {len(db_candidates)}")
        
        # Check for mismatches
        if not df.empty:
            csv_resumes = set(df['resume_name'].tolist())
            missing_in_csv = resume_files - csv_resumes
            extra_in_csv = csv_resumes - resume_files
            
            if missing_in_csv:
                print(f"Missing in CSV: {missing_in_csv}")
            if extra_in_csv:
                print(f"Extra in CSV: {extra_in_csv}")
            
            if not missing_in_csv and not extra_in_csv:
                print("CSV and resume folder are in sync")
        
        print("Verification complete")

def main():
    sync_manager = DatabaseSyncManager()
    sync_manager.full_sync()

if __name__ == "__main__":
    main()
