from datetime import datetime
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DecisionEngine:
    """RL-enhanced decision engine for candidate evaluation"""
    
    def __init__(self, db_adapter=None):
        self.db_adapter = db_adapter
    
    def make_rl_decision(self, candidate_features: Dict, job_features: Dict, 
                        feedback_history: List[Dict] = None) -> Dict:
        """Make RL-enhanced hiring decision"""
        try:
            from .ml_models import MLModels
            
            # Calculate base similarity
            candidate_skills = candidate_features.get('skills', [])
            job_requirements = job_features.get('requirements', [])
            
            base_score = MLModels.calculate_skill_similarity(candidate_skills, job_requirements)
            
            # Apply RL adjustments based on feedback
            rl_adjustment = self._calculate_rl_adjustment(feedback_history or [])
            
            # Final RL score
            rl_score = min(100, max(0, base_score + rl_adjustment))
            
            # Determine decision type
            if rl_score >= 75:
                decision_type = "recommend"
            elif rl_score >= 50:
                decision_type = "review"
            else:
                decision_type = "reject"
            
            # Calculate confidence
            confidence = self._calculate_confidence(rl_score, len(feedback_history or []))
            
            decision_data = {
                "rl_score": round(rl_score, 2),
                "base_score": round(base_score, 2),
                "rl_adjustment": round(rl_adjustment, 2),
                "decision_type": decision_type,
                "confidence_level": round(confidence, 2),
                "reasoning": self._generate_reasoning(base_score, rl_adjustment, decision_type),
                "model_version": "v1.0.0",
                "features_used": {
                    "candidate_skills_count": len(candidate_skills),
                    "job_requirements_count": len(job_requirements),
                    "feedback_samples": len(feedback_history or [])
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return decision_data
            
        except Exception as e:
            logger.error(f"RL decision failed: {e}")
            return {
                "rl_score": 0.0,
                "decision_type": "review",
                "confidence_level": 0.0,
                "error": str(e)
            }
    
    def _calculate_rl_adjustment(self, feedback_history: List[Dict]) -> float:
        """Calculate RL adjustment based on historical feedback"""
        if not feedback_history:
            return 0.0
        
        try:
            total_reward = 0.0
            for feedback in feedback_history[-10:]:  # Last 10 feedback entries
                reward = self._calculate_reward_signal(feedback)
                total_reward += reward
            
            # Average reward as adjustment (-20 to +20 points)
            avg_reward = total_reward / len(feedback_history[-10:])
            adjustment = avg_reward * 20
            
            return max(-20, min(20, adjustment))
            
        except Exception as e:
            logger.error(f"RL adjustment calculation failed: {e}")
            return 0.0
    
    def _calculate_reward_signal(self, feedback: Dict) -> float:
        """Calculate reward signal from feedback outcome"""
        try:
            outcome = feedback.get('actual_outcome', 'unknown')
            feedback_score = feedback.get('feedback_score', 3)
            
            # Reward mapping
            outcome_rewards = {
                'hired': 1.0,
                'interviewed': 0.5,
                'shortlisted': 0.3,
                'rejected': -0.5,
                'withdrawn': -0.2
            }
            
            base_reward = outcome_rewards.get(outcome, 0.0)
            
            # Adjust by feedback score (1-5 scale)
            score_adjustment = (feedback_score - 3) / 2  # -1 to +1
            
            return base_reward + (score_adjustment * 0.3)
            
        except Exception as e:
            logger.error(f"Reward calculation failed: {e}")
            return 0.0
    
    def _calculate_confidence(self, rl_score: float, feedback_count: int) -> float:
        """Calculate confidence level in the decision"""
        try:
            # Base confidence from score certainty
            if rl_score >= 80 or rl_score <= 20:
                base_confidence = 90.0
            elif rl_score >= 70 or rl_score <= 30:
                base_confidence = 75.0
            else:
                base_confidence = 60.0
            
            # Adjust by feedback sample size
            if feedback_count >= 10:
                confidence_boost = 10.0
            elif feedback_count >= 5:
                confidence_boost = 5.0
            else:
                confidence_boost = 0.0
            
            return min(95.0, base_confidence + confidence_boost)
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 50.0
    
    def _generate_reasoning(self, base_score: float, rl_adjustment: float, 
                          decision_type: str) -> str:
        """Generate human-readable reasoning for the decision"""
        try:
            reasoning_parts = []
            
            # Base score reasoning
            if base_score >= 80:
                reasoning_parts.append("Strong skill match with job requirements")
            elif base_score >= 60:
                reasoning_parts.append("Good skill alignment with some gaps")
            else:
                reasoning_parts.append("Limited skill match with requirements")
            
            # RL adjustment reasoning
            if rl_adjustment > 5:
                reasoning_parts.append("Historical feedback suggests positive outcomes")
            elif rl_adjustment < -5:
                reasoning_parts.append("Historical feedback indicates potential concerns")
            else:
                reasoning_parts.append("Neutral historical performance indicators")
            
            # Decision reasoning
            decision_reasons = {
                "recommend": "Strong candidate for immediate consideration",
                "review": "Candidate requires additional evaluation",
                "reject": "Candidate does not meet current requirements"
            }
            
            reasoning_parts.append(decision_reasons.get(decision_type, "Standard evaluation"))
            
            return ". ".join(reasoning_parts) + "."
            
        except Exception as e:
            logger.error(f"Reasoning generation failed: {e}")
            return "Decision based on standard evaluation criteria."

class EventTimeline:
    """Event timeline tracking for RL decisions"""
    
    def __init__(self, db_adapter=None):
        self.db_adapter = db_adapter
    
    def log_rl_decision(self, candidate_id: int, job_id: int, decision_data: Dict) -> Optional[str]:
        """Log RL decision to timeline"""
        try:
            event_data = {
                "candidate_id": candidate_id,
                "job_id": job_id,
                "event_type": "rl_decision",
                "decision_type": decision_data.get("decision_type"),
                "rl_score": decision_data.get("rl_score"),
                "confidence_level": decision_data.get("confidence_level"),
                "reasoning": decision_data.get("reasoning"),
                "timestamp": datetime.now().isoformat(),
                "event_id": f"RL_{candidate_id}_{job_id}_{int(datetime.now().timestamp())}"
            }
            
            # Store in database if adapter available
            if self.db_adapter:
                self.db_adapter.log_rl_decision(event_data)
            
            logger.info(f"RL decision logged: {decision_data.get('decision_type')} for candidate {candidate_id}")
            return event_data["event_id"]
            
        except Exception as e:
            logger.error(f"Failed to log RL decision: {e}")
            return None
    
    def get_candidate_rl_history(self, candidate_id: int) -> List[Dict]:
        """Get RL decision history for candidate"""
        try:
            if self.db_adapter:
                return self.db_adapter.get_candidate_rl_history(candidate_id)
            return []
            
        except Exception as e:
            logger.error(f"Failed to get RL history: {e}")
            return []