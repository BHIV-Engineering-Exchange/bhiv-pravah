"""
RL Loop Service

Processes rewards from different pipeline stages and merges them into unified episodes.
Handles rewards from:
- LM Core output quality
- KSML label accuracy
- Vaani user feedback

Focused on Arabic language reinforcement learning for the Sovereign Fusion Layer.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ── RL BOUNDARY ENFORCEMENT ──────────────────────────────────────────────
# RL can optimize pacing, sequencing, and personalization.
# RL CANNOT mutate grading authority, governance semantics, or policy logic.
# ──────────────────────────────────────────────────────────────────────────


def process_lm_output(
    lm_output: str,
    original_text: str,
    language: str,
    db: Session
) -> Dict[str, Any]:
    """
    Process LM output and generate reward based on quality
    
    Args:
        lm_output: Generated text from LM Core
        original_text: Original input text
        language: Language code
        db: Database session
        
    Returns:
        dict: Reward information
    """
    try:
        # Simple quality metrics (can be enhanced with actual quality models)
        output_length = len(lm_output.split())
        input_length = len(original_text.split())
        
        # Reward based on output quality heuristics
        # In production, this would use actual quality models
        length_ratio = min(output_length / max(input_length, 1), 2.0) / 2.0
        
        # Check for completeness (has content)
        has_content = len(lm_output.strip()) > 0
        
        # Calculate reward (0.0 to 1.0)
        reward_value = 0.5  # Base reward
        if has_content:
            reward_value += 0.3
        if 0.5 <= length_ratio <= 1.5:  # Reasonable length
            reward_value += 0.2
        
        reward_value = min(reward_value, 1.0)
        
        # BOUNDARY GUARD: Ensure reward context does not include grading authority overrides
        context = {
            "output_length": output_length,
            "input_length": input_length,
            "length_ratio": length_ratio,
            "has_content": has_content
        }
        
        return {
            "source": "lm_core",
            "reward_value": reward_value,
            "reward_type": "quality",
            "context": context,
            "schema_version": "edu.reward.v1",
            "provenance": "gurukul.rl_loop.lm_processing",
            "ownership": "educational_intelligence"
        }
        
    except Exception as e:
        logger.error(f"LM output processing failed: {e}")
        return {
            "source": "lm_core",
            "reward_value": 0.0,
            "reward_type": "quality",
            "context": {"error": str(e)}
        }


def process_ksml_labels(
    ksml_result: Dict[str, Any],
    language: str,
    db: Session
) -> Dict[str, Any]:
    """
    Process KSML labels and generate reward based on annotation quality
    
    Args:
        ksml_result: KSML annotation result
        language: Language code
        db: Database session
        
    Returns:
        dict: Reward information
    """
    try:
        labels = ksml_result.get("ksml_labels", {})
        
        # Reward based on label completeness
        required_labels = ["language", "has_questions", "has_examples", "has_definitions"]
        labels_present = sum(1 for label in required_labels if label in labels)
        completeness = labels_present / len(required_labels)
        
        # Reward based on structure detection
        structure = labels.get("structure", {})
        structure_detected = any(structure.values()) if structure else False
        
        # Calculate reward
        reward_value = completeness * 0.6
        if structure_detected:
            reward_value += 0.2
        if labels.get("topics"):
            reward_value += 0.2
        
        reward_value = min(reward_value, 1.0)
        
        return {
            "source": "ksml",
            "reward_value": reward_value,
            "reward_type": "accuracy",
            "context": {
                "labels_present": labels_present,
                "completeness": completeness,
                "structure_detected": structure_detected,
                "topics_found": bool(labels.get("topics"))
            }
        }
        
    except Exception as e:
        logger.error(f"KSML processing failed: {e}")
        return {
            "source": "ksml",
            "reward_value": 0.0,
            "reward_type": "accuracy",
            "context": {"error": str(e)}
        }


def process_vaani_feedback(
    user_feedback: Optional[Dict[str, Any]],
    audio_output: Optional[str],
    prosody_hint: Optional[str],
    db: Session
) -> Dict[str, Any]:
    """
    Process Vaani user feedback and generate reward
    
    Args:
        user_feedback: User feedback dict (e.g., {"rating": 5, "comment": "..."})
        audio_output: Path to generated audio file
        prosody_hint: Prosody hint used
        db: Database session
        
    Returns:
        dict: Reward information
    """
    try:
        if not user_feedback:
            # No feedback yet, return neutral reward
            return {
                "source": "vaani",
                "reward_value": 0.5,
                "reward_type": "user_satisfaction",
                "context": {"note": "No user feedback yet"}
            }
        
        # Extract rating (assume 1-5 scale)
        rating = user_feedback.get("rating", 3)
        reward_value = rating / 5.0  # Normalize to 0.0-1.0
        
        # Adjust based on comment sentiment (simplified)
        comment = user_feedback.get("comment", "").lower()
        if any(word in comment for word in ["good", "great", "excellent", "perfect"]):
            reward_value = min(reward_value + 0.1, 1.0)
        elif any(word in comment for word in ["bad", "terrible", "awful", "wrong"]):
            reward_value = max(reward_value - 0.2, 0.0)
        
        return {
            "source": "vaani",
            "reward_value": reward_value,
            "reward_type": "user_satisfaction",
            "context": {
                "rating": rating,
                "has_comment": bool(user_feedback.get("comment")),
                "prosody_hint": prosody_hint
            },
            "feedback_text": user_feedback.get("comment")
        }
        
    except Exception as e:
        logger.error(f"Vaani feedback processing failed: {e}")
        return {
            "source": "vaani",
            "reward_value": 0.0,
            "reward_type": "user_satisfaction",
            "context": {"error": str(e)}
        }


def merge_episodes(
    episode_data: Dict[str, Any],
    rewards: List[Dict[str, Any]],
    db: Session
) -> str:
    """
    Merge all episode data and rewards into unified reward store
    
    Args:
        episode_data: Episode metadata (text, language, outputs, etc.)
        rewards: List of reward dictionaries from different sources
        db: Database session
        
    Returns:
        str: Episode ID
    """
    try:
        from app.models.rl_models import RLEpisode, RLReward
        
        # Generate episode ID
        episode_id = episode_data.get("episode_id") or f"ep_{uuid.uuid4().hex[:12]}"
        
        # Create episode
        episode = RLEpisode(
            episode_id=episode_id,
            source_text=episode_data.get("source_text", ""),
            target_lang=episode_data.get("target_lang", "ar"),
            tone=episode_data.get("tone"),
            lm_output=episode_data.get("lm_output"),
            ksml_labels=episode_data.get("ksml_labels"),
            prosody_hint=episode_data.get("prosody_hint"),
            metadata_=episode_data.get("metadata", {})
        )
        
        db.add(episode)
        db.flush()  # Get episode ID
        
        # Add rewards
        for reward_data in rewards:
            reward = RLReward(
                episode_id=episode.id,
                source=reward_data.get("source"),
                reward_value=reward_data.get("reward_value", 0.0),
                reward_type=reward_data.get("reward_type", "unknown"),
                context=reward_data.get("context", {}),
                feedback_text=reward_data.get("feedback_text")
            )
            db.add(reward)
        
        db.commit()
        logger.info(f"Episode {episode_id} merged with {len(rewards)} rewards")
        
        return episode_id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to merge episode: {e}")
        raise

