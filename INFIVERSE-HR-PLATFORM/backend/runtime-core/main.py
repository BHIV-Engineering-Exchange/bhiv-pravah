"""
Sovereign Application Runtime (SAR) - Main Application Entry Point

This is the main entry point for the SAR that integrates all components.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from typing import Optional

# Add the runtime-core directory to the path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="Sovereign Application Runtime (SAR)",
    version="1.0.0",
    description="Reusable, multi-tenant runtime environment for BHIV products",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, configure specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Sovereign Application Runtime (SAR)",
        "version": "1.0.0",
        "status": "running",
        "components": [
            "Authentication Service",
            "Tenant Resolution Service", 
            "Role Enforcement Service",
            "Audit Logging Service",
            "Workflow Engine"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Sovereign Application Runtime",
        "version": "1.0.0",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }

@app.get("/ready")
async def readiness_check():
    # Add any readiness checks here
    return {
        "status": "ready",
        "service": "Sovereign Application Runtime",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }

# Import and include all SAR modules
try:
    from auth.router import router as auth_router
    app.include_router(auth_router)
    print("✓ Authentication service loaded")
except ImportError as e:
    print(f"⚠ Authentication service not loaded: {e}")

try:
    from tenancy.router import router as tenancy_router
    app.include_router(tenancy_router)
    print("✓ Tenancy service loaded")
except ImportError as e:
    print(f"⚠ Tenancy service not loaded: {e}")

try:
    from role_enforcement.router import router as role_router
    app.include_router(role_router)
    print("✓ Role enforcement service loaded")
except ImportError as e:
    print(f"⚠ Role enforcement service not loaded: {e}")

try:
    from audit_logging.router import router as audit_router
    app.include_router(audit_router)
    print("✓ Audit logging service loaded")
except ImportError as e:
    print(f"⚠ Audit logging service not loaded: {e}")

try:
    from workflow.router import router as workflow_router
    app.include_router(workflow_router)
    print("✓ Workflow engine loaded")
except ImportError as e:
    print(f"⚠ Workflow engine not loaded: {e}")

# Add middleware for all services
try:
    from tenancy.middleware import TenantIsolationMiddleware
    app.add_middleware(TenantIsolationMiddleware)
    print("✓ Tenant isolation middleware loaded")
except ImportError as e:
    print(f"⚠ Tenant isolation middleware not loaded: {e}")

try:
    from role_enforcement.middleware import RoleEnforcementMiddleware
    app.add_middleware(RoleEnforcementMiddleware)
    print("✓ Role enforcement middleware loaded")
except ImportError as e:
    print(f"⚠ Role enforcement middleware not loaded: {e}")

try:
    from audit_logging.middleware import AuditLoggingMiddleware
    app.add_middleware(AuditLoggingMiddleware)
    print("✓ Audit logging middleware loaded")
except ImportError as e:
    print(f"⚠ Audit logging middleware not loaded: {e}")

try:
    from workflow.middleware import WorkflowEnforcementMiddleware
    app.add_middleware(WorkflowEnforcementMiddleware)
    print("✓ Workflow enforcement middleware loaded")
except ImportError as e:
    print(f"⚠ Workflow enforcement middleware not loaded: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )