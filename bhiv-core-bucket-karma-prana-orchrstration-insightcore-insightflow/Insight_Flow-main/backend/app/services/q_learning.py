import numpy as np
from typing import Dict, Tuple, Optional, List
import logging
from datetime import datetime
from app.core.config import settings
from app.core.database import get_db
import json
import atexit

logger = logging.getLogger(__name__)


class QLearningRouter:
    """Q-Learning based routing engine"""
    
    def __init__(
        self,
        learning_rate: float = None,
        discount_factor: float = None,
        epsilon: float = None,
        min_epsilon: float = None,
        epsilon_decay: float = None
    ):
        """
        Initialize Q-Learning router
        
        Args:
            learning_rate: Learning rate (alpha)
            discount_factor: Discount factor (gamma)
            epsilon: Exploration rate
            min_epsilon: Minimum epsilon value
            epsilon_decay: Epsilon decay rate
        """
        self.learning_rate = learning_rate or settings.LEARNING_RATE
        self.discount_factor = discount_factor or settings.DISCOUNT_FACTOR
        self.epsilon = epsilon or settings.EPSILON
        self.min_epsilon = min_epsilon or settings.MIN_EPSILON
        self.epsilon_decay = epsilon_decay or settings.EPSILON_DECAY
        
        # Q-table: {(state, action): q_value}
        self.q_table: Dict[Tuple[str, str], float] = {}
        
        # Persistence tracking
        self._unsaved_updates = 0
        self._save_threshold = 10  # Save after 10 updates
        self._last_save_time = datetime.now()
        self._save_interval = 300  # Save every 5 minutes
        
        # Load existing Q-table from database
        self._load_q_table()
        
        logger.info(f"Q-Learning router initialized with lr={self.learning_rate}, "
                   f"gamma={self.discount_factor}, epsilon={self.epsilon}")
        
        # Register cleanup on exit
        atexit.register(self.force_save_q_table)
    
    def _load_q_table(self):
        """Load Q-table from database"""
        try:
            db = get_db()
            result = db.table("q_learning_table").select("*").execute()
            
            if result.data:
                for row in result.data:
                    state = row['state']
                    action = row['action']
                    q_value = row['q_value']
                    self.q_table[(state, action)] = q_value
                
                logger.info(f"Loaded {len(self.q_table)} Q-table entries from database")
        except Exception as e:
            logger.warning(f"Could not load Q-table: {e}. Starting with empty Q-table.")
    
    def _save_q_table(self, force: bool = False):
        """Save Q-table to database with crash-safe mechanism"""
        try:
            db = get_db()
            
            # Convert Q-table to list of records
            records = [
                {
                    "state": state,
                    "action": action,
                    "q_value": q_value
                }
                for (state, action), q_value in self.q_table.items()
            ]
            
            # Batch upsert to database
            if records:
                db.table("q_learning_table").upsert(records).execute()
                self._unsaved_updates = 0
                self._last_save_time = datetime.now()
                logger.info(f"Saved {len(records)} Q-table entries to database")
        except Exception as e:
            logger.error(f"Failed to save Q-table: {e}")
    
    def _check_and_save_q_table(self):
        """Check if Q-table should be saved based on updates or time"""
        current_time = datetime.now()
        time_since_save = (current_time - self._last_save_time).total_seconds()
        
        # Save if threshold reached or time interval exceeded
        if (self._unsaved_updates >= self._save_threshold or 
            time_since_save >= self._save_interval):
            self._save_q_table()
    
    def force_save_q_table(self):
        """Force immediate save of Q-table (for shutdown/critical updates)"""
        if self._unsaved_updates > 0:
            self._save_q_table(force=True)
            logger.info("Force saved Q-table due to critical update")
    
    def _get_state_representation(self, context: Dict) -> str:
        """
        Convert context to enhanced state representation
        
        Args:
            context: Request context dictionary
            
        Returns:
            State string representation
        """
        # Enhanced state features
        input_type = str(context.get("input_type", "unknown"))[:10]
        priority = str(context.get("priority", "normal"))[:8]
        domain = str(context.get("domain", "general"))[:10]
        
        # Time-based features
        import datetime
        hour = datetime.datetime.now().hour
        time_period = "night" if hour < 6 or hour > 22 else "day"
        
        # User context features
        has_user_id = "user_id" in context
        user_type = "returning" if has_user_id else "new"
        
        # Request complexity indicators
        complexity = "high" if context.get("preferences", {}).get("min_confidence", 0) > 0.8 else "normal"
        
        # Agent load balancing hint
        load_hint = context.get("load_balancing", "balanced")
        
        # Sanitize and combine features
        features = [input_type, priority, domain, time_period, user_type, complexity, load_hint]
        sanitized = [f.replace('_', '').replace('|', '') for f in features]
        
        return "|".join(sanitized)
    
    def select_agent(
        self,
        available_agents: List[str],
        context: Dict,
        explore: bool = True
    ) -> Tuple[str, float]:
        """
        Select agent using epsilon-greedy policy
        
        Args:
            available_agents: List of available agent IDs
            context: Request context
            explore: Whether to use exploration
            
        Returns:
            Tuple of (selected_agent_id, confidence_score)
        """
        if not available_agents:
            raise ValueError("No available agents for routing")
        
        state = self._get_state_representation(context)
        
        # Epsilon-greedy action selection
        if explore and np.random.random() < self.epsilon:
            # Exploration: random agent
            selected_agent = np.random.choice(available_agents)
            confidence = 0.5  # Low confidence for random selection
            logger.debug(f"Exploration: Selected random agent {selected_agent}")
        else:
            # Exploitation: best known agent
            q_values = {
                agent: self.q_table.get((state, agent), 0.0)
                for agent in available_agents
            }
            
            selected_agent = max(q_values, key=q_values.get)
            confidence = min(1.0, max(0.0, q_values[selected_agent]))
            logger.debug(f"Exploitation: Selected agent {selected_agent} with Q-value {q_values[selected_agent]}")
        
        return selected_agent, confidence
    
    def update_q_value(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str,
        available_next_actions: List[str]
    ):
        """
        Update Q-value using Q-learning update rule
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            available_next_actions: Available actions in next state
        """
        # Get current Q-value
        current_q = self.q_table.get((state, action), 0.0)
        
        # Get max Q-value for next state
        if available_next_actions:
            max_next_q = max(
                [self.q_table.get((next_state, a), 0.0) for a in available_next_actions]
            )
        else:
            max_next_q = 0.0
        
        # Q-learning update rule
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[(state, action)] = new_q
        
        logger.debug(f"Updated Q({state}, {action}): {current_q:.3f} -> {new_q:.3f} "
                    f"(reward={reward:.3f})")
        
        # Decay epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        # Track unsaved updates
        self._unsaved_updates += 1
        
        # Event-driven persistence
        self._check_and_save_q_table()
    
    def process_feedback(
        self,
        routing_log_id: str,
        feedback: Dict,
        context: Dict,
        available_agents: List[str]
    ):
        """
        Process feedback and update Q-table
        
        Args:
            routing_log_id: ID of routing log
            feedback: Feedback data
            context: Original request context
            available_agents: List of available agents
        """
        state = self._get_state_representation(context)
        action = feedback.get("agent_id")
        
        if not action:
            logger.warning(f"No agent_id in feedback for routing {routing_log_id}")
            return
        
        # Calculate reward based on feedback
        reward = self._calculate_reward(feedback)
        
        # Assume next state is similar to current (simplified)
        next_state = state
        
        # Update Q-value
        self.update_q_value(state, action, reward, next_state, available_agents)
        
        logger.info(f"Processed feedback for routing {routing_log_id}: "
                   f"reward={reward:.3f}, epsilon={self.epsilon:.3f}")
    
    def _calculate_reward(self, feedback: Dict) -> float:
        """
        Calculate reward from feedback
        
        Args:
            feedback: Feedback dictionary
            
        Returns:
            Reward value between -1 and 1
        """
        if not feedback.get("success"):
            return -1.0
        
        # Positive reward based on multiple factors
        accuracy = feedback.get("accuracy_score", 0.5)
        
        # Latency penalty (assume target is 200ms)
        latency_ms = feedback.get("latency_ms", 200)
        latency_penalty = min(1.0, latency_ms / 200.0) * 0.2
        
        # User satisfaction bonus
        satisfaction = feedback.get("user_satisfaction", 3) / 5.0
        
        reward = (0.5 * accuracy) + (0.3 * satisfaction) - (0.2 * latency_penalty)
        
        return np.clip(reward, -1.0, 1.0)
    
    def _extract_state_features(self, state: str) -> Dict:
        """Extract features from state string for analysis"""
        try:
            parts = state.split("|")
            if len(parts) >= 7:
                return {
                    "input_type": parts[0],
                    "priority": parts[1], 
                    "domain": parts[2],
                    "time_period": parts[3],
                    "user_type": parts[4],
                    "complexity": parts[5],
                    "load_hint": parts[6]
                }
        except:
            pass
        return {"raw_state": state}
    
    def get_statistics(self) -> Dict:
        """Get enhanced Q-learning statistics"""
        states = set(state for state, _ in self.q_table.keys())
        
        # Analyze state distribution
        state_features = {}
        for state in states:
            features = self._extract_state_features(state)
            for key, value in features.items():
                if key not in state_features:
                    state_features[key] = {}
                state_features[key][value] = state_features[key].get(value, 0) + 1
        
        return {
            "q_table_size": len(self.q_table),
            "epsilon": self.epsilon,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "states_explored": len(states),
            "avg_q_value": np.mean(list(self.q_table.values())) if self.q_table else 0.0,
            "state_feature_distribution": state_features
        }


# Global Q-learning router instance
q_learning_router = QLearningRouter()

# Alias for service import compatibility
q_learning_service = q_learning_router