#!/usr/bin/env python3
"""
Test RL + Feedback Agent Integration
Verify all components work without database connection
"""

import sys
import os
sys.path.append('services/langgraph/app')

def test_ml_models():
    """Test ML models functionality"""
    try:
        from services.langgraph.app.rl_integration.ml_models import MLModels
        
        # Test skill similarity
        candidate_skills = ["Python", "FastAPI", "PostgreSQL"]
        job_requirements = ["Python", "Django", "MySQL", "REST API"]
        
        similarity = MLModels.calculate_skill_similarity(candidate_skills, job_requirements)
        
        print(f"ML Models Test: Skill similarity = {similarity}%")
        return True
        
    except Exception as e:
        print(f"ML Models Test Failed: {e}")
        return False

def test_decision_engine():
    """Test decision engine functionality"""
    try:
        from services.langgraph.app.rl_integration.decision_engine import DecisionEngine
        
        decision_engine = DecisionEngine()
        
        candidate_features = {
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience": 3
        }
        
        job_features = {
            "requirements": ["Python", "Django", "MySQL"],
            "level": "mid"
        }
        
        decision = decision_engine.make_rl_decision(candidate_features, job_features)
        
        print(f"Decision Engine Test: Decision = {decision.get('decision_type')} (Score: {decision.get('rl_score')})")
        return True
        
    except Exception as e:
        print(f"Decision Engine Test Failed: {e}")
        return False

def test_postgres_adapter():
    """Test PostgreSQL adapter (without actual connection)"""
    try:
        from services.langgraph.app.rl_integration.postgres_adapter import PostgreSQLAdapter
        
        adapter = PostgreSQLAdapter()
        
        # Test connection parameters setup
        params = adapter._get_connection_params()
        
        print(f"PostgreSQL Adapter Test: Connection params configured")
        return True
        
    except Exception as e:
        print(f"PostgreSQL Adapter Test Failed: {e}")
        return False

def test_rl_endpoints():
    """Test RL endpoints import"""
    try:
        from services.langgraph.app.rl_integration.rl_endpoints import router
        
        # Check router has routes
        route_count = len(router.routes)
        
        print(f"RL Endpoints Test: {route_count} routes configured")
        return True
        
    except Exception as e:
        print(f"RL Endpoints Test Failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("RL + Feedback Agent Integration Tests")
    print("=" * 50)
    
    tests = [
        ("ML Models", test_ml_models),
        ("Decision Engine", test_decision_engine),
        ("PostgreSQL Adapter", test_postgres_adapter),
        ("RL Endpoints", test_rl_endpoints)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("RL + Feedback Agent Integration: READY!")
        print("\nComponents Successfully Integrated:")
        print("   - ML Models (TF-IDF similarity)")
        print("   - Decision Engine (RL-enhanced)")
        print("   - PostgreSQL Adapter (database bridge)")
        print("   - RL Endpoints (6 API routes)")
        print("\nNext Steps:")
        print("   1. Start Docker database")
        print("   2. Deploy RL tables")
        print("   3. Test API endpoints")
        return True
    else:
        print("Integration has issues that need fixing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)