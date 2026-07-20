#!/usr/bin/env python3
"""
Dynamic Job Creator - Replaces create_demo_jobs.py
Creates jobs dynamically based on real market data and client needs
"""

import requests
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
import os

# API Configuration
API_BASE = os.getenv("GATEWAY_SERVICE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY_SECRET", "myverysecureapikey123")
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

class DynamicJobCreator:
    def __init__(self):
        self.job_templates = self._load_job_templates()
        self.skill_trends = self._load_skill_trends()
        self.market_data = self._load_market_data()
    
    def _load_job_templates(self) -> Dict:
        """Load dynamic job templates based on market trends"""
        return {
            "software_engineer": {
                "base_title": "Software Engineer",
                "levels": ["Junior", "Mid-Level", "Senior", "Lead", "Principal"],
                "departments": ["Engineering", "Product", "Platform"],
                "core_skills": ["Programming", "Problem Solving", "System Design"],
                "trending_skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
                "salary_ranges": {
                    "Junior": "$60k-80k",
                    "Mid-Level": "$80k-120k", 
                    "Senior": "$120k-160k",
                    "Lead": "$160k-200k",
                    "Principal": "$200k-250k"
                }
            },
            "data_scientist": {
                "base_title": "Data Scientist",
                "levels": ["Junior", "Mid-Level", "Senior", "Lead"],
                "departments": ["Data Science", "Analytics", "AI/ML"],
                "core_skills": ["Statistics", "Machine Learning", "Data Analysis"],
                "trending_skills": ["Python", "R", "SQL", "TensorFlow", "PyTorch", "Pandas"],
                "salary_ranges": {
                    "Junior": "$70k-90k",
                    "Mid-Level": "$90k-130k",
                    "Senior": "$130k-170k", 
                    "Lead": "$170k-220k"
                }
            },
            "product_manager": {
                "base_title": "Product Manager",
                "levels": ["Associate", "Mid-Level", "Senior", "Director"],
                "departments": ["Product", "Strategy", "Growth"],
                "core_skills": ["Product Strategy", "User Research", "Analytics"],
                "trending_skills": ["Agile", "Scrum", "SQL", "A/B Testing", "Figma"],
                "salary_ranges": {
                    "Associate": "$80k-100k",
                    "Mid-Level": "$100k-140k",
                    "Senior": "$140k-180k",
                    "Director": "$180k-250k"
                }
            },
            "devops_engineer": {
                "base_title": "DevOps Engineer",
                "levels": ["Junior", "Mid-Level", "Senior", "Lead"],
                "departments": ["Engineering", "Infrastructure", "Platform"],
                "core_skills": ["CI/CD", "Infrastructure", "Automation"],
                "trending_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Jenkins"],
                "salary_ranges": {
                    "Junior": "$65k-85k",
                    "Mid-Level": "$85k-125k",
                    "Senior": "$125k-165k",
                    "Lead": "$165k-210k"
                }
            }
        }
    
    def _load_skill_trends(self) -> Dict:
        """Load current skill trends and demand"""
        return {
            "high_demand": ["Python", "React", "AWS", "Kubernetes", "Machine Learning"],
            "emerging": ["Rust", "Go", "GraphQL", "Serverless", "Edge Computing"],
            "stable": ["Java", "JavaScript", "SQL", "Git", "Linux"],
            "declining": ["jQuery", "PHP", "Flash", "Perl"]
        }
    
    def _load_market_data(self) -> Dict:
        """Load market data for dynamic job creation"""
        return {
            "locations": {
                "high_demand": ["San Francisco", "New York", "Seattle", "Austin"],
                "emerging": ["Denver", "Atlanta", "Portland", "Nashville"],
                "remote_friendly": ["Remote", "Hybrid", "Remote-First"]
            },
            "company_types": ["Startup", "Scale-up", "Enterprise", "Consulting"],
            "work_types": ["Full-time", "Contract", "Part-time", "Internship"]
        }
    
    def create_dynamic_job(self, job_type: str = None, client_id: int = None) -> Dict:
        """Create a single dynamic job based on market trends"""
        if not job_type:
            job_type = random.choice(list(self.job_templates.keys()))
        
        template = self.job_templates[job_type]
        level = random.choice(template["levels"])
        department = random.choice(template["departments"])
        location = random.choice(
            self.market_data["locations"]["high_demand"] + 
            self.market_data["locations"]["remote_friendly"]
        )
        
        # Generate dynamic title
        title = f"{level} {template['base_title']}"
        if random.random() > 0.7:  # 30% chance of specialization
            specializations = {
                "software_engineer": ["Frontend", "Backend", "Full Stack", "Mobile"],
                "data_scientist": ["ML", "Analytics", "Research", "Platform"],
                "product_manager": ["Growth", "Platform", "Mobile", "B2B"],
                "devops_engineer": ["Cloud", "Security", "Platform", "Site Reliability"]
            }
            if job_type in specializations:
                spec = random.choice(specializations[job_type])
                title = f"{level} {spec} {template['base_title']}"
        
        # Generate dynamic skills requirement
        required_skills = template["core_skills"].copy()
        trending_count = random.randint(3, 6)
        required_skills.extend(random.sample(template["trending_skills"], trending_count))
        
        # Add high-demand skills
        if random.random() > 0.5:
            required_skills.extend(random.sample(self.skill_trends["high_demand"], 2))
        
        # Generate dynamic description
        description = self._generate_job_description(title, department, required_skills, level)
        requirements = self._generate_requirements(required_skills, level)
        
        return {
            "title": title,
            "department": department,
            "location": location,
            "experience_level": level,
            "requirements": requirements,
            "description": description,
            "client_id": client_id or random.randint(1, 5),
            "salary_range": template["salary_ranges"].get(level, "Competitive"),
            "employment_type": random.choice(self.market_data["work_types"]),
            "created_dynamically": True,
            "market_trend_score": self._calculate_trend_score(required_skills)
        }
    
    def _generate_job_description(self, title: str, department: str, skills: List[str], level: str) -> str:
        """Generate dynamic job description"""
        company_types = ["innovative", "fast-growing", "leading", "cutting-edge"]
        company_type = random.choice(company_types)
        
        description_templates = [
            f"Join our {company_type} {department} team as a {title}. You'll work on exciting projects that impact millions of users.",
            f"We're looking for a talented {title} to join our {department} team and help build the future of technology.",
            f"As a {title} in our {department} team, you'll have the opportunity to work with cutting-edge technologies and solve complex problems."
        ]
        
        base_description = random.choice(description_templates)
        
        responsibilities = [
            f"Design and implement scalable solutions using {', '.join(skills[:3])}",
            f"Collaborate with cross-functional teams to deliver high-quality products",
            f"Mentor junior team members and contribute to technical decisions",
            f"Stay up-to-date with industry trends and best practices"
        ]
        
        if level in ["Senior", "Lead", "Principal"]:
            responsibilities.extend([
                "Lead technical architecture discussions",
                "Drive technical strategy and roadmap planning"
            ])
        
        return f"{base_description}\n\nKey Responsibilities:\n" + "\n".join(f"• {resp}" for resp in responsibilities)
    
    def _generate_requirements(self, skills: List[str], level: str) -> str:
        """Generate dynamic requirements"""
        experience_years = {
            "Junior": "1-3 years",
            "Associate": "2-4 years", 
            "Mid-Level": "3-5 years",
            "Senior": "5-8 years",
            "Lead": "7-10 years",
            "Principal": "10+ years",
            "Director": "8-12 years"
        }
        
        years = experience_years.get(level, "3-5 years")
        
        requirements = [
            f"{years} of professional experience",
            f"Strong proficiency in {', '.join(skills[:4])}",
            "Excellent problem-solving and communication skills",
            "Experience with agile development methodologies"
        ]
        
        if level in ["Senior", "Lead", "Principal"]:
            requirements.extend([
                "Experience leading technical projects",
                "Mentoring and coaching experience"
            ])
        
        return "\n".join(f"• {req}" for req in requirements)
    
    def _calculate_trend_score(self, skills: List[str]) -> float:
        """Calculate market trend score for the job"""
        score = 0.0
        total_skills = len(skills)
        
        for skill in skills:
            if skill in self.skill_trends["high_demand"]:
                score += 1.0
            elif skill in self.skill_trends["emerging"]:
                score += 0.8
            elif skill in self.skill_trends["stable"]:
                score += 0.6
            else:
                score += 0.4
        
        return round(score / total_skills, 2) if total_skills > 0 else 0.5
    
    def create_batch_jobs(self, count: int = 10) -> List[Dict]:
        """Create a batch of dynamic jobs"""
        jobs = []
        job_types = list(self.job_templates.keys())
        
        for i in range(count):
            # Distribute job types evenly
            job_type = job_types[i % len(job_types)]
            client_id = (i % 5) + 1  # Distribute across 5 clients
            
            job = self.create_dynamic_job(job_type, client_id)
            jobs.append(job)
        
        return jobs
    
    def post_job_to_api(self, job_data: Dict) -> bool:
        """Post job to API"""
        try:
            # Remove non-API fields
            api_job_data = {k: v for k, v in job_data.items() 
                           if k not in ['salary_range', 'employment_type', 'created_dynamically', 'market_trend_score']}
            
            response = requests.post(f"{API_BASE}/v1/jobs", json=api_job_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Created job: {job_data['title']} (ID: {result.get('job_id')})")
                return True
            else:
                print(f"❌ Failed to create job: {job_data['title']} - {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating job: {job_data['title']} - {str(e)}")
            return False
    
    def create_and_post_jobs(self, count: int = 10) -> Dict:
        """Create and post jobs to API"""
        print(f"🚀 Creating {count} dynamic jobs based on market trends...")
        
        jobs = self.create_batch_jobs(count)
        successful = 0
        failed = 0
        
        for job in jobs:
            if self.post_job_to_api(job):
                successful += 1
            else:
                failed += 1
        
        print(f"\n📊 Results:")
        print(f"✅ Successfully created: {successful} jobs")
        print(f"❌ Failed: {failed} jobs")
        print(f"📈 Success rate: {(successful/count)*100:.1f}%")
        
        return {
            "total": count,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful/count)*100,
            "jobs_created": jobs
        }

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dynamic Job Creator")
    parser.add_argument("--count", type=int, default=10, help="Number of jobs to create")
    parser.add_argument("--type", type=str, help="Specific job type to create")
    parser.add_argument("--client-id", type=int, help="Specific client ID")
    parser.add_argument("--dry-run", action="store_true", help="Generate jobs without posting to API")
    
    args = parser.parse_args()
    
    creator = DynamicJobCreator()
    
    if args.dry_run:
        print(f"🔍 Dry run: Generating {args.count} jobs without posting...")
        jobs = creator.create_batch_jobs(args.count)
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Department: {job['department']}")
            print(f"   Location: {job['location']}")
            print(f"   Skills: {job['requirements'][:100]}...")
            print(f"   Trend Score: {job['market_trend_score']}")
    else:
        results = creator.create_and_post_jobs(args.count)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dynamic_jobs_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")

if __name__ == "__main__":
    main()
