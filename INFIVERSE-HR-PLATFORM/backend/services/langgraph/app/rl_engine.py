"""
RL Engine for LangGraph Service
Provides reinforcement learning score calculation and feedback processing
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class RLEngine:
    """Reinforcement Learning Engine for candidate scoring"""
    
    def __init__(self, model_version: str = "v1.0.0"):
        self.model_version = model_version
        self._learning_rate = 0.1
        self._exploration_rate = 0.2
        self._feature_weights = {}
        logger.info(f"✅ RL Engine initialized: {model_version}")
    
    def calculate_rl_score(
        self, 
        candidate_features: Dict[str, Any], 
        job_features: Dict[str, Any],
        feedback_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calculate RL-enhanced matching score
        
        Args:
            candidate_features: Skills, experience, education of candidate
            job_features: Requirements, title, description of job
            feedback_history: Past feedback to learn from
        
        Returns:
            Dict with rl_score, confidence_level, decision_type, features_used
        """
        try:
            # Extract candidate skills
            candidate_skills = set(
                s.lower() if isinstance(s, str) else s.get('name', '').lower() 
                for s in candidate_features.get('skills', [])
            )
            
            # Extract job requirements
            job_requirements = set(
                r.lower() if isinstance(r, str) else r.get('name', '').lower() 
                for r in job_features.get('requirements', [])
            )
            
            # Calculate skill match ratio
            if job_requirements:
                skill_match = len(candidate_skills & job_requirements) / len(job_requirements)
            else:
                skill_match = 0.5  # Default for no requirements
            
            # Calculate experience score
            experience = candidate_features.get('experience', [])
            experience_score = min(len(experience) * 10, 30)  # Max 30 points
            
            # Calculate education score
            education = candidate_features.get('education', [])
            education_score = min(len(education) * 10, 20)  # Max 20 points
            
            # Base score calculation
            base_score = (skill_match * 50) + experience_score + education_score
            
            # Apply RL adjustment from feedback history
            rl_adjustment = self._calculate_rl_adjustment(
                candidate_features, job_features, feedback_history
            )
            
            # Calculate final RL score
            rl_score = min(100, max(0, base_score + rl_adjustment))
            
            # Calculate confidence based on feedback history
            confidence = self._calculate_confidence(feedback_history)
            
            # Determine decision type
            if rl_score >= 75:
                decision_type = "shortlist"
            elif rl_score >= 50:
                decision_type = "review"
            else:
                decision_type = "reject"
            
            result = {
                "rl_score": round(rl_score, 2),
                "confidence_level": confidence,
                "decision_type": decision_type,
                "features_used": {
                    "skill_match": round(skill_match * 100, 2),
                    "experience_score": experience_score,
                    "education_score": education_score,
                    "rl_adjustment": round(rl_adjustment, 2)
                },
                "model_version": self.model_version
            }
            
            logger.debug(f"RL Score calculated: {rl_score:.2f}, Decision: {decision_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating RL score: {e}")
            return {
                "rl_score": 50.0,
                "confidence_level": 30,
                "decision_type": "review",
                "features_used": {},
                "model_version": self.model_version,
                "error": str(e)
            }
    
    def _calculate_rl_adjustment(
        self,
        candidate_features: Dict,
        job_features: Dict,
        feedback_history: List[Dict] = None
    ) -> float:
        """Calculate RL adjustment based on feedback history"""
        if not feedback_history:
            return 0.0
        
        try:
            # Calculate average reward from recent feedback
            positive_count = 0
            negative_count = 0
            
            for feedback in feedback_history[:20]:  # Use last 20 feedbacks
                reward = feedback.get('reward_signal', 0)
                if reward > 0:
                    positive_count += 1
                elif reward < 0:
                    negative_count += 1
            
            # Calculate adjustment factor
            total = positive_count + negative_count
            if total > 0:
                adjustment = ((positive_count - negative_count) / total) * 10
            else:
                adjustment = 0.0
            
            return adjustment
            
        except Exception as e:
            logger.error(f"Error calculating RL adjustment: {e}")
            return 0.0
    
    def _calculate_confidence(self, feedback_history: List[Dict] = None) -> int:
        """Calculate confidence level based on feedback history"""
        if not feedback_history:
            return 50  # Default confidence
        
        # More feedback = higher confidence
        feedback_count = len(feedback_history)
        
        if feedback_count >= 100:
            return 90
        elif feedback_count >= 50:
            return 80
        elif feedback_count >= 20:
            return 70
        elif feedback_count >= 10:
            return 60
        else:
            return 50
    
    def update_model(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Update model weights based on training data"""
        try:
            if not training_data:
                return {"status": "no_data", "model_version": self.model_version}
            
            # Simple weight update logic
            for sample in training_data:
                reward = sample.get('reward', 0)
                features = sample.get('feature_vector', [])
                
                # Update feature weights based on reward
                for i, feature in enumerate(features):
                    if i not in self._feature_weights:
                        self._feature_weights[i] = 0.5
                    
                    self._feature_weights[i] += self._learning_rate * reward * feature
            
            logger.info(f"Model updated with {len(training_data)} samples")
            return {
                "status": "updated",
                "samples_processed": len(training_data),
                "model_version": self.model_version
            }
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
            return {"status": "error", "error": str(e)}


class FeedbackProcessor:
    """Process and transform feedback for RL learning"""
    
    def __init__(self):
        self._outcome_rewards = {
            "hired": 1.0,
            "shortlisted": 0.5,
            "reviewed": 0.0,
            "pending": 0.0,
            "rejected": -0.3,
            "withdrawn": -0.5
        }
        logger.info("✅ Feedback Processor initialized")
    
    def process_feedback(self, feedback_data: Dict) -> Dict[str, Any]:
        """Process raw feedback into RL-compatible format"""
        try:
            actual_outcome = feedback_data.get('actual_outcome', 'pending')
            feedback_score = feedback_data.get('feedback_score', 3)
            
            # Calculate reward signal
            outcome_reward = self._outcome_rewards.get(actual_outcome, 0.0)
            score_reward = (feedback_score - 3) / 2  # Normalize to [-1, 1]
            reward_signal = (outcome_reward + score_reward) / 2
            
            processed = {
                "prediction_id": feedback_data.get('prediction_id'),
                "candidate_id": feedback_data.get('candidate_id'),
                "actual_outcome": actual_outcome,
                "feedback_score": feedback_score,
                "feedback_source": feedback_data.get('feedback_source', 'system'),
                "reward_signal": round(reward_signal, 3),
                "feedback_notes": feedback_data.get('feedback_notes', ''),
                "processed_at": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Feedback processed: outcome={actual_outcome}, reward={reward_signal:.3f}")
            return processed
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return {
                "error": str(e),
                "feedback_data": feedback_data
            }
    
    def generate_training_data(
        self,
        candidate_features: Dict,
        job_features: Dict,
        matching_score: float,
        actual_outcome: str
    ) -> Dict[str, Any]:
        """Generate training data from a completed prediction-feedback cycle"""
        try:
            reward = self._outcome_rewards.get(actual_outcome, 0.0)
            
            # Create feature vector (simplified)
            feature_vector = [
                len(candidate_features.get('skills', [])) / 10,
                len(candidate_features.get('experience', [])) / 5,
                len(candidate_features.get('education', [])) / 3,
                len(job_features.get('requirements', [])) / 10,
                matching_score / 100
            ]
            
            training_data = {
                "candidate_features": candidate_features,
                "job_features": job_features,
                "matching_score": matching_score,
                "actual_outcome": actual_outcome,
                "reward": reward,
                "feature_vector": feature_vector,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "version": "1.0.0"
                }
            }
            
            logger.debug(f"Training data generated: outcome={actual_outcome}, reward={reward}")
            return training_data
            
        except Exception as e:
            logger.error(f"Error generating training data: {e}")
            return {
                "error": str(e)
            }
    
    def calculate_batch_reward(self, feedback_batch: List[Dict]) -> float:
        """Calculate aggregate reward for a batch of feedback"""
        if not feedback_batch:
            return 0.0
        
        total_reward = sum(
            fb.get('reward_signal', 0) for fb in feedback_batch
        )
        return total_reward / len(feedback_batch)


# Global instances
rl_engine = RLEngine(model_version="v1.0.0")
feedback_processor = FeedbackProcessor()
