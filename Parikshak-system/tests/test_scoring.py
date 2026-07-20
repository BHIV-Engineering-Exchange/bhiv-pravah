"""
Test scoring components to verify they're working
"""
import sys
import os

# Add paths for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'intelligence-integration-module-main'))

from task_selector.final_convergence import final_convergence

def process_legacy_convergence(
    evaluation_result: str = None,
    failure_type: str = None,
    submission_id: str = None,
    trace_id: str = None,
    current_task_id: str = None,
    **kwargs
):
    from contracts.schemas import Task
    from task_selector.review_orchestrator import ReviewOrchestrator
    import hashlib
    from datetime import datetime
    
    task_title = kwargs.get("task_title") or evaluation_result or "Evaluation Task"
    task_description = kwargs.get("task_description") or failure_type or ""
    repository_url = kwargs.get("repository_url")
    module_id = kwargs.get("module_id") or "task-review-agent"
    schema_version = kwargs.get("schema_version") or "v1.0"
    
    task_hash = hashlib.md5(f"{task_title}:{task_description}:{module_id}".encode("utf-8", errors="ignore")).hexdigest()
    task = Task(
        task_id=f"task-conv-{task_hash}",
        task_title=task_title,
        task_description=task_description,
        submitted_by="system_convergence",
        timestamp=datetime.now(),
        github_repo_link=repository_url or "",
        module_id=module_id,
        schema_version=schema_version
    )
    
    orchestrator = ReviewOrchestrator()
    res = orchestrator.process_submission(task, trace_id=trace_id)
    
    return {
        "score": res["review"]["score"],
        "status": res["review"]["status"],
        "task_type": res["next_task"]["task_type"],
        "canonical_authority": True,
        "evaluation_basis": "assignment_engine",
        "registry_rejection": res.get("registry_rejection", False),
        "difficulty": res["next_task"]["difficulty"],
        "supporting_signals": {
            "technical_signals": {
                "title_score": res["review"].get("title_score", 0),
                "description_score": res["review"].get("description_score", 0),
                "repository_score": res["review"].get("repository_score", 0)
            }
        },
        "evidence_summary": {
            "expected_features": 0,
            "delivered_features": 0,
            "delivery_ratio": 0.0
        }
    }

def test_scoring_with_good_task():
    """Test with a well-structured task that should get higher scores"""
    
    result = process_legacy_convergence(
        task_title="Advanced Microservices Auth API: JWT, OAuth2, RBAC, Rate Limiting, and Docker Containerization",
        task_description="""
        Build a comprehensive enterprise-grade authentication microservice with the following technical requirements:
        
        1. JWT Token Management:
           - Token generation with custom claims
           - Token validation and refresh mechanisms
           - Secure token storage and rotation
        
        2. OAuth2 Integration:
           - Authorization code flow implementation
           - Client credentials management
           - Scope-based access control
        
        3. Role-Based Access Control (RBAC):
           - Dynamic role assignment
           - Permission-based resource access
           - Hierarchical role inheritance
        
        4. Rate Limiting:
           - Token bucket algorithm implementation
           - Per-user and per-endpoint rate limits
           - Redis-based distributed rate limiting
        
        5. Docker Containerization:
           - Multi-stage Docker builds
           - Container orchestration with Docker Compose
           - Health checks and monitoring endpoints
        
        6. Security Features:
           - Password hashing with bcrypt
           - SQL injection prevention
           - CORS configuration
           - Input validation and sanitization
        
        7. Testing and Documentation:
           - Unit tests with 90%+ coverage
           - Integration tests for all endpoints
           - Comprehensive API documentation
           - Deployment guides and examples
         
        Technical Stack: Node.js, Express.js, PostgreSQL, Redis, Docker, Jest
        Architecture: Clean Architecture with dependency injection
        """,
        repository_url="https://github.com/user/enterprise-auth-api",
        module_id="task-review-agent",
        schema_version="v1.0",
        trace_id="trace-test-scoring-good-task"
    )
    
    print("=" * 60)
    print("SCORING TEST - COMPREHENSIVE TASK")
    print("=" * 60)
    print(f"Title Score: {result.get('supporting_signals', {}).get('technical_signals', {}).get('title_score', 0)}/20")
    print(f"Description Score: {result.get('supporting_signals', {}).get('technical_signals', {}).get('description_score', 0)}/40")
    print(f"Repository Score: {result.get('supporting_signals', {}).get('technical_signals', {}).get('repository_score', 0)}/40")
    print(f"Total Score: {result.get('score', 0)}/100")
    print(f"Status: {result.get('status')}")
    print(f"Task Type: {result.get('task_type')}")
    
    # Show evidence
    evidence = result.get('evidence_summary', {})
    print(f"\nEvidence Summary:")
    print(f"  Expected Features: {evidence.get('expected_features', 0)}")
    print(f"  Delivered Features: {evidence.get('delivered_features', 0)}")
    print(f"  Delivery Ratio: {evidence.get('delivery_ratio', 0.0):.2f}")
    
    return result

if __name__ == "__main__":
    test_scoring_with_good_task()