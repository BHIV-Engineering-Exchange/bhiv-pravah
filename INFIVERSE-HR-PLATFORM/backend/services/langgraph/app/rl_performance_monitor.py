"""
RL Performance Monitor for LangGraph Service
Tracks and monitors RL system performance metrics
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import threading

logger = logging.getLogger(__name__)


class RLPerformanceMonitor:
    """Monitor and track RL system performance"""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize performance monitor
        
        Args:
            window_size: Number of recent predictions to keep in memory
        """
        self.window_size = window_size
        self._predictions = deque(maxlen=window_size)
        self._feedback = deque(maxlen=window_size)
        self._lock = threading.Lock()
        
        # Aggregate stats
        self._total_predictions = 0
        self._total_feedback = 0
        self._total_correct = 0
        self._total_reward = 0.0
        self._start_time = datetime.utcnow()
        
        logger.info(f"✅ RL Performance Monitor initialized (window={window_size})")
    
    def record_prediction(self, prediction_time_ms: float, rl_score: float) -> None:
        """
        Record a new RL prediction
        
        Args:
            prediction_time_ms: Time taken for prediction in milliseconds
            rl_score: The calculated RL score
        """
        try:
            with self._lock:
                self._predictions.append({
                    "timestamp": datetime.utcnow(),
                    "prediction_time_ms": prediction_time_ms,
                    "rl_score": rl_score
                })
                self._total_predictions += 1
            
            logger.debug(f"Prediction recorded: {prediction_time_ms:.2f}ms, score={rl_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error recording prediction: {e}")
    
    def record_feedback(self, is_correct: bool, reward_signal: float) -> None:
        """
        Record feedback for a prediction
        
        Args:
            is_correct: Whether the prediction was correct
            reward_signal: The reward signal from feedback
        """
        try:
            with self._lock:
                self._feedback.append({
                    "timestamp": datetime.utcnow(),
                    "is_correct": is_correct,
                    "reward_signal": reward_signal
                })
                self._total_feedback += 1
                if is_correct:
                    self._total_correct += 1
                self._total_reward += reward_signal
            
            logger.debug(f"Feedback recorded: correct={is_correct}, reward={reward_signal:.3f}")
            
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            with self._lock:
                # Calculate window metrics
                recent_predictions = list(self._predictions)
                recent_feedback = list(self._feedback)
            
            # Prediction metrics
            if recent_predictions:
                avg_prediction_time = sum(
                    p['prediction_time_ms'] for p in recent_predictions
                ) / len(recent_predictions)
                avg_rl_score = sum(
                    p['rl_score'] for p in recent_predictions
                ) / len(recent_predictions)
            else:
                avg_prediction_time = 0
                avg_rl_score = 0
            
            # Feedback metrics
            if recent_feedback:
                window_correct = sum(1 for f in recent_feedback if f['is_correct'])
                window_accuracy = window_correct / len(recent_feedback) * 100
                avg_reward = sum(f['reward_signal'] for f in recent_feedback) / len(recent_feedback)
            else:
                window_accuracy = 0
                avg_reward = 0
            
            # Overall metrics
            overall_accuracy = (
                self._total_correct / max(self._total_feedback, 1)
            ) * 100
            
            uptime = datetime.utcnow() - self._start_time
            predictions_per_hour = (
                self._total_predictions / max(uptime.total_seconds() / 3600, 0.1)
            )
            
            metrics = {
                "window_metrics": {
                    "predictions_in_window": len(recent_predictions),
                    "feedback_in_window": len(recent_feedback),
                    "avg_prediction_time_ms": round(avg_prediction_time, 2),
                    "avg_rl_score": round(avg_rl_score, 2),
                    "window_accuracy": round(window_accuracy, 2),
                    "avg_reward": round(avg_reward, 3)
                },
                "overall_metrics": {
                    "total_predictions": self._total_predictions,
                    "total_feedback": self._total_feedback,
                    "total_correct": self._total_correct,
                    "overall_accuracy": round(overall_accuracy, 2),
                    "total_reward": round(self._total_reward, 3),
                    "predictions_per_hour": round(predictions_per_hour, 2)
                },
                "system": {
                    "uptime_seconds": int(uptime.total_seconds()),
                    "uptime_formatted": str(uptime).split('.')[0],
                    "window_size": self.window_size,
                    "start_time": self._start_time.isoformat()
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {"error": str(e)}
    
    def get_prediction_distribution(self) -> Dict[str, int]:
        """Get distribution of prediction scores"""
        try:
            with self._lock:
                predictions = list(self._predictions)
            
            distribution = {
                "shortlist_range": 0,    # 75-100
                "review_range": 0,       # 50-74
                "reject_range": 0        # 0-49
            }
            
            for pred in predictions:
                score = pred['rl_score']
                if score >= 75:
                    distribution["shortlist_range"] += 1
                elif score >= 50:
                    distribution["review_range"] += 1
                else:
                    distribution["reject_range"] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting prediction distribution: {e}")
            return {}
    
    def get_feedback_trend(self, hours: int = 24) -> List[Dict]:
        """Get feedback trend over time"""
        try:
            with self._lock:
                feedback_list = list(self._feedback)
            
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            recent = [f for f in feedback_list if f['timestamp'] >= cutoff]
            
            # Group by hour
            hourly_data = {}
            for fb in recent:
                hour_key = fb['timestamp'].strftime('%Y-%m-%d %H:00')
                if hour_key not in hourly_data:
                    hourly_data[hour_key] = {
                        "correct": 0,
                        "total": 0,
                        "reward_sum": 0
                    }
                hourly_data[hour_key]["total"] += 1
                if fb['is_correct']:
                    hourly_data[hour_key]["correct"] += 1
                hourly_data[hour_key]["reward_sum"] += fb['reward_signal']
            
            trend = []
            for hour, data in sorted(hourly_data.items()):
                trend.append({
                    "hour": hour,
                    "accuracy": round(data["correct"] / max(data["total"], 1) * 100, 2),
                    "avg_reward": round(data["reward_sum"] / max(data["total"], 1), 3),
                    "count": data["total"]
                })
            
            return trend
            
        except Exception as e:
            logger.error(f"Error getting feedback trend: {e}")
            return []
    
    def check_health(self) -> Dict[str, Any]:
        """Check RL system health"""
        try:
            metrics = self.get_metrics()
            
            # Health checks
            issues = []
            status = "healthy"
            
            # Check prediction latency
            avg_time = metrics.get("window_metrics", {}).get("avg_prediction_time_ms", 0)
            if avg_time > 1000:
                issues.append(f"High prediction latency: {avg_time:.0f}ms")
                status = "degraded"
            
            # Check accuracy
            accuracy = metrics.get("window_metrics", {}).get("window_accuracy", 100)
            if accuracy < 50:
                issues.append(f"Low accuracy: {accuracy:.1f}%")
                status = "degraded" if status != "unhealthy" else status
            
            # Check reward trend
            avg_reward = metrics.get("window_metrics", {}).get("avg_reward", 0)
            if avg_reward < -0.3:
                issues.append(f"Negative reward trend: {avg_reward:.3f}")
                status = "degraded" if status != "unhealthy" else status
            
            return {
                "status": status,
                "issues": issues,
                "summary": metrics.get("overall_metrics", {}),
                "checked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking health: {e}")
            return {"status": "unknown", "error": str(e)}
    
    def reset(self) -> None:
        """Reset all metrics (for testing)"""
        with self._lock:
            self._predictions.clear()
            self._feedback.clear()
            self._total_predictions = 0
            self._total_feedback = 0
            self._total_correct = 0
            self._total_reward = 0.0
            self._start_time = datetime.utcnow()
        
        logger.info("Performance monitor reset")


# Global instance
rl_performance_monitor = RLPerformanceMonitor()
