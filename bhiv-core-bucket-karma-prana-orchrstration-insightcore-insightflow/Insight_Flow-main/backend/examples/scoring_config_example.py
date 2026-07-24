"""
Example: Scoring Configuration Usage

Demonstrates how to use and customize the weighted scoring configuration
for different deployment scenarios and requirements.
"""

import logging
from app.ml.weighted_scoring import WeightedScoringEngine, get_scoring_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_scoring_configurations():
    """Demonstrate different scoring configurations"""
    
    print("=== Scoring Configuration Demo ===\n")
    
    # 1. Default configuration
    print("1. Default Configuration:")
    default_engine = get_scoring_engine()
    
    print(f"   Weights: {default_engine.weights}")
    print(f"   Config keys: {list(default_engine.config.keys())}")
    
    # Test with default config
    result = default_engine.calculate_confidence(
        agent_id="demo-agent",
        rule_based_score=0.8,
        feedback_score=0.9,
        availability_score=0.95
    )
    
    print(f"   Sample score: {result.final_score:.3f}")
    print()
    
    # 2. Custom weight scenarios
    print("2. Custom Weight Scenarios:")
    
    scenarios = [
        {
            "name": "Feedback-Heavy",
            "weights": {"rule_based": 0.2, "feedback_based": 0.6, "availability": 0.2},
            "description": "Prioritizes user feedback over rules"
        },
        {
            "name": "Rule-Heavy", 
            "weights": {"rule_based": 0.7, "feedback_based": 0.2, "availability": 0.1},
            "description": "Prioritizes traditional routing rules"
        },
        {
            "name": "Availability-Critical",
            "weights": {"rule_based": 0.3, "feedback_based": 0.3, "availability": 0.4},
            "description": "Prioritizes agent availability/health"
        }
    ]
    
    test_scores = {
        "rule_based_score": 0.7,
        "feedback_score": 0.9,
        "availability_score": 0.8
    }
    
    for scenario in scenarios:
        # Create temporary engine with custom weights
        temp_engine = WeightedScoringEngine()
        temp_engine.weights = scenario["weights"]
        
        result = temp_engine.calculate_confidence(
            agent_id="test-agent",
            **test_scores
        )
        
        print(f"   {scenario['name']}: {result.final_score:.3f}")
        print(f"     - {scenario['description']}")
        print(f"     - Weights: {scenario['weights']}")
        
        # Show breakdown
        breakdown = result.get_breakdown()
        for comp_name, comp_data in breakdown["components"].items():
            print(f"       {comp_name}: {comp_data['score']:.2f} × {comp_data['weight']:.1f} = {comp_data['weighted_value']:.3f}")
        print()
    
    # 3. Configuration validation
    print("3. Configuration Validation:")
    
    # Test weight normalization
    invalid_weights = {"rule_based": 0.6, "feedback_based": 0.8, "availability": 0.4}  # Sum = 1.8
    print(f"   Invalid weights (sum={sum(invalid_weights.values()):.1f}): {invalid_weights}")
    
    temp_engine = WeightedScoringEngine()
    normalized = temp_engine._normalize_weights(invalid_weights)
    print(f"   Normalized weights (sum={sum(normalized.values()):.1f}): {normalized}")
    print()
    
    # 4. Score boundary testing
    print("4. Score Boundary Testing:")
    
    boundary_tests = [
        {"name": "Perfect Scores", "scores": (1.0, 1.0, 1.0)},
        {"name": "Zero Scores", "scores": (0.0, 0.0, 0.0)},
        {"name": "Out of Bounds", "scores": (1.5, -0.2, 0.8)},
        {"name": "Mixed Range", "scores": (0.3, 0.7, 0.9)}
    ]
    
    for test in boundary_tests:
        rule_score, feedback_score, avail_score = test["scores"]
        
        result = default_engine.calculate_confidence(
            agent_id="boundary-test",
            rule_based_score=rule_score,
            feedback_score=feedback_score,
            availability_score=avail_score
        )
        
        print(f"   {test['name']}: Input({rule_score}, {feedback_score}, {avail_score}) → {result.final_score:.3f}")
        
        # Show clamped values
        components = result.components
        clamped = (
            components["rule_based"].score,
            components["feedback_based"].score, 
            components["availability"].score
        )
        print(f"     Clamped: {clamped}")
    
    print()
    
    # 5. Configuration file structure
    print("5. Configuration File Structure:")
    print("   Expected YAML structure:")
    print("""
   scoring_weights:
     rule_based: 0.4
     feedback_based: 0.4  
     availability: 0.2
   
   score_sources:
     rule_based:
       enabled: true
       fallback_weight: 0.5
     feedback_based:
       enabled: true
       cache_ttl: 30
     availability:
       enabled: true
       timeout_threshold: 5.0
   
   normalization:
     strategy: "min_max"
     min_confidence: 0.1
     max_confidence: 1.0
   
   logging:
     level: "DEBUG"
     score_breakdown: true
   """)
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    demo_scoring_configurations()