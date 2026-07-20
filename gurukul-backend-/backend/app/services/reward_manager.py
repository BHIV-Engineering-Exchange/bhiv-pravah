"""
Reward Manager Service

Manages unified reward table and policy updates for the RL system.
Provides functions to query, aggregate, and update rewards.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ── AUTHORIZED OPTIMIZATION VARIABLES ────────────────────────────────────
# Only these keys can be mutated by the RL policy logic.
# ──────────────────────────────────────────────────────────────────────────
AUTHORIZED_RL_PARAMETERS = {
    "learning_rate",
    "pacing_coefficient",
    "sequencing_bias",
    "tone_preference",
    "reinforcement_density",
}


def add_reward(
    episode_id: str,
    source: str,
    reward_value: float,
    reward_type: str,
    context: Optional[Dict[str, Any]] = None,
    feedback_text: Optional[str] = None,
    db: Session = None
) -> bool:
    """
    Add a reward to the unified reward store
    
    Args:
        episode_id: Episode ID
        source: Reward source ('lm_core', 'ksml', 'vaani', 'user_feedback')
        reward_value: Reward value (0.0 to 1.0)
        reward_type: Type of reward ('quality', 'accuracy', 'user_satisfaction')
        context: Additional context
        feedback_text: User feedback text if applicable
        db: Database session
        
    Returns:
        bool: True if successful
    """
    if db is None:
        logger.warning("No database session provided, reward not saved")
        return False
    
    try:
        from app.models.rl_models import RLEpisode, RLReward
        
        # Find episode
        episode = db.query(RLEpisode).filter(RLEpisode.episode_id == episode_id).first()
        if not episode:
            logger.warning(f"Episode {episode_id} not found, cannot add reward")
            return False
        
        # Create reward
        reward = RLReward(
            episode_id=episode.id,
            source=source,
            reward_value=reward_value,
            reward_type=reward_type,
            context=context or {},
            feedback_text=feedback_text
        )
        
        db.add(reward)
        db.commit()
        
        logger.debug(f"Reward added: {source} = {reward_value} for episode {episode_id}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add reward: {e}")
        return False


def get_unified_rewards(
    episode_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Get all rewards for an episode
    
    Args:
        episode_id: Episode ID
        db: Database session
        
    Returns:
        dict: Unified rewards with aggregated statistics
    """
    try:
        from app.models.rl_models import RLEpisode, RLReward
        
        # Find episode
        episode = db.query(RLEpisode).filter(RLEpisode.episode_id == episode_id).first()
        if not episode:
            return {"error": f"Episode {episode_id} not found"}
        
        # Get all rewards
        rewards = db.query(RLReward).filter(RLReward.episode_id == episode.id).all()
        
        # Aggregate by source
        rewards_by_source = {}
        total_reward = 0.0
        
        for reward in rewards:
            source = reward.source
            if source not in rewards_by_source:
                rewards_by_source[source] = {
                    "rewards": [],
                    "average": 0.0,
                    "count": 0
                }
            
            rewards_by_source[source]["rewards"].append({
                "value": reward.reward_value,
                "type": reward.reward_type,
                "context": reward.context,
                "timestamp": reward.created_at.isoformat() if reward.created_at else None
            })
            rewards_by_source[source]["count"] += 1
            total_reward += reward.reward_value
        
        # Calculate averages
        for source_data in rewards_by_source.values():
            if source_data["count"] > 0:
                source_data["average"] = sum(
                    r["value"] for r in source_data["rewards"]
                ) / source_data["count"]
        
        overall_average = total_reward / len(rewards) if rewards else 0.0
        
        return {
            "episode_id": episode_id,
            "total_rewards": len(rewards),
            "overall_average": round(overall_average, 4),
            "rewards_by_source": rewards_by_source,
            "episode_metadata": {
                "source_text": episode.source_text[:100] + "..." if len(episode.source_text) > 100 else episode.source_text,
                "target_lang": episode.target_lang,
                "tone": episode.tone,
                "created_at": episode.created_at.isoformat() if episode.created_at else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get unified rewards: {e}")
        return {"error": str(e)}


def update_policy(
    language: str,
    rewards: List[Dict[str, Any]],
    db: Session,
    new_parameters: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update RL policy based on accumulated rewards and optional parameters.
    Strictly enforces authorized parameter boundaries and clamps pacing.
    
    Args:
        language: Language code (e.g., 'ar')
        rewards: List of reward data
        db: Database session
        new_parameters: Optional parameter dictionary to update
        
    Returns:
        bool: True if policy updated successfully
    """
    try:
        from app.models.rl_models import RLPolicy
        
        policy_name = f"sovereign_fusion_{language}"
        
        # Find or create policy
        policy = db.query(RLPolicy).filter(
            RLPolicy.policy_name == policy_name,
            RLPolicy.is_active == True
        ).first()
        
        if not policy:
            policy = RLPolicy(
                policy_name=policy_name,
                language=language,
                parameters={},
                version="1.0.0"
            )
            db.add(policy)
        
        # Calculate average reward
        avg_reward = 0.0
        if rewards:
            avg_reward = sum(r.get("reward_value", 0.0) for r in rewards) / len(rewards)
            
            # Update policy statistics
            if policy.total_episodes is None:
                policy.total_episodes = 0
            policy.total_episodes += 1
            
            # Exponential moving average
            if policy.average_reward is None:
                policy.average_reward = 0.0
            policy.average_reward = 0.9 * policy.average_reward + 0.1 * avg_reward
            
        # Get baseline parameters
        existing_params = dict(policy.parameters or {})
        
        # Merge proposed updates
        proposed_updates = {}
        if new_parameters:
            proposed_updates.update(new_parameters)
            
        # Also extract updates from rewards if any contain adjustment hints
        for r in rewards:
            ctx = r.get("context", {})
            if isinstance(ctx, dict):
                if "pacing_adjustment" in ctx:
                    proposed_updates["pacing_coefficient"] = existing_params.get("pacing_coefficient", 1.0) + ctx["pacing_adjustment"]
                if "sequencing_bias" in ctx:
                    proposed_updates["sequencing_bias"] = ctx["sequencing_bias"]
                
        # Validate proposed parameters against authorized list
        cleaned_updates = {}
        for k, v in proposed_updates.items():
            if k in AUTHORIZED_RL_PARAMETERS:
                # Bounding constraints for pacing
                if k == "pacing_coefficient":
                    try:
                        val = float(v)
                        # Clamp pacing to [0.5, 2.0]
                        clamped_val = max(0.5, min(2.0, val))
                        cleaned_updates[k] = clamped_val
                        if clamped_val != val:
                            logger.warning(f"Clamped pacing_coefficient from {val} to {clamped_val} to enforce TANTRA safety bounds.")
                    except (ValueError, TypeError):
                        logger.error(f"Invalid type for pacing_coefficient: {v}")
                else:
                    cleaned_updates[k] = v
            else:
                logger.warning(f"Blocked unauthorized parameter update attempt: '{k}' is not in AUTHORIZED_RL_PARAMETERS.")
                
        # Compile new parameter set
        new_params = {
            "learning_rate": cleaned_updates.get("learning_rate", existing_params.get("learning_rate", 0.001)),
            "last_avg_reward": round(avg_reward, 4) if rewards else existing_params.get("last_avg_reward", 0.0),
            "update_count": existing_params.get("update_count", 0) + 1,
            "pacing_coefficient": cleaned_updates.get("pacing_coefficient", existing_params.get("pacing_coefficient", 1.0)),
            "sequencing_bias": cleaned_updates.get("sequencing_bias", existing_params.get("sequencing_bias", 0.0)),
            "tone_preference": cleaned_updates.get("tone_preference", existing_params.get("tone_preference", 0.0)),
            "reinforcement_density": cleaned_updates.get("reinforcement_density", existing_params.get("reinforcement_density", 0.0)),
        }
        
        # Double check filtering to prevent any downstream bypasses
        policy.parameters = {
            k: v for k, v in new_params.items() 
            if k in AUTHORIZED_RL_PARAMETERS or k in ["last_avg_reward", "update_count"]
        }
        
        db.commit()
        logger.info(f"Policy {policy_name} updated for {language}. Current parameters: {policy.parameters}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update policy: {e}")
        return False
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update policy: {e}")
        return False


def get_policy_stats(language: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get current policy statistics for a language
    
    Args:
        language: Language code
        db: Database session
        
    Returns:
        dict: Policy statistics or None if not found
    """
    try:
        from app.models.rl_models import RLPolicy
        
        policy_name = f"sovereign_fusion_{language}"
        policy = db.query(RLPolicy).filter(
            RLPolicy.policy_name == policy_name,
            RLPolicy.is_active == True
        ).first()
        
        if not policy:
            return None
        
        return {
            "policy_name": policy.policy_name,
            "language": policy.language,
            "version": policy.version,
            "total_episodes": policy.total_episodes,
            "average_reward": round(policy.average_reward, 4),
            "parameters": policy.parameters,
            "last_updated": policy.last_updated.isoformat() if policy.last_updated else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get policy stats: {e}")
        return None

