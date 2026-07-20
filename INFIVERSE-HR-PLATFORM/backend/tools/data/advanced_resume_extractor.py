#!/usr/bin/env python3
"""
Advanced Resume Extractor for BHIV HR Platform
Enhanced with AI-powered extraction, validation, and database compatibility
Version: 2.0.0 - Production Ready
"""

import os
import pandas as pd
import PyPDF2
import docx
import re
import spacy
import nltk
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except:
    pass

# Try to load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

@dataclass
class CandidateProfile:
    """Structured candidate profile matching database schema"""
    name: str
    email: str
    phone: str
    location: str
    seniority_level: str
    technical_skills: str
    experience_years: int
    education_level: str
    resume_path: str
    confidence_score: float = 0.0

class AdvancedResumeExtractor:
    """Advanced resume extractor with AI-powered analysis"""
    
    def __init__(self, resume_folder="assets/resumes", output_csv="data/candidates.csv"):
        self.resume_folder = resume_folder
        self.output_csv = output_csv
        self.setup_logging()
        
        # Enhanced skill databases
        self.skill_categories = {
            'programming': [
                'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'C', 'PHP', 'Ruby',
                'Go', 'Rust', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl', 'Shell'
            ],
            'web_frontend': [
                'React', 'Angular', 'Vue.js', 'HTML5', 'CSS3', 'SASS', 'Bootstrap', 
                'jQuery', 'Next.js'
            ],
            'web_backend': [
                'Node.js', 'Express.js', 'Django', 'Flask', 'FastAPI', 'Spring Boot',
                'ASP.NET', 'Laravel'
            ],
            'databases': [
                'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQL Server', 'SQLite'
            ],
            'cloud_devops': [
                'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub'
            ],
            'data_ai': [
                'Machine Learning', 'Deep Learning', 'AI', 'Data Science', 'Pandas', 'NumPy',
                'TensorFlow', 'PyTorch', 'Scikit-learn', 'Tableau'
            ]
        }
        
        # Enhanced location database
        self.locations = {
            'indian_metros': ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune'],
            'indian_tier2': ['Ahmedabad', 'Jaipur', 'Surat', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Nashik'],
            'international': ['New York', 'San Francisco', 'London', 'Toronto', 'Sydney', 'Singapore', 'Dubai']
        }
        
    def setup_logging(self):
        """Setup logging for extraction process"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/resume_extraction.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def scan_resume_folder(self) -> List[Path]:
        """Scan and identify all resume files with validation"""
        if not os.path.exists(self.resume_folder):
            self.logger.error(f"Resume folder not found: {self.resume_folder}")
            return []
        
        resume_files = []
        supported_extensions = ['.pdf', '.docx', '.doc', '.txt']
        
        for file_path in Path(self.resume_folder).iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                resume_files.append(file_path)
        
        return sorted(resume_files)
    
    def _clean_text(self, text: str) -> str:
        """Clean text to remove problematic characters"""
        # Remove or replace problematic unicode characters
        text = re.sub(r'[^\w\s@.+()-]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_text_with_metadata(self, file_path: Path) -> Tuple[str, Dict]:
        """Extract text content with metadata"""
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._extract_pdf_text(file_path), {}
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                return self._extract_docx_text(file_path), {}
            elif file_path.suffix.lower() == '.txt':
                return self._extract_txt_text(file_path), {}
            else:
                return "", {}
        except Exception as e:
            self.logger.error(f"Error extracting {file_path.name}: {e}")
            return "", {}
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF"""
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
            self.logger.error(f"PDF extraction failed for {file_path.name}: {e}")
            return ""
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            self.logger.error(f"DOCX extraction failed for {file_path.name}: {e}")
            return ""
    
    def _extract_txt_text(self, file_path: Path) -> str:
        """Extract text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            self.logger.error(f"TXT extraction failed for {file_path.name}: {e}")
            return ""
    
    def analyze_with_ai(self, text: str, file_path: Path) -> CandidateProfile:
        """AI-powered analysis of resume text"""
        # Clean text to remove problematic characters
        text = self._clean_text(text)
        
        profile = CandidateProfile(
            name="Unknown",
            email="",
            phone="",
            location="",
            seniority_level="Junior",
            technical_skills="",
            experience_years=0,
            education_level="Bachelors",
            resume_path=f"assets/resumes/{file_path.name}",
            confidence_score=0.0
        )
        
        try:
            profile.name = self._extract_name_ai(text, file_path.name)
            profile.email = self._extract_email_ai(text)
            profile.phone = self._extract_phone_ai(text)
            profile.location = self._extract_location_ai(text)
            profile.technical_skills = self._extract_skills_ai(text)
            profile.experience_years = self._extract_experience_ai(text)
            profile.education_level = self._extract_education_ai(text)
            profile.seniority_level = self._determine_seniority(profile.experience_years)
            profile.confidence_score = self._calculate_confidence(profile)
            
            return profile
        except Exception as e:
            self.logger.error(f"AI analysis failed for {file_path.name}: {e}")
            return profile
    
    def _extract_name_ai(self, text: str, filename: str) -> str:
        """Extract name using AI and patterns"""
        # First try filename - often most reliable
        name_from_file = Path(filename).stem
        name_from_file = re.sub(r'[_-]', ' ', name_from_file)
        name_from_file = re.sub(r'(?i)(resume|cv|document)', '', name_from_file)
        name_from_file = re.sub(r'[^A-Za-z\s]', '', name_from_file).strip()
        
        # If filename gives good name, use it
        if (len(name_from_file) > 2 and len(name_from_file.split()) >= 2 and 
            len(name_from_file.split()) <= 4 and len(name_from_file) < 50):
            return ' '.join(word.capitalize() for word in name_from_file.split())
        
        # Clean text for better processing
        text = re.sub(r'[^\w\s@.-]', ' ', text)
        
        # Use spaCy if available - with better filtering
        if nlp:
            doc = nlp(text[:1000])
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    # Strict filtering for person names
                    if (2 <= len(name.split()) <= 3 and len(name) < 40 and 
                        all(word.isalpha() for word in name.split()) and
                        not any(word in name.lower() for word in ['email', 'phone', 'address', 'skills', 'experience', 'education', 'work', 'project'])):
                        return name.title()
        
        # Pattern matching - very strict
        lines = [line.strip() for line in text.split('\n')[:10] if line.strip()]
        for line in lines:
            # Skip lines with keywords or symbols
            if (any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', 'contact', 'email', 'phone', 'address', 'objective', 'summary', 'education', 'experience', 'skills', 'project', 'work', 'linkedin', 'github']) or
                any(char in line for char in ['@', 'http', 'www', '+91', ':', '|'])):
                continue
            
            # Look for clean name pattern
            if 10 <= len(line) <= 40:
                words = line.split()
                if (2 <= len(words) <= 3 and 
                    all(len(word) > 1 and word.isalpha() for word in words)):
                    return ' '.join(word.capitalize() for word in words)
        
        # If filename has single word, try to use it
        if len(name_from_file) > 2:
            return name_from_file.capitalize()
        
        return "Unknown"
    
    def _extract_email_ai(self, text: str) -> str:
        """Extract email using regex patterns"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0].lower() if emails else ""
    
    def _extract_phone_ai(self, text: str) -> str:
        """Extract phone using comprehensive patterns"""
        patterns = [
            r'\+91[-\s]?\d{10}',
            r'\b\d{10}\b',
            r'\+\d{1,3}[-\s]?\d{10,14}'
        ]
        
        for pattern in patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0]
        return ""
    
    def _extract_location_ai(self, text: str) -> str:
        """Extract location using city database"""
        all_locations = []
        for locations in self.locations.values():
            all_locations.extend(locations)
        
        for location in all_locations:
            if location.lower() in text.lower():
                return location
        return "Mumbai"
    
    def _extract_skills_ai(self, text: str) -> str:
        """Extract skills using comprehensive database"""
        found_skills = []
        text_lower = text.lower()
        
        for category, skills in self.skill_categories.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills.append(skill)
        
        return ', '.join(found_skills[:10])
    
    def _extract_experience_ai(self, text: str) -> int:
        """Extract experience years using patterns"""
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'experience\s*:?\s*(\d+)\+?\s*years?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return int(matches[0])
        
        if any(word in text.lower() for word in ['fresher', 'fresh graduate', 'entry level']):
            return 0
        
        return 1
    
    def _extract_education_ai(self, text: str) -> str:
        """Extract education level"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['phd', 'ph.d', 'doctorate']):
            return 'PhD'
        elif any(word in text_lower for word in ['master', 'mba', 'm.tech', 'ms']):
            return 'Masters'
        elif any(word in text_lower for word in ['bachelor', 'b.tech', 'be', 'bs']):
            return 'Bachelors'
        elif any(word in text_lower for word in ['diploma', 'polytechnic']):
            return 'Diploma'
        else:
            return 'Bachelors'
    
    def _determine_seniority(self, experience_years: int) -> str:
        """Determine seniority level based on experience"""
        if experience_years <= 2:
            return 'Junior'
        elif experience_years <= 5:
            return 'Mid'
        else:
            return 'Senior'
    
    def _calculate_confidence(self, profile: CandidateProfile) -> float:
        """Calculate extraction confidence score"""
        score = 0.0
        
        if profile.name != "Unknown":
            score += 0.2
        if profile.email and '@' in profile.email:
            score += 0.2
        if profile.phone:
            score += 0.15
        if profile.technical_skills:
            score += 0.25
        if profile.experience_years >= 0:
            score += 0.1
        if profile.education_level:
            score += 0.1
        
        return min(score, 1.0)
    
    def process_all_resumes(self) -> pd.DataFrame:
        """Process all resume files with AI analysis"""
        resume_files = self.scan_resume_folder()
        
        if not resume_files:
            self.logger.error("No resume files found!")
            return pd.DataFrame()
        
        self.logger.info(f"Processing {len(resume_files)} resume files...")
        
        candidates = []
        
        for i, file_path in enumerate(resume_files, 1):
            self.logger.info(f"[{i}/{len(resume_files)}] Processing: {file_path.name}")
            
            text, metadata = self.extract_text_with_metadata(file_path)
            
            if not text.strip():
                self.logger.warning(f"No text extracted from {file_path.name}")
                continue
            
            profile = self.analyze_with_ai(text, file_path)
            
            candidate_data = {
                'name': profile.name,
                'email': profile.email,
                'phone': profile.phone,
                'location': profile.location,
                'seniority_level': profile.seniority_level,
                'technical_skills': profile.technical_skills,
                'experience_years': profile.experience_years,
                'education_level': profile.education_level,
                'resume_path': profile.resume_path
            }
            
            candidates.append(candidate_data)
            
            # Clean name for logging to avoid unicode issues
            clean_name = re.sub(r'[^\w\s-]', '', profile.name)
            self.logger.info(f"  Extracted: {clean_name} ({profile.confidence_score:.2f} confidence)")
        
        df = pd.DataFrame(candidates)
        
        os.makedirs(os.path.dirname(self.output_csv), exist_ok=True)
        df.to_csv(self.output_csv, index=False)
        
        self.logger.info(f"Processed {len(candidates)} candidates")
        self.logger.info(f"Output saved to: {self.output_csv}")
        
        return df

def main():
    """Main execution function"""
    print("BHIV HR Platform - Advanced Resume Extractor")
    print("=" * 50)
    
    extractor = AdvancedResumeExtractor(
        resume_folder="assets/resumes",
        output_csv="data/candidates.csv"
    )
    
    df = extractor.process_all_resumes()
    
    if not df.empty:
        print(f"\nSuccessfully processed {len(df)} candidates")
        print(f"Output: data/candidates.csv")
        
        print("\nSample candidates:")
        for _, row in df.head(3).iterrows():
            skills_preview = str(row.get('technical_skills', ''))[:30] + "..." if len(str(row.get('technical_skills', ''))) > 30 else str(row.get('technical_skills', ''))
            print(f"  - {row['name']} | {skills_preview} | {row['seniority_level']}")
    else:
        print("No candidates processed")

if __name__ == "__main__":
    main()