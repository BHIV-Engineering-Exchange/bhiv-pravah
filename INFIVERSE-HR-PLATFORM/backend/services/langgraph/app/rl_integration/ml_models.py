import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MLModels:
    """Machine Learning models for HR predictions"""
    
    @staticmethod
    def calculate_skill_similarity(candidate_skills, job_requirements):
        """Calculate skill similarity using TF-IDF and cosine similarity"""
        try:
            if not candidate_skills or not job_requirements:
                return 0.0
            
            # Combine skills into text
            candidate_text = ' '.join(candidate_skills)
            job_text = ' '.join(job_requirements)
            
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([candidate_text, job_text])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return round(similarity * 100, 2)
        except Exception as e:
            logger.error(f"Skill similarity calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def predict_interview_success(feedback_scores, skills_match_score):
        """Predict interview success probability"""
        try:
            if not feedback_scores:
                return skills_match_score * 0.6  # Base on skills only
            
            avg_feedback = sum(feedback_scores) / len(feedback_scores)
            
            # Weighted prediction: 60% feedback, 40% skills
            prediction = (avg_feedback * 20 * 0.6) + (skills_match_score * 0.4)
            return min(100, max(0, round(prediction, 2)))
        except Exception as e:
            logger.error(f"Success prediction failed: {e}")
            return 0.0
    
    @staticmethod
    def analyze_hiring_patterns(candidates_data):
        """Analyze hiring patterns and trends"""
        try:
            if not candidates_data:
                return {}
            
            patterns = {
                "total_candidates": len(candidates_data),
                "avg_skills_count": 0,
                "top_skills": {},
                "score_distribution": {"high": 0, "medium": 0, "low": 0}
            }
            
            all_skills = []
            scores = []
            
            for candidate in candidates_data:
                skills = candidate.get('skills', [])
                all_skills.extend(skills)
                
                score = candidate.get('match_score', 0)
                scores.append(score)
                
                if score >= 80:
                    patterns["score_distribution"]["high"] += 1
                elif score >= 60:
                    patterns["score_distribution"]["medium"] += 1
                else:
                    patterns["score_distribution"]["low"] += 1
            
            # Calculate averages
            if candidates_data:
                patterns["avg_skills_count"] = len(all_skills) / len(candidates_data)
            
            # Count skill frequency
            for skill in all_skills:
                patterns["top_skills"][skill] = patterns["top_skills"].get(skill, 0) + 1
            
            return patterns
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {}

class PredictiveAnalytics:
    """Advanced predictive analytics for HR decisions"""
    
    @staticmethod
    def forecast_hiring_needs(historical_data, months_ahead=3):
        """Forecast hiring needs based on historical data"""
        try:
            if not historical_data:
                return {"forecast": "Insufficient data"}
            
            # Simple trend analysis
            recent_hires = len([h for h in historical_data if h.get('hired', False)])
            total_candidates = len(historical_data)
            
            hire_rate = recent_hires / total_candidates if total_candidates > 0 else 0
            
            forecast = {
                "current_hire_rate": round(hire_rate * 100, 1),
                "projected_hires": round(hire_rate * 50 * months_ahead),  # Assuming 50 candidates per month
                "recommendation": "Increase sourcing" if hire_rate < 0.2 else "Maintain current pace"
            }
            
            return forecast
        except Exception as e:
            logger.error(f"Hiring forecast failed: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def identify_success_factors(feedback_data):
        """Identify factors that lead to successful hires"""
        try:
            if not feedback_data:
                return {}
            
            success_factors = {
                "high_score_outcomes": {"accept": 0, "reject": 0},
                "skill_success_rate": {},
                "feedback_patterns": {}
            }
            
            for feedback in feedback_data:
                score = feedback.get('score', 0)
                outcome = feedback.get('outcome', 'unknown')
                
                if score >= 4:
                    success_factors["high_score_outcomes"][outcome] = success_factors["high_score_outcomes"].get(outcome, 0) + 1
            
            return success_factors
        except Exception as e:
            logger.error(f"Success factor analysis failed: {e}")
            return {}