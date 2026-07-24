# app/ml/q_learning_updater.py
"""
Q-Learning Update Module

Handles Q-learning updates based on reward signals.
Integrates with existing routing confidence scores.
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class QLearningUpdater:
    """
    Q-Learning update handler.
    
    Features:
    - Q-value updates based on reward signals
    - Learning rate and discount factor
    - Safety bounds on updates
    - Logging of confidence changes
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        enable_updates: bool = False,
        enable_karma_weighting: bool = False
    ):
        """
        Initialize Q-learning updater.
        
        Args:
            learning_rate: Alpha (0-1)
            discount_factor: Gamma (0-1)
            enable_updates: Toggle for Q-learning updates
            enable_karma_weighting: Toggle for karma weighting
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.enable_updates = enable_updates
        self.enable_karma_weighting = enable_karma_weighting
        
        # Q-table: {(state, action): q_value}
        self.q_table: Dict[Tuple[str, str], float] = {}
        
        # Learning trace log
        self.learning_trace = []
        
        logger.info(
            f"QLearningUpdater initialized "
            f"(lr={learning_rate}, gamma={discount_factor}, "
            f"updates_enabled={enable_updates})"
        )
    
    def q_update(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: Optional[str] = None,
        request_id: Optional[str] = None,
        karma_score: Optional[float] = None  # ADD this parameter
    ) -> Tuple[float, float]:
        """
        Perform Q-learning update with karma-weighted smoothing.
        
        Args:
            state: Current state identifier
            action: Action taken (agent selected)
            reward: Base reward signal (-1 to 1)
            next_state: Optional next state
            request_id: Request identifier for logging
            karma_score: Optional karma score for smoothing (-1 to 1)
        
        Returns:
            Tuple of (old_confidence, new_confidence)
        """
        if not self.enable_updates:
            logger.debug("Q-updates disabled, skipping")
            return (0.0, 0.0)
        
        try:
            # PHASE 3.1: Apply karma-weighted reward smoothing
            if self.enable_karma_weighting and karma_score is not None:
                # Normalize karma score to [0, 1] range
                karma_normalized = (karma_score + 1.0) / 2.0
                
                # Weighted smoothing formula:
                # adjusted_reward = 0.75 * q_reward + 0.25 * karma_normalized
                adjusted_reward = (0.75 * reward) + (0.25 * karma_normalized)
                
                # Clamp to valid range [-1, 1]
                adjusted_reward = max(-1.0, min(1.0, adjusted_reward))
                
                logger.debug(
                    f"Reward smoothing: base={reward:.2f}, "
                    f"karma={karma_score:.2f}, "
                    f"adjusted={adjusted_reward:.2f}"
                )
                
                # Use adjusted reward for Q-update
                reward = adjusted_reward
            
            # Get current Q-value
            state_action = (state, action)
            old_q_value = self.q_table.get(state_action, 0.5)  # Default 0.5
            
            # Calculate max Q-value for next state
            max_next_q = 0.5  # Default if no next state
            if next_state:
                next_actions = self._get_actions_for_state(next_state)
                if next_actions:
                    max_next_q = max(
                        self.q_table.get((next_state, a), 0.5)
                        for a in next_actions
                    )
            
            # Q-learning update formula:
            # Q(s,a) = Q(s,a) + α * [r + γ * max(Q(s',a')) - Q(s,a)]
            td_error = reward + self.discount_factor * max_next_q - old_q_value
            new_q_value = old_q_value + self.learning_rate * td_error
            
            # Clamp to valid range [0, 1]
            new_q_value = max(0.0, min(1.0, new_q_value))
            
            # Check for NaN/infinity
            if not (0.0 <= new_q_value <= 1.0):
                logger.warning(f"Invalid Q-value: {new_q_value}, resetting to 0.5")
                new_q_value = 0.5
            
            # Update Q-table
            self.q_table[state_action] = new_q_value
            
            # Log update
            self._log_update(
                request_id=request_id or "unknown",
                state=state,
                action=action,
                reward=reward,
                old_conf=old_q_value,
                new_conf=new_q_value
            )
            
            logger.info(
                f"Q-update: {state}->{action}, "
                f"reward={reward:.2f}, "
                f"conf: {old_q_value:.3f} → {new_q_value:.3f}"
            )
            
            return (old_q_value, new_q_value)
        
        except Exception as e:
            logger.error(f"Error in Q-update: {str(e)}")
            return (0.5, 0.5)
    
    def get_q_value(self, state: str, action: str) -> float:
        """
        Get Q-value for state-action pair.
        
        Args:
            state: State identifier
            action: Action identifier
        
        Returns:
            Q-value (0-1)
        """
        return self.q_table.get((state, action), 0.5)
    
    def _get_actions_for_state(self, state: str) -> list:
        """Get all actions seen for a state"""
        return [
            action for (s, action) in self.q_table.keys()
            if s == state
        ]
    
    def _log_update(
        self,
        request_id: str,
        state: str,
        action: str,
        reward: float,
        old_conf: float,
        new_conf: float
    ):
        """Log Q-learning update for traceability"""
        trace_entry = {
            "request_id": request_id,
            "state": state,
            "action": action,
            "reward": reward,
            "old_conf": old_conf,
            "new_conf": new_conf,
            "ts": datetime.utcnow().isoformat() + "Z"
        }
        
        self.learning_trace.append(trace_entry)
        
        # Keep last 1000 entries
        if len(self.learning_trace) > 1000:
            self.learning_trace = self.learning_trace[-1000:]
    
    def get_learning_trace(self, limit: int = 100) -> list:
        """Get recent learning trace"""
        return self.learning_trace[-limit:]
    
    def save_q_table(self, filepath: str = "q_table.json"):
        """Save Q-table to file"""
        try:
            # Convert tuple keys to strings
            serializable = {
                f"{s}|{a}": v
                for (s, a), v in self.q_table.items()
            }
            
            Path(filepath).write_text(json.dumps(serializable, indent=2))
            logger.info(f"Saved Q-table to {filepath}")
        
        except Exception as e:
            logger.error(f"Error saving Q-table: {str(e)}")
    
    def load_q_table(self, filepath: str = "q_table.json"):
        """Load Q-table from file"""
        try:
            data = json.loads(Path(filepath).read_text())
            
            # Convert string keys back to tuples
            self.q_table = {
                tuple(k.split("|")): v
                for k, v in data.items()
            }
            
            logger.info(f"Loaded Q-table from {filepath} ({len(self.q_table)} entries)")
        
        except Exception as e:
            logger.error(f"Error loading Q-table: {str(e)}")


# Global Q-learning updater instance
_q_updater: Optional[QLearningUpdater] = None


def get_q_updater() -> QLearningUpdater:
    """Get or create global Q-learning updater instance"""
    global _q_updater
    
    if _q_updater is None:
        from app.core.config import settings
        
        _q_updater = QLearningUpdater(
            learning_rate=getattr(settings, 'Q_LEARNING_RATE', settings.LEARNING_RATE),
            discount_factor=getattr(settings, 'Q_DISCOUNT_FACTOR', settings.DISCOUNT_FACTOR),
            enable_updates=getattr(settings, 'ENABLE_Q_UPDATES', False),
            enable_karma_weighting=getattr(settings, 'ENABLE_KARMA_WEIGHTING', False)
        )
    
    return _q_updater