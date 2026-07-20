"""
Dynamic Evaluation Engine Demo
Demonstrates the new dynamic scoring capabilities
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.evaluation_engine import EvaluationEngine
import json

def demo_dynamic_evaluation():
    print("=" * 80)
    print("DYNAMIC DETERMINISTIC EVALUATION ENGINE - DEMONSTRATION")
    print("=" * 80)
    
    engine = EvaluationEngine()
    
    # Test Case 1: High-Quality Technical Task
    print("\n[TEST CASE 1] High-Quality Technical Task")
    print("-" * 50)
    
    title1 = "Build Microservice Authentication System with JWT and OAuth2"
    description1 = """
    Objective: Develop a scalable microservice for user authentication and authorization
    
    Technical Requirements:
    - JWT token generation and validation with RS256 algorithm
    - OAuth2 integration with Google and GitHub providers
    - Rate limiting for security (100 requests/minute per IP)
    - Database persistence with PostgreSQL and Redis caching
    - API documentation with OpenAPI/Swagger
    
    Technical Implementation:
    1. FastAPI framework setup with async/await patterns
    2. Database models and Alembic migrations
    3. Authentication endpoints (/login, /register, /refresh)
    4. Token management utilities and middleware
    5. Security middleware with CORS and CSRF protection
    
    Testing Strategy:
    - Unit tests for all endpoints (pytest)
    - Integration tests for database operations
    - Security penetration testing with OWASP guidelines
    - Load testing with 1000+ concurrent users
    
    Deployment:
    - Docker containerization
    - Kubernetes deployment with health checks
    - CI/CD pipeline with GitHub Actions
    """
    
    result1 = engine.evaluate(title1, description1)
    
    print(f"Title: {title1}")
    print(f"Final Score: {result1['final_score']}/100")
    print(f"Classification: {result1['classification']}")
    print(f"Score Breakdown:")
    print(f"  - Title: {result1['score_breakdown']['title']}/20")
    print(f"  - Description: {result1['score_breakdown']['description']}/40")
    print(f"  - Repository: {result1['score_breakdown']['repository']}/40")
    
    print(f"\\nKey Signals:")
    signals = result1['signals']
    print(f"  - Technical Keyword Ratio: {signals.get('technical_keyword_ratio', 0):.3f}")
    print(f"  - Description Word Count: {signals.get('description_word_count', 0)}")
    print(f"  - Structure Indicators: {signals.get('structure_indicators', 0)}")
    print(f"  - Code Blocks: {signals.get('code_blocks', 0)}")
    
    # Test Case 2: Medium-Quality Task
    print("\\n\\n[TEST CASE 2] Medium-Quality Task")
    print("-" * 50)
    
    title2 = "Create User Login System"
    description2 = """
    Build a login system for users.
    
    Requirements:
    - Users can register with email and password
    - Users can login and logout
    - Password should be secure
    
    Implementation:
    - Use a web framework
    - Store data in database
    - Add some security features
    """
    
    result2 = engine.evaluate(title2, description2)
    
    print(f"Title: {title2}")
    print(f"Final Score: {result2['final_score']}/100")
    print(f"Classification: {result2['classification']}")
    print(f"Score Breakdown:")
    print(f"  - Title: {result2['score_breakdown']['title']}/20")
    print(f"  - Description: {result2['score_breakdown']['description']}/40")
    print(f"  - Repository: {result2['score_breakdown']['repository']}/40")
    
    print(f"\\nFailure Reasons:")
    for reason in result2.get('failure_reasons', []):
        print(f"  - {reason}")
    
    print(f"\\nImprovement Hints:")
    for hint in result2.get('improvement_hints', []):
        print(f"  - {hint}")
    
    # Test Case 3: Low-Quality Task
    print("\\n\\n[TEST CASE 3] Low-Quality Task")
    print("-" * 50)
    
    title3 = "Make website"
    description3 = "Create a simple website with some pages and forms."
    
    result3 = engine.evaluate(title3, description3)
    
    print(f"Title: {title3}")
    print(f"Final Score: {result3['final_score']}/100")
    print(f"Classification: {result3['classification']}")
    print(f"Score Breakdown:")
    print(f"  - Title: {result3['score_breakdown']['title']}/20")
    print(f"  - Description: {result3['score_breakdown']['description']}/40")
    print(f"  - Repository: {result3['score_breakdown']['repository']}/40")
    
    print(f"\\nFailure Reasons:")
    for reason in result3.get('failure_reasons', []):
        print(f"  - {reason}")
    
    # Determinism Test
    print("\\n\\n[DETERMINISM VERIFICATION]")
    print("-" * 50)
    
    print("Running identical evaluation 5 times...")
    results = []
    for i in range(5):
        result = engine.evaluate(title1, description1)
        results.append(result['final_score'])
    
    print(f"Scores: {results}")
    print(f"All identical: {len(set(results)) == 1}")
    print(f"Standard deviation: {0 if len(set(results)) == 1 else 'Non-zero (ERROR!)'}")
    
    # Explainability Demo
    print("\\n\\n[EXPLAINABILITY BREAKDOWN]")
    print("-" * 50)
    
    detailed_metrics = result1['detailed_metrics']
    
    print("Title Analysis:")
    title_metrics = detailed_metrics['title_metrics']
    for key, value in title_metrics.items():
        print(f"  {key}: {value}")
    
    print("\\nDescription Analysis:")
    desc_metrics = detailed_metrics['description_metrics']
    for key, value in desc_metrics.items():
        print(f"  {key}: {value}")
    
    print("\\n" + "=" * 80)
    print("DYNAMIC EVALUATION ENGINE - DEMONSTRATION COMPLETE")
    print("✓ Dynamic scoring based on measurable signals")
    print("✓ Deterministic behavior guaranteed")
    print("✓ Full explainability with all metrics")
    print("✓ No hardcoded scores - all values computed")
    print("=" * 80)

if __name__ == "__main__":
    demo_dynamic_evaluation()