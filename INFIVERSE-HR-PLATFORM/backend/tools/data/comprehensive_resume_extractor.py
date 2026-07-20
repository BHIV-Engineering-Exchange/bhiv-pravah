import os
import pandas as pd
import PyPDF2
import docx
import re
from pathlib import Path

class ComprehensiveResumeExtractor:
    def __init__(self, resume_folder="assets/resumes", output_csv="data/candidates.csv"):
        self.resume_folder = resume_folder
        self.output_csv = output_csv
        
    def scan_resume_folder(self):
        """Scan and identify all resume files"""
        if not os.path.exists(self.resume_folder):
            print(f"Resume folder not found: {self.resume_folder}")
            return []
        
        resume_files = []
        supported_extensions = ['.pdf', '.docx', '.doc', '.txt']
        
        for file_path in Path(self.resume_folder).iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                resume_files.append(file_path)
        
        return sorted(resume_files)
    
    def extract_text_content(self, file_path):
        """Extract text content from different file types"""
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._extract_pdf_text(file_path)
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                return self._extract_docx_text(file_path)
            elif file_path.suffix.lower() == '.txt':
                return self._extract_txt_text(file_path)
        except Exception as e:
            print(f"  Error extracting text: {e}")
            return ""
        return ""
    
    def _extract_pdf_text(self, file_path):
        """Extract text from PDF with error handling"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    try:
                        text += page.extract_text() + "\n"
                    except:
                        continue
                return text
        except Exception as e:
            print(f"  PDF error: {e}")
            return ""
    
    def _extract_docx_text(self, file_path):
        """Extract text from DOCX"""
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    
    def _extract_txt_text(self, file_path):
        """Extract text from TXT"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    
    def deep_content_analysis(self, text, filename):
        """Perform deep analysis of file content"""
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text_lower = text.lower()
        
        # Extract all fields through content analysis
        name = self._analyze_name(text, filename)
        email = self._analyze_email(text)
        phone = self._analyze_phone(text)
        location = self._analyze_location(text)
        designation = self._analyze_designation(text)
        skills = self._analyze_skills(text)
        experience = self._analyze_experience(text)
        education = self._analyze_education(text)
        
        # Convert experience to years
        exp_years = 0
        if 'year' in experience.lower():
            try:
                exp_years = int(experience.split()[0])
            except:
                exp_years = 0
        elif experience == 'Fresher':
            exp_years = 0
        else:
            exp_years = 1
        
        # Map designation to seniority_level
        seniority_level = 'Junior'
        if exp_years <= 2:
            seniority_level = 'Junior'
        elif exp_years <= 5:
            seniority_level = 'Mid'
        else:
            seniority_level = 'Senior'
        
        return {
            'name': name,
            'email': email,
            'phone': phone,
            'location': location,
            'seniority_level': seniority_level,  # FIXED: was 'designation'
            'technical_skills': skills,  # FIXED: was 'skills'
            'experience_years': exp_years,  # FIXED: was 'experience'
            'education_level': education,  # FIXED: was 'education'
            'resume_path': f"assets/resumes/{filename}"  # FIXED: was 'resume_name'
        }
    
    def _analyze_name(self, text, filename):
        """Deep name analysis"""
        # Method 1: Clean filename
        name_from_file = Path(filename).stem
        name_from_file = re.sub(r'[_-]', ' ', name_from_file)
        name_from_file = re.sub(r'(?i)(resume|cv|curriculum|vitae)', '', name_from_file)
        name_from_file = re.sub(r'\(\d+\)', '', name_from_file)
        name_from_file = re.sub(r'[^\w\s]', '', name_from_file).strip()
        
        # Method 2: Extract from text patterns
        lines = [line.strip() for line in text.split('\n')[:10] if line.strip()]
        
        # Look for name patterns in first lines
        for line in lines:
            # Skip headers and common resume words
            if any(word in line.lower() for word in ['resume', 'curriculum', 'contact', 'email', 'phone', 'address']):
                continue
            
            # Name pattern: 2-4 words, mostly alphabetic, reasonable length
            words = line.split()
            if 2 <= len(words) <= 4 and len(line) < 50:
                if all(len(word) > 1 and word.replace('.', '').isalpha() for word in words):
                    return ' '.join(word.capitalize() for word in words)
        
        # Method 3: Use cleaned filename if valid
        if len(name_from_file) > 2 and not name_from_file.isdigit():
            return ' '.join(word.capitalize() for word in name_from_file.split())
        
        return "Unknown"
    
    def _analyze_email(self, text):
        """Deep email analysis"""
        # Multiple email patterns
        patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
        ]
        
        for pattern in patterns:
            emails = re.findall(pattern, text)
            for email in emails:
                # Validate email format
                if '@' in email and '.' in email.split('@')[1]:
                    return email.lower()
        return ""
    
    def _analyze_phone(self, text):
        """Deep phone analysis"""
        # Comprehensive phone patterns
        patterns = [
            r'\+91[-\s]?\d{10}',
            r'\+91[-\s]?\d{5}[-\s]?\d{5}',
            r'91[-\s]?\d{10}',
            r'\+\d{1,3}[-\s]?\d{10,14}',
            r'\b\d{10}\b',
            r'\(\d{3}\)[-\s]?\d{3}[-\s]?\d{4}'
        ]
        
        for pattern in patterns:
            phones = re.findall(pattern, text)
            for phone in phones:
                # Clean and validate
                clean_phone = re.sub(r'[-\s()]', '', phone)
                if 10 <= len(clean_phone) <= 15:
                    return phone
        return ""
    
    def _analyze_location(self, text):
        """Deep location analysis"""
        # Comprehensive city lists
        indian_cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune',
            'Ahmedabad', 'Jaipur', 'Surat', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore',
            'Thane', 'Bhopal', 'Visakhapatnam', 'Patna', 'Vadodara', 'Ghaziabad',
            'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut', 'Rajkot', 'Kalyan'
        ]
        
        international_cities = [
            'New York', 'San Francisco', 'Los Angeles', 'Chicago', 'Boston', 'Seattle',
            'Austin', 'Denver', 'London', 'Toronto', 'Sydney', 'Singapore', 'Dubai'
        ]
        
        all_cities = indian_cities + international_cities
        
        # Check for exact city matches
        for city in all_cities:
            if city.lower() in text.lower():
                return city
        
        # Look for address patterns
        address_patterns = [
            r'([A-Z][a-z]+,\s*[A-Z]{2,3})',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+,\s*[A-Z]{2})'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return ""
    
    def _analyze_designation(self, text):
        """Deep designation analysis"""
        # Comprehensive job titles
        designations = [
            'Senior Software Engineer', 'Lead Software Engineer', 'Principal Software Engineer',
            'Software Engineer', 'Software Developer', 'Full Stack Developer',
            'Frontend Developer', 'Backend Developer', 'Web Developer',
            'Senior Data Scientist', 'Data Scientist', 'Data Analyst', 'Business Analyst',
            'Machine Learning Engineer', 'AI Engineer', 'DevOps Engineer', 'Cloud Engineer',
            'Product Manager', 'Senior Product Manager', 'Project Manager', 'Program Manager',
            'Technical Lead', 'Team Lead', 'Engineering Manager', 'Development Manager',
            'System Administrator', 'Database Administrator', 'Network Administrator',
            'Quality Assurance Engineer', 'Test Engineer', 'Automation Engineer'
        ]
        
        text_lower = text.lower()
        
        # Look for exact designation matches
        for designation in designations:
            if designation.lower() in text_lower:
                return designation
        
        # Fallback to generic titles
        if 'software engineer' in text_lower:
            return 'Software Engineer'
        elif 'developer' in text_lower:
            return 'Software Developer'
        elif 'data scientist' in text_lower:
            return 'Data Scientist'
        elif 'data analyst' in text_lower:
            return 'Data Analyst'
        elif 'product manager' in text_lower:
            return 'Product Manager'
        elif 'project manager' in text_lower:
            return 'Project Manager'
        
        return ""
    
    def _analyze_skills(self, text):
        """Deep skills analysis"""
        # Comprehensive skills database
        programming_languages = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'C', 'PHP', 'Ruby',
            'Go', 'Rust', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl', 'Shell'
        ]
        
        web_technologies = [
            'React', 'Angular', 'Vue', 'Node.js', 'Express', 'Django', 'Flask', 'Spring Boot',
            'HTML', 'CSS', 'SASS', 'Bootstrap', 'jQuery', 'REST API', 'GraphQL'
        ]
        
        databases = [
            'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Oracle', 'Redis', 'Cassandra',
            'SQLite', 'MariaDB', 'DynamoDB', 'Neo4j', 'InfluxDB'
        ]
        
        cloud_devops = [
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub',
            'GitLab', 'Terraform', 'Ansible', 'Chef', 'Puppet', 'CI/CD'
        ]
        
        data_ai = [
            'Machine Learning', 'Deep Learning', 'AI', 'Data Science', 'Pandas', 'NumPy',
            'TensorFlow', 'PyTorch', 'Scikit-learn', 'Tableau', 'Power BI', 'Spark', 'Hadoop'
        ]
        
        all_skills = programming_languages + web_technologies + databases + cloud_devops + data_ai
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in all_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return ', '.join(found_skills[:12])  # Limit to 12 skills
    
    def _analyze_experience(self, text):
        """Deep experience analysis"""
        # Experience patterns
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'experience\s*:?\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\s*years?\s*(?:in|of)\s*(?:software|development|programming)'
        ]
        
        for pattern in exp_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                years = int(matches[0])
                return f"{years} years" if years > 0 else "Fresher"
        
        # Check for fresher indicators
        fresher_keywords = ['fresher', 'fresh graduate', 'recent graduate', 'entry level', 'new graduate']
        text_lower = text.lower()
        
        for keyword in fresher_keywords:
            if keyword in text_lower:
                return "Fresher"
        
        # Estimate from years in text
        current_year = 2024
        years = re.findall(r'\b(20\d{2})\b', text)
        if years:
            years = [int(y) for y in years if 2010 <= int(y) <= current_year]
            if years:
                grad_year = max(years)
                exp_years = current_year - grad_year
                if exp_years <= 1:
                    return "Fresher"
                elif exp_years <= 20:
                    return f"{exp_years} years"
        
        return "Not Specified"
    
    def _analyze_education(self, text):
        """Deep education analysis"""
        text_lower = text.lower()
        
        # PhD patterns
        if any(pattern in text_lower for pattern in ['phd', 'ph.d', 'doctorate', 'doctoral degree']):
            return 'PhD'
        
        # Masters patterns
        elif any(pattern in text_lower for pattern in ['master', 'masters', 'mba', 'm.tech', 'mtech', 'm.s', 'ms', 'm.a', 'ma', 'post graduate']):
            return 'Masters'
        
        # Bachelors patterns
        elif any(pattern in text_lower for pattern in ['bachelor', 'bachelors', 'b.tech', 'btech', 'be', 'b.e', 'b.s', 'bs', 'b.a', 'ba', 'b.com', 'bcom']):
            return 'Bachelors'
        
        # Diploma patterns
        elif any(pattern in text_lower for pattern in ['diploma', 'polytechnic', 'associate degree']):
            return 'Diploma'
        
        # 12th patterns
        elif any(pattern in text_lower for pattern in ['12th', 'higher secondary', 'intermediate', 'hsc', '+2']):
            return '12th'
        
        # Default for professional resumes
        else:
            return 'Bachelors'
    
    def process_all_resumes(self):
        """Process all resume files comprehensively"""
        resume_files = self.scan_resume_folder()
        
        if not resume_files:
            print("No resume files found!")
            return None
        
        print(f"Comprehensive Resume Processing")
        print("=" * 60)
        print(f"Found {len(resume_files)} files to process")
        
        candidates = []
        
        for i, file_path in enumerate(resume_files, 1):
            filename = file_path.name
            print(f"\n[{i}/{len(resume_files)}] Processing: {filename}")
            print(f"  Type: {file_path.suffix.upper()}")
            print(f"  Size: {file_path.stat().st_size} bytes")
            
            # Extract text content
            text = self.extract_text_content(file_path)
            if not text.strip():
                print("  - No text content extracted")
                continue
            
            print(f"  Text: {len(text)} characters")
            
            # Perform deep content analysis
            candidate_data = self.deep_content_analysis(text, filename)
            candidates.append(candidate_data)
            
            # Show extracted information
            print(f"  Name: {candidate_data['name']}")
            print(f"  Email: {candidate_data['email'] or 'Not found'}")
            print(f"  Phone: {candidate_data['phone'] or 'Not found'}")
            print(f"  Location: {candidate_data['location'] or 'Not found'}")
            print(f"  Seniority: {candidate_data['seniority_level']}")
            print(f"  Experience: {candidate_data['experience_years']} years")
            print(f"  Education: {candidate_data['education_level']}")
            print(f"  Skills: {candidate_data['technical_skills'][:60]}{'...' if len(candidate_data['technical_skills']) > 60 else ''}")
        
        if candidates:
            # Save results
            os.makedirs(os.path.dirname(self.output_csv), exist_ok=True)
            df = pd.DataFrame(candidates)
            df.to_csv(self.output_csv, index=False)
            
            print(f"\n" + "=" * 60)
            print(f"COMPREHENSIVE PROCESSING COMPLETE")
            print(f"Total candidates processed: {len(candidates)}")
            print(f"Output saved to: {self.output_csv}")
            
            # Detailed statistics
            print(f"\nExtraction Statistics:")
            print(f"Names: {len(df)} (100%)")
            print(f"Emails: {df['email'].astype(bool).sum()} ({df['email'].astype(bool).sum()/len(df)*100:.0f}%)")
            print(f"Phones: {df['phone'].astype(bool).sum()} ({df['phone'].astype(bool).sum()/len(df)*100:.0f}%)")
            print(f"Locations: {df['location'].astype(bool).sum()} ({df['location'].astype(bool).sum()/len(df)*100:.0f}%)")
            print(f"Seniority Levels: {df['seniority_level'].astype(bool).sum()} ({df['seniority_level'].astype(bool).sum()/len(df)*100:.0f}%)")
            
            return df
        
        print("No files processed successfully")
        return None

def main():
    extractor = ComprehensiveResumeExtractor()
    result = extractor.process_all_resumes()
    
    if result is not None:
        print("\nAuto-syncing to database for real-time portal updates...")
        try:
            from database_sync_manager import DatabaseSyncManager
            sync_manager = DatabaseSyncManager()
            sync_manager.upload_candidates_to_db(result.to_dict('records'))
            print("✅ Data successfully synced to database!")
            print("Both HR Portal (8501) and Client Portal (8502) now have real-time data")
        except Exception as e:
            print(f"Auto-sync error: {e}")
            print("Run: python tools/database_sync_manager.py")

if __name__ == "__main__":
    main()
