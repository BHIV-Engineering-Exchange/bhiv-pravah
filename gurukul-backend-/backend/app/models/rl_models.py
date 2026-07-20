"""
Reinforcement Learning Models

Database models for storing RL rewards and episodes from the Sovereign Fusion Layer.
Tracks rewards from LM output, KSML labels, and Vaani user feedback.
"""

from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class RLEpisode(Base):
    """
    RL Episode - Represents a single inference run through the pipeline
    
    Each episode contains multiple rewards from different sources (LM, KSML, Vaani)
    """
    __tablename__ = "rl_episodes"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    episode_id = Column(String, unique=True, index=True, nullable=False)  # External episode ID
    source_text = Column(Text, nullable=False)
    target_lang = Column(String, nullable=False)  # e.g., 'ar'
    tone = Column(String, nullable=True)
    
    # Pipeline outputs
    lm_output = Column(Text, nullable=True)
    ksml_labels = Column(JSON, nullable=True)
    prosody_hint = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    metadata_ = Column("metadata", JSON, default={})
    
    # Relationship to rewards
    rewards = relationship("RLReward", back_populates="episode", cascade="all, delete-orphan")


class RLReward(Base):
    """
    RL Reward - Individual reward from a specific source
    
    Sources: 'lm_core', 'ksml', 'vaani', 'user_feedback'
    """
    __tablename__ = "rl_rewards"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    episode_id = Column(String, ForeignKey("rl_episodes.id"), nullable=False, index=True)
    
    # Reward details
    source = Column(String, nullable=False, index=True)  # 'lm_core', 'ksml', 'vaani', 'user_feedback'
    reward_value = Column(Float, nullable=False)  # Reward score (typically 0.0 to 1.0)
    reward_type = Column(String, nullable=False)  # 'quality', 'accuracy', 'user_satisfaction', etc.
    
    # Context
    context = Column(JSON, nullable=True)  # Additional context about the reward
    feedback_text = Column(Text, nullable=True)  # User feedback if applicable
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    episode = relationship("RLEpisode", back_populates="rewards")


class RLPolicy(Base):
    """
    RL Policy - Stores current policy state and parameters
    
    Updated based on accumulated rewards from episodes
    """
    __tablename__ = "rl_policies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    policy_name = Column(String, unique=True, nullable=False, index=True)  # e.g., 'sovereign_fusion_v1'
    language = Column(String, nullable=False, index=True)  # e.g., 'ar'
    
    # Policy parameters (stored as JSON for flexibility)
    parameters = Column(JSON, nullable=False, default={})
    
    # Statistics
    total_episodes = Column(Float, default=0.0)
    average_reward = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Version tracking
    version = Column(String, nullable=False, default="1.0.0")
    is_active = Column(Boolean, default=True)

