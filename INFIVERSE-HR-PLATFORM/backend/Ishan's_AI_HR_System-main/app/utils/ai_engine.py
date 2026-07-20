import json
import re
from datetime import datetime
from typing import Dict, List, Any
from app.utils.ml_models import MLModels
import logging

logger = logging.getLogger(__name__)

class AIEngine:
    """AI-powered candidate matching and recommendation engine"""
    
    @staticmethod
    def calculate_match_score(candidate: Dict, job_requirements: List[str] = None) -> float:
        """Calculate AI match score using ML similarity"""
        try:
            skills = candidate.get('skills', [])
            if not job_requirements:
                job_requirements = ['Python', 'FastAPI', 'AI', 'Machine Learning']
            
            # Use ML-powered similarity calculation
            ml_score = MLModels.calculate_skill_similarity(skills, job_requirements)
            
            # Fallback to simple matching if ML fails
            if ml_score == 0.0:
                matches = sum(1 for skill in skills if any(req.lower() in skill.lower() for req in job_requirements))
                ml_score = min(95.0, (matches / len(job_requirements)) * 100)
            
            return round(ml_score, 2)
        except:
            return 0.0
    
    @staticmethod
    def generate_recommendations(candidate_id: int, feedback_history: List[Dict]) -> List[str]:
        """Generate AI recommendations based on feedback"""
        recommendations = []
        
        if not feedback_history:
            recommendations.append("Schedule initial screening interview")
            return recommendations
        
        avg_score = sum(f.get('score', 0) for f in feedback_history) / len(feedback_history)
        
        if avg_score >= 4:
            recommendations.extend([
                "Strong candidate - proceed to final interview",
                "Consider for senior role placement"
            ])
        elif avg_score >= 3:
            recommendations.extend([
                "Schedule technical assessment",
                "Conduct behavioral interview"
            ])
        else:
            recommendations.extend([
                "Provide additional training resources",
                "Consider alternative role fit"
            ])
        
        return recommendations

class SmartNotifications:
    """Smart notification system with AI-driven timing"""
    
    @staticmethod
    def get_optimal_send_time() -> str:
        """Get optimal time to send notifications"""
        hour = datetime.now().hour
        if 9 <= hour <= 11:
            return "morning_peak"
        elif 14 <= hour <= 16:
            return "afternoon_peak"
        else:
            return "off_peak"
    
    @staticmethod
    def personalize_message(template: str, candidate: Dict) -> str:
        """Personalize message content"""
        name = candidate.get('name', 'Candidate')
        skills = ', '.join(candidate.get('skills', [])[:2])
        
        return template.replace('{name}', name).replace('{skills}', skills)