# app/ml/weighted_scoring.py
"""
Weighted Scoring Engine: Combines multiple score sources.

Combines:
1. Rule-based score (traditional InsightFlow logic)
2. Feedback-based score (from Core feedback service)
3. Availability score (agent health/uptime)

Result: Single confidence score (0-1) for routing decisions.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import yaml
import os

logger = logging.getLogger(__name__)


@dataclass
class ScoreComponent:
    """Individual score component"""
    name: str
    score: float
    weight: float
    
    def weighted_value(self) -> float:
        """Get weighted score value"""
        return self.score * self.weight


@dataclass
class ConfidenceScore:
    """Final confidence score with breakdown"""
    final_score: float
    components: Dict[str, ScoreComponent]
    normalization_method: str
    
    def get_breakdown(self) -> Dict[str, Any]:
        """Get human-readable breakdown"""
        return {
            "final_score": self.final_score,
            "components": {
                name: {
                    "score": comp.score,
                    "weight": comp.weight,
                    "weighted_value": comp.weighted_value()
                }
                for name, comp in self.components.items()
            }
        }


class WeightedScoringEngine:
    """
    Engine for combining multiple scoring sources including Karma.
    
    Configuration (from scoring_config.yaml):
    ```yaml
    scoring_weights:
      rule_based: 0.4
      feedback_based: 0.4
      availability: 0.2
    karma_weight: 0.15
    ```
    """
    
    def __init__(
        self, 
        config_path: str = None,
        karma_service: Optional['KarmaServiceClient'] = None
    ):
        """
        Initialize scoring engine with optional Karma service.
        
        Args:
            config_path: Path to scoring configuration YAML (auto-detected if None)
            karma_service: Optional Karma service client
        """
        if config_path is None:
            config_path = self._find_config_path()
        
        self.config = self._load_config(config_path)
        self.weights = self.config.get("scoring_weights", {})
        self.karma_service = karma_service
        
        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(
                f"Scoring weights don't sum to 1.0: {total_weight}. "
                f"Normalizing..."
            )
            self.weights = self._normalize_weights(self.weights)
    
    def calculate_confidence(
        self,
        agent_id: str,
        rule_based_score: float,
        feedback_score: float,
        availability_score: float
    ) -> ConfidenceScore:
        """
        Calculate final confidence score from components.
        
        Args:
            agent_id: Agent identifier
            rule_based_score: Score from traditional rules (0-1)
            feedback_score: Score from Core feedback service (0-1)
            availability_score: Agent availability score (0-1)
        
        Returns:
            ConfidenceScore object
        """
        # Validate inputs
        for score in [rule_based_score, feedback_score, availability_score]:
            if not (0.0 <= score <= 1.0):
                logger.warning(
                    f"Score out of bounds [0-1]: {score}. Clamping..."
                )
        
        # Create score components
        components = {
            "rule_based": ScoreComponent(
                name="rule_based",
                score=self._clamp(rule_based_score),
                weight=self.weights.get("rule_based", 0.33)
            ),
            "feedback_based": ScoreComponent(
                name="feedback_based",
                score=self._clamp(feedback_score),
                weight=self.weights.get("feedback_based", 0.33)
            ),
            "availability": ScoreComponent(
                name="availability",
                score=self._clamp(availability_score),
                weight=self.weights.get("availability", 0.34)
            ),
        }
        
        # Calculate weighted sum
        total_weighted_score = sum(
            component.weighted_value()
            for component in components.values()
        )
        
        # Normalize
        final_score = self._normalize_score(total_weighted_score)
        
        # Log detailed breakdown if enabled
        if self.config.get("logging", {}).get("score_breakdown", False):
            logger.debug(
                f"Calculated confidence for {agent_id}: "
                f"{final_score:.2f} (breakdown: "
                f"rule={components['rule_based'].score:.2f}×{components['rule_based'].weight:.1f}={components['rule_based'].weighted_value():.3f}, "
                f"feedback={components['feedback_based'].score:.2f}×{components['feedback_based'].weight:.1f}={components['feedback_based'].weighted_value():.3f}, "
                f"avail={components['availability'].score:.2f}×{components['availability'].weight:.1f}={components['availability'].weighted_value():.3f})"
            )
        else:
            logger.debug(f"Calculated confidence for {agent_id}: {final_score:.2f}")
        
        return ConfidenceScore(
            final_score=final_score,
            components=components,
            normalization_method="min_max"
        )
    
    async def calculate_confidence_with_karma(
        self,
        agent_id: str,
        rule_based_score: float,
        feedback_score: float,
        availability_score: float
    ) -> ConfidenceScore:
        """
        Calculate final confidence score with Karma weighting.
        
        Args:
            agent_id: Agent identifier
            rule_based_score: Score from traditional rules (0-1)
            feedback_score: Score from Core feedback service (0-1)
            availability_score: Agent availability score (0-1)
        
        Returns:
            ConfidenceScore object with Karma adjustment
        """
        # Get base confidence (without Karma)
        base_confidence = self.calculate_confidence(
            agent_id=agent_id,
            rule_based_score=rule_based_score,
            feedback_score=feedback_score,
            availability_score=availability_score
        )
        
        # Check if Karma is enabled in configuration
        karma_config = self.config.get("karma_weighting", {})
        karma_enabled = karma_config.get("enabled", True)
        
        # If no Karma service or disabled, return base confidence
        if (self.karma_service is None or 
            not self.karma_service.enabled or 
            not karma_enabled):
            return base_confidence
        
        # Fetch Karma score
        try:
            karma_score = await self.karma_service.get_karma_score(agent_id)
            
            # Apply Karma modifier
            # Karma ranges from -1.0 to 1.0
            # Negative Karma decreases confidence, positive increases it
            karma_config = self.config.get("karma_weighting", {})
            karma_weight = karma_config.get("weight", self.config.get("karma_weight", 0.15))  # 15% influence
            
            # Calculate Karma adjustment
            karma_adjustment = karma_score * karma_weight
            
            # Apply adjustment to final score
            adjusted_score = base_confidence.final_score + karma_adjustment
            
            # Clamp to valid range [0, 1]
            adjusted_score = max(0.0, min(1.0, adjusted_score))
            
            # Add Karma component to breakdown
            karma_component = ScoreComponent(
                name="karma_weighted",
                score=karma_score,
                weight=karma_weight
            )
            
            # Create new confidence with Karma
            components = base_confidence.components.copy()
            components["karma_weighted"] = karma_component
            
            adjusted_confidence = ConfidenceScore(
                final_score=adjusted_score,
                components=components,
                normalization_method="karma_adjusted"
            )
            
            logger.debug(
                f"Karma adjustment for {agent_id}: "
                f"karma={karma_score:.2f}, "
                f"base={base_confidence.final_score:.2f}, "
                f"adjusted={adjusted_score:.2f}"
            )
            
            return adjusted_confidence
        
        except Exception as e:
            logger.error(f"Error applying Karma weighting: {str(e)}")
            # Fallback to base confidence
            return base_confidence
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normalize weights to sum to 1.0"""
        total = sum(weights.values())
        if total == 0:
            return {k: 1.0 / len(weights) for k in weights}
        return {k: v / total for k, v in weights.items()}
    
    @staticmethod
    def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp value to range"""
        return max(min_val, min(value, max_val))
    
    def _normalize_score(self, score: float, min_conf: float = None) -> float:
        """
        Robust normalization with boundary handling for edge cases.
        
        Args:
            score: Raw score value
            min_conf: Minimum confidence floor (from config if None)
        
        Returns:
            Normalized score (0-1)
        """
        if min_conf is None:
            min_conf = self.config.get("normalization", {}).get("min_confidence", 0.1)
        
        max_conf = self.config.get("normalization", {}).get("max_confidence", 1.0)
        
        # Handle edge cases
        if score != score:  # NaN check
            logger.warning("NaN score detected, using minimum confidence")
            return min_conf
        
        if score == float('inf'):
            logger.warning("Infinite score detected, using maximum confidence")
            return max_conf
        
        if score == float('-inf'):
            logger.warning("Negative infinite score detected, using minimum confidence")
            return min_conf
        
        # Log if score is significantly out of expected range
        if score > 2.0 or score < -1.0:
            logger.warning(
                f"Score significantly out of expected range [0-1]: {score:.3f}. "
                f"This may indicate a configuration issue."
            )
        
        # Apply sigmoid normalization for extreme values to prevent hard clipping
        if abs(score) > 1.5:
            import math
            # Sigmoid function: 1 / (1 + e^(-x))
            normalized = 1.0 / (1.0 + math.exp(-score))
            logger.debug(f"Applied sigmoid normalization: {score:.3f} -> {normalized:.3f}")
            score = normalized
        
        # Standard clamp to configured range
        clamped = self._clamp(score, 0.0, max_conf)
        
        # Apply minimum confidence floor with validation
        if min_conf > max_conf:
            logger.error(
                f"Invalid config: min_confidence ({min_conf}) > max_confidence ({max_conf}). "
                f"Using defaults."
            )
            min_conf = 0.1
            max_conf = 1.0
        
        floored = max(clamped, min_conf) if min_conf > 0 else clamped
        
        # Final validation
        result = self._clamp(floored, 0.0, max_conf)
        
        # Log normalization details for debugging
        if abs(result - score) > 0.1:
            logger.debug(
                f"Score normalization: {score:.3f} -> {result:.3f} "
                f"(range: [{min_conf:.1f}, {max_conf:.1f}])"
            )
        
        return result
    
    def _find_config_path(self) -> str:
        """Find configuration file in multiple possible locations"""
        # Check environment variable first
        env_path = os.getenv("SCORING_CONFIG_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
            
        possible_paths = [
            "app/config/scoring_config.yaml",
            "config/scoring_config.yaml", 
            "scoring_config.yaml",
            os.path.join(os.path.dirname(__file__), "..", "config", "scoring_config.yaml"),
            os.path.join(os.getcwd(), "app", "config", "scoring_config.yaml")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("No configuration file found in standard locations. Using defaults.")
        return None
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file with fallback to defaults"""
        if config_path is None:
            logger.info("No config path provided, using default configuration")
            return self._default_config()
            
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
                logger.info(f"Loaded scoring configuration from {config_path}")
                return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return self._default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config: {e}. Using defaults.")
            return self._default_config()
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}. Using defaults.")
            return self._default_config()
    
    @staticmethod
    def _default_config() -> Dict:
        """Get default configuration"""
        return {
            "scoring_weights": {
                "rule_based": 0.4,
                "feedback_based": 0.4,
                "availability": 0.2,
            },
            "karma_weight": 0.15,
            "score_sources": {
                "rule_based": {
                    "enabled": True,
                    "fallback_weight": 0.5
                },
                "feedback_based": {
                    "enabled": True,
                    "cache_ttl": 30,
                    "fallback_weight": 0.5
                },
                "availability": {
                    "enabled": True,
                    "timeout_threshold": 5.0
                }
            },
            "normalization": {
                "strategy": "min_max",
                "min_confidence": 0.1,
                "max_confidence": 1.0
            },
            "logging": {
                "level": "DEBUG",
                "score_breakdown": True
            },
            "karma_weighting": {
                "enabled": True,
                "weight": 0.15,
                "cache_ttl": 60,
                "timeout": 5,
                "max_retries": 3
            }
        }


# Global scoring engine instance
_scoring_engine: Optional[WeightedScoringEngine] = None


def get_scoring_engine(karma_service: Optional['KarmaServiceClient'] = None) -> WeightedScoringEngine:
    """Get or create scoring engine instance with optional Karma service"""
    global _scoring_engine
    if _scoring_engine is None:
        # Import here to avoid circular imports
        if karma_service is None:
            try:
                from app.services.karma_service import get_karma_service
                karma_service = get_karma_service()
            except ImportError:
                logger.debug("Karma service not available, continuing without it")
                karma_service = None
        
        try:
            _scoring_engine = WeightedScoringEngine(karma_service=karma_service)
        except Exception as e:
            logger.error(f"Failed to initialize scoring engine: {e}")
            # Create with minimal config as fallback
            _scoring_engine = WeightedScoringEngine(config_path=None, karma_service=None)
    return _scoring_engine