from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, super_admin, schools, dashboard, teacher, student, parent, bucket
from app.routers.admin import dashboard as admin_dashboard
from app.config import settings

import os
import asyncio

# Initialize FastAPI app
app = FastAPI(
    title="School Management System API",
    description="Multi-tenant School Management System Backend",
    version="1.0.0"
)

# Create database tables and seed demo data on startup
@app.on_event("startup")
async def startup_event():
    async def run_setup():
        try:
            from app.models import StudentSummary, StudentFlashcard, StudentTestResult, StudentSubjectData
            # Create tables in thread to avoid blocking
            await asyncio.to_thread(Base.metadata.create_all, bind=engine)
            print("[Startup] Database tables created/verified successfully!")
            
            # --- AUTO SEED DEMO DATA ---
            if os.getenv("AUTO_SEED_DEMO") == "true":
                try:
                    print("[Startup] [SEED] AUTO_SEED_DEMO=true detected. Seeding EMS demo data...")
                    from scripts.seed_ems_demo import seed_ems_demo
                    # Seed in thread
                    await asyncio.to_thread(seed_ems_demo)
                    print("[Startup] [SEED] [OK] EMS demo data seeded successfully")
                except Exception as e:
                    print(f"[Startup] [SEED] [FAIL] Error seeding EMS demo: {e}")
        except Exception as e:
            print(f"[Startup] Database table creation/seeding warning: {e}")

    # Run setup in background so server can start immediately
    asyncio.create_task(run_setup())

# CORS middleware (configure for your frontend domain in production)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite default port (Gurukul frontend)
    "http://127.0.0.1:5173",
    "http://localhost:3001",  # EMS frontend port
    "http://127.0.0.1:3001",
    "https://ems-frontend-x7tr.onrender.com",  # EMS Frontend (Production)
]
additional_origins = os.getenv("ALLOWED_ORIGINS")
if additional_origins:
    origins.extend([org.strip() for org in additional_origins.split(",") if org.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Include routers
app.include_router(auth.router)
app.include_router(super_admin.router)
app.include_router(schools.router)
app.include_router(dashboard.router)
app.include_router(admin_dashboard.router)  # School Admin Dashboard
app.include_router(teacher.router)  # Teacher Dashboard
app.include_router(student.router)  # Student Dashboard
app.include_router(parent.router)  # Parent Dashboard
app.include_router(bucket.router)  # BHIV Bucket PRANA ingest


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "School Management System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint with database validation."""
    from app.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
    finally:
        db.close()
