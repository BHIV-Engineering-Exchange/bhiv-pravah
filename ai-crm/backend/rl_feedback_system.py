#!/usr/bin/env python3
"""
Noopur's Rishabh RL Feedback System
Reinforcement Learning with reward/penalty loops for AI agent optimization
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import pickle
import os

class ActionType(Enum):
    """Types of actions that can be evaluated"""
    RESTOCK_DECISION = "restock_decision"
    PROCUREMENT_ORDER = "procurement_order"
    DELIVERY_ROUTING = "delivery_routing"
    INVENTORY_ALLOCATION = "inventory_allocation"
    SUPPLIER_SELECTION = "supplier_selection"
    CUSTOMER_COMMUNICATION = "customer_communication"
    PRICE_OPTIMIZATION = "price_optimization"

class OutcomeType(Enum):
    """Types of outcomes for reward calculation"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"

@dataclass
class RLAction:
    """Represents an action taken by an AI agent"""
    action_id: str
    agent_name: str
    action_type: ActionType
    parameters: Dict
    timestamp: datetime
    confidence_score: float
    context: Dict

@dataclass
class RLOutcome:
    """Represents the outcome of an action"""
    action_id: str
    outcome_type: OutcomeType
    success_metrics: Dict
    cost_metrics: Dict
    time_metrics: Dict
    customer_satisfaction: float
    business_impact: float
    timestamp: datetime

@dataclass
class RLReward:
    """Represents a calculated reward/penalty"""
    action_id: str
    reward_score: float
    reward_components: Dict
    penalty_components: Dict
    net_reward: float
    learning_weight: float

class RLRewardCalculator:
    """Calculates rewards and penalties for actions"""
    
    def __init__(self):
        self.reward_weights = {
            "success_rate": 0.3,
            "cost_efficiency": 0.25,
            "time_efficiency": 0.2,
            "customer_satisfaction": 0.15,
            "business_impact": 0.1
        }
        
        self.penalty_weights = {
            "failure_cost": 0.4,
            "delay_penalty": 0.3,
            "resource_waste": 0.2,
            "customer_dissatisfaction": 0.1
        }
    
    def calculate_reward(self, action: RLAction, outcome: RLOutcome) -> RLReward:
        """Calculate reward/penalty for an action-outcome pair"""
        
        # Calculate reward components
        reward_components = {}
        
        # Success rate reward
        if outcome.outcome_type == OutcomeType.SUCCESS:
            reward_components["success_rate"] = 100 * action.confidence_score
        elif outcome.outcome_type == OutcomeType.PARTIAL_SUCCESS:
            reward_components["success_rate"] = 50 * action.confidence_score
        else:
            reward_components["success_rate"] = 0
        
        # Cost efficiency reward
        expected_cost = action.parameters.get("expected_cost", 1000)
        actual_cost = outcome.cost_metrics.get("actual_cost", expected_cost)
        cost_efficiency = max(0, (expected_cost - actual_cost) / expected_cost * 100)
        reward_components["cost_efficiency"] = cost_efficiency
        
        # Time efficiency reward
        expected_time = action.parameters.get("expected_time_hours", 24)
        actual_time = outcome.time_metrics.get("actual_time_hours", expected_time)
        time_efficiency = max(0, (expected_time - actual_time) / expected_time * 100)
        reward_components["time_efficiency"] = time_efficiency
        
        # Customer satisfaction reward
        reward_components["customer_satisfaction"] = outcome.customer_satisfaction * 20
        
        # Business impact reward
        reward_components["business_impact"] = outcome.business_impact * 10
        
        # Calculate penalty components
        penalty_components = {}
        
        # Failure cost penalty
        if outcome.outcome_type in [OutcomeType.FAILURE, OutcomeType.ERROR]:
            failure_cost = outcome.cost_metrics.get("failure_cost", 0)
            penalty_components["failure_cost"] = failure_cost * 0.1
        
        # Delay penalty
        if actual_time > expected_time:
            delay_hours = actual_time - expected_time
            penalty_components["delay_penalty"] = delay_hours * 5
        
        # Resource waste penalty
        resource_waste = outcome.cost_metrics.get("resource_waste", 0)
        penalty_components["resource_waste"] = resource_waste * 0.05
        
        # Customer dissatisfaction penalty
        if outcome.customer_satisfaction < 3.0:
            penalty_components["customer_dissatisfaction"] = (3.0 - outcome.customer_satisfaction) * 20
        
        # Calculate weighted scores
        total_reward = sum(
            reward_components[component] * self.reward_weights[component]
            for component in reward_components
        )
        
        total_penalty = sum(
            penalty_components.get(component, 0) * self.penalty_weights[component]
            for component in self.penalty_weights
        )
        
        net_reward = total_reward - total_penalty
        
        # Learning weight based on confidence and outcome
        learning_weight = self._calculate_learning_weight(action, outcome)
        
        return RLReward(
            action_id=action.action_id,
            reward_score=total_reward,
            reward_components=reward_components,
            penalty_components=penalty_components,
            net_reward=net_reward,
            learning_weight=learning_weight
        )
    
    def _calculate_learning_weight(self, action: RLAction, outcome: RLOutcome) -> float:
        """Calculate learning weight for the reward"""
        base_weight = 1.0
        
        # Higher weight for unexpected outcomes
        if action.confidence_score > 0.8 and outcome.outcome_type == OutcomeType.FAILURE:
            base_weight *= 2.0  # Learn more from confident failures
        elif action.confidence_score < 0.5 and outcome.outcome_type == OutcomeType.SUCCESS:
            base_weight *= 1.5  # Learn more from uncertain successes
        
        # Higher weight for high-impact actions
        if outcome.business_impact > 7.0:
            base_weight *= 1.3
        
        return min(base_weight, 3.0)  # Cap at 3x weight

class RLAgentOptimizer:
    """Optimizes agent behavior based on RL feedback"""
    
    def __init__(self):
        self.agent_performance = {}
        self.action_patterns = {}
        self.optimization_rules = {}
        self.load_learning_data()
    
    def update_agent_performance(self, agent_name: str, reward: RLReward):
        """Update agent performance metrics"""
        if agent_name not in self.agent_performance:
            self.agent_performance[agent_name] = {
                "total_actions": 0,
                "total_reward": 0,
                "average_reward": 0,
                "success_rate": 0,
                "recent_rewards": [],
                "improvement_trend": 0
            }
        
        perf = self.agent_performance[agent_name]
        perf["total_actions"] += 1
        perf["total_reward"] += reward.net_reward
        perf["average_reward"] = perf["total_reward"] / perf["total_actions"]
        
        # Track recent rewards for trend analysis
        perf["recent_rewards"].append(reward.net_reward)
        if len(perf["recent_rewards"]) > 20:
            perf["recent_rewards"].pop(0)
        
        # Calculate improvement trend
        if len(perf["recent_rewards"]) >= 10:
            recent_avg = np.mean(perf["recent_rewards"][-10:])
            older_avg = np.mean(perf["recent_rewards"][-20:-10]) if len(perf["recent_rewards"]) >= 20 else recent_avg
            perf["improvement_trend"] = (recent_avg - older_avg) / max(abs(older_avg), 1)
    
    def generate_optimization_suggestions(self, agent_name: str) -> List[str]:
        """Generate optimization suggestions for an agent"""
        suggestions = []
        
        if agent_name not in self.agent_performance:
            return ["No performance data available for analysis"]
        
        perf = self.agent_performance[agent_name]
        
        # Performance-based suggestions
        if perf["average_reward"] < 0:
            suggestions.append("Agent showing negative average reward - review decision criteria")
        
        if perf["improvement_trend"] < -0.1:
            suggestions.append("Performance declining - consider retraining or parameter adjustment")
        elif perf["improvement_trend"] > 0.1:
            suggestions.append("Performance improving - current strategy is effective")
        
        # Pattern-based suggestions
        if agent_name in self.action_patterns:
            patterns = self.action_patterns[agent_name]
            
            if patterns.get("high_confidence_failures", 0) > 3:
                suggestions.append("Reduce confidence threshold - overconfident decisions failing")
            
            if patterns.get("low_confidence_successes", 0) > 5:
                suggestions.append("Increase confidence threshold - underestimating success probability")
        
        return suggestions if suggestions else ["Agent performance is stable"]
    
    def get_recommended_parameters(self, agent_name: str, action_type: ActionType) -> Dict:
        """Get recommended parameters for an action type"""
        base_params = {
            "confidence_threshold": 0.7,
            "risk_tolerance": 0.5,
            "optimization_weight": 1.0
        }
        
        if agent_name in self.agent_performance:
            perf = self.agent_performance[agent_name]
            
            # Adjust confidence threshold based on performance
            if perf["improvement_trend"] < -0.1:
                base_params["confidence_threshold"] = min(0.9, base_params["confidence_threshold"] + 0.1)
            elif perf["improvement_trend"] > 0.1:
                base_params["confidence_threshold"] = max(0.5, base_params["confidence_threshold"] - 0.05)
            
            # Adjust risk tolerance
            if perf["average_reward"] > 50:
                base_params["risk_tolerance"] = min(0.8, base_params["risk_tolerance"] + 0.1)
            elif perf["average_reward"] < 0:
                base_params["risk_tolerance"] = max(0.2, base_params["risk_tolerance"] - 0.1)
        
        return base_params
    
    def save_learning_data(self):
        """Save learning data to file"""
        try:
            os.makedirs("data/rl_learning", exist_ok=True)
            
            with open("data/rl_learning/agent_performance.json", "w") as f:
                # Convert numpy arrays to lists for JSON serialization
                serializable_data = {}
                for agent, perf in self.agent_performance.items():
                    serializable_data[agent] = {
                        k: v.tolist() if isinstance(v, np.ndarray) else v
                        for k, v in perf.items()
                    }
                json.dump(serializable_data, f, indent=2)
            
            with open("data/rl_learning/action_patterns.json", "w") as f:
                json.dump(self.action_patterns, f, indent=2)
                
        except Exception as e:
            print(f"[ERROR] Failed to save learning data: {e}")
    
    def load_learning_data(self):
        """Load learning data from file"""
        try:
            if os.path.exists("data/rl_learning/agent_performance.json"):
                with open("data/rl_learning/agent_performance.json", "r") as f:
                    self.agent_performance = json.load(f)
            
            if os.path.exists("data/rl_learning/action_patterns.json"):
                with open("data/rl_learning/action_patterns.json", "r") as f:
                    self.action_patterns = json.load(f)
                    
        except Exception as e:
            print(f"[WARNING] Failed to load learning data: {e}")

class RLFeedbackSystem:
    """Main RL feedback system coordinator"""
    
    def __init__(self):
        self.reward_calculator = RLRewardCalculator()
        self.optimizer = RLAgentOptimizer()
        self.action_history = []
        self.outcome_history = []
        self.reward_history = []
    
    def record_action(self, agent_name: str, action_type: ActionType, parameters: Dict, 
                     confidence_score: float, context: Dict = None) -> str:
        """Record an action taken by an agent"""
        action_id = f"{agent_name}_{action_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        action = RLAction(
            action_id=action_id,
            agent_name=agent_name,
            action_type=action_type,
            parameters=parameters,
            timestamp=datetime.now(),
            confidence_score=confidence_score,
            context=context or {}
        )
        
        self.action_history.append(action)
        print(f"[RL] Recorded action: {action_id}")
        return action_id
    
    def record_outcome(self, action_id: str, outcome_type: OutcomeType, 
                      success_metrics: Dict, cost_metrics: Dict, time_metrics: Dict,
                      customer_satisfaction: float, business_impact: float):
        """Record the outcome of an action"""
        outcome = RLOutcome(
            action_id=action_id,
            outcome_type=outcome_type,
            success_metrics=success_metrics,
            cost_metrics=cost_metrics,
            time_metrics=time_metrics,
            customer_satisfaction=customer_satisfaction,
            business_impact=business_impact,
            timestamp=datetime.now()
        )
        
        self.outcome_history.append(outcome)
        
        # Find corresponding action and calculate reward
        action = next((a for a in self.action_history if a.action_id == action_id), None)
        if action:
            reward = self.reward_calculator.calculate_reward(action, outcome)
            self.reward_history.append(reward)
            self.optimizer.update_agent_performance(action.agent_name, reward)
            
            print(f"[RL] Calculated reward for {action_id}: {reward.net_reward:.2f}")
            return reward
        else:
            print(f"[RL] Warning: No action found for outcome {action_id}")
            return None
    
    def get_agent_insights(self, agent_name: str) -> Dict:
        """Get insights and recommendations for an agent"""
        performance = self.optimizer.agent_performance.get(agent_name, {})
        suggestions = self.optimizer.generate_optimization_suggestions(agent_name)
        
        return {
            "performance_metrics": performance,
            "optimization_suggestions": suggestions,
            "recommended_parameters": self.optimizer.get_recommended_parameters(agent_name, ActionType.RESTOCK_DECISION)
        }
    
    def get_system_analytics(self) -> Dict:
        """Get system-wide RL analytics"""
        total_actions = len(self.action_history)
        total_rewards = sum(r.net_reward for r in self.reward_history)
        avg_reward = total_rewards / max(total_actions, 1)
        
        # Agent rankings
        agent_rankings = []
        for agent_name, perf in self.optimizer.agent_performance.items():
            agent_rankings.append({
                "agent_name": agent_name,
                "average_reward": perf["average_reward"],
                "total_actions": perf["total_actions"],
                "improvement_trend": perf["improvement_trend"]
            })
        
        agent_rankings.sort(key=lambda x: x["average_reward"], reverse=True)
        
        return {
            "total_actions": total_actions,
            "total_rewards": total_rewards,
            "average_reward": avg_reward,
            "agent_rankings": agent_rankings,
            "learning_progress": self._calculate_learning_progress()
        }
    
    def _calculate_learning_progress(self) -> Dict:
        """Calculate overall learning progress"""
        if len(self.reward_history) < 10:
            return {"status": "insufficient_data", "progress": 0}
        
        recent_rewards = [r.net_reward for r in self.reward_history[-20:]]
        older_rewards = [r.net_reward for r in self.reward_history[-40:-20]] if len(self.reward_history) >= 40 else recent_rewards
        
        recent_avg = np.mean(recent_rewards)
        older_avg = np.mean(older_rewards)
        
        progress = (recent_avg - older_avg) / max(abs(older_avg), 1)
        
        if progress > 0.1:
            status = "improving"
        elif progress < -0.1:
            status = "declining"
        else:
            status = "stable"
        
        return {
            "status": status,
            "progress": progress,
            "recent_average": recent_avg,
            "older_average": older_avg
        }

# Global RL feedback system instance
rl_feedback_system = RLFeedbackSystem()

# Convenience functions for integration
def record_agent_action(agent_name: str, action_type: str, parameters: Dict, 
                       confidence_score: float, context: Dict = None) -> str:
    """Record an agent action for RL feedback"""
    action_enum = ActionType(action_type)
    return rl_feedback_system.record_action(agent_name, action_enum, parameters, confidence_score, context)

def record_action_outcome(action_id: str, success: bool, cost_actual: float, cost_expected: float,
                         time_actual: float, time_expected: float, customer_rating: float = 4.0,
                         business_impact: float = 5.0):
    """Record the outcome of an action"""
    outcome_type = OutcomeType.SUCCESS if success else OutcomeType.FAILURE
    
    success_metrics = {"success": success}
    cost_metrics = {"actual_cost": cost_actual, "expected_cost": cost_expected}
    time_metrics = {"actual_time_hours": time_actual, "expected_time_hours": time_expected}
    
    return rl_feedback_system.record_outcome(
        action_id, outcome_type, success_metrics, cost_metrics, 
        time_metrics, customer_rating, business_impact
    )

def get_agent_recommendations(agent_name: str) -> Dict:
    """Get RL-based recommendations for an agent"""
    return rl_feedback_system.get_agent_insights(agent_name)

def get_rl_analytics() -> Dict:
    """Get RL system analytics"""
    return rl_feedback_system.get_system_analytics()

if __name__ == "__main__":
    print("[INFO] Testing RL Feedback System...")
    
    # Test restock agent
    action_id1 = record_agent_action(
        "restock_agent", 
        "restock_decision", 
        {"product_id": "A101", "quantity": 50, "expected_cost": 1000, "expected_time": 24},
        0.85
    )
    
    # Simulate successful outcome
    record_action_outcome(action_id1, True, 950, 1000, 20, 24, 4.5, 7.0)
    
    # Test procurement agent
    action_id2 = record_agent_action(
        "procurement_agent",
        "procurement_order",
        {"supplier": "TechParts", "amount": 5000, "expected_cost": 5000, "expected_time": 48},
        0.75
    )
    
    # Simulate delayed outcome
    record_action_outcome(action_id2, True, 5200, 5000, 60, 48, 3.5, 6.0)
    
    # Get insights
    insights = get_agent_recommendations("restock_agent")
    print(f"[RL] Restock agent insights: {insights}")
    
    analytics = get_rl_analytics()
    print(f"[RL] System analytics: {analytics}")
    
    print("[SUCCESS] RL Feedback System test completed")