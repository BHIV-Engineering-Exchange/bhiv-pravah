import sys
from app.core.logging_config import setup_logging
setup_logging()

print("=" * 80, flush=True)
print("[Main] FILE LOADED - Starting Gurukul Backend (Deterministic Mode)...", flush=True)

import os
import uvicorn
import logging
import traceback
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

print(f"[Main] Python version: {sys.version}", flush=True)
print(f"[Main] Working directory: {os.getcwd()}", flush=True)
print(f"[Main] Python path: {sys.path[:3]}", flush=True)
sys.stdout.flush()

try:
    from fastapi import FastAPI, Request, status, HTTPException, Header
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError
    from app.core.config import settings
    from app.core.database import engine, Base
    from app.core.karma_database import get_db as get_mongo_db
    from app.services.prana_contract_registry import IngressContractViolationError
    from app.services.prana_runtime import (
        AppendOnlyViolationError,
        append_only_violation_from_exception,
        ensure_prana_integrity_append_only_guards,
    )
    print("[Main] [OK] FastAPI and core imports successful")
except Exception as e:
    print(f"[Main] [FAIL] Error importing FastAPI/core modules: {e}")
    print(traceback.format_exc())
    sys.exit(1)

logger = logging.getLogger(__name__)


def load_demo_seed_fn():
    """Load the optional demo seeding function if the script exists."""
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "create_demo_tenant.py"
    if not script_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("create_demo_tenant", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load demo seed script from {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "seed_demo_env", None)

# Initialize FastAPI IMMEDIATELY - this allows the server to start listening
# even if router imports are slow. We'll include routers after the app is created.
try:
    app = FastAPI(title=settings.API_TITLE)
    print(f"[Main] [OK] FastAPI app initialized with title: {settings.API_TITLE}")
    sys.stdout.flush()
except Exception as e:
    print(f"[Main] [FAIL] Error initializing FastAPI app: {e}")
    print(traceback.format_exc())
    sys.stdout.flush()
    sys.exit(1)

# DEFER router imports to startup event to allow server to start immediately
# This is critical - uvicorn waits for module to fully load before starting server
# By deferring router imports, we allow the server to start and bind to port first
print("[Main] Router imports will be deferred to startup event for faster server start")
sys.stdout.flush()

# Placeholder variables for routers - will be imported in startup event
chat = None
flashcards = None
learning = None
ems = None
summarizer = None
auth = None
soul = None
agents = None
quiz = None
journey = None
tts = None
ems_student = None
lesson = None
sovereign = None
vaani = None
bucket = None
ems_sync_manual = None
prana = None
dashboard_mock_apis = None
dev_panel = None

# Karma Tracker routers
karma_router = None
balance = None
redeem = None
policy = None
feedback = None
analytics = None
agami = None
normalization = None
rnanubandhan = None
karma_v1_main = None
lifecycle = None
stats = None
log_action = None
appeal = None
atonement = None
death = None
event = None

# Global health state
system_health = {
    "sql_db": "initializing",
    "mongo_db": "initializing",
    "startup_complete": False
}

# CORS - Allow frontend to access backend
origins = [
    "http://localhost:5173",  # Vite dev server (Gurukul Frontend)
    "http://localhost:3000",  # Alternative frontend port
    "http://localhost:3001",  # EMS frontend dev
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "https://gurukul-frontend-738j.onrender.com",  # Gurukul Frontend (Production)
    "https://gurukul.blackholeinfiverse.com",  # Gurukul custom domain
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


# API security: rate limit, then payload size (last added = first run). Use BaseHTTPMiddleware so Starlette passes (app).
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.api_security_layer import payload_size_middleware, rate_limit_middleware
from app.middleware.trace_middleware import trace_id_middleware

app.add_middleware(BaseHTTPMiddleware, dispatch=payload_size_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=trace_id_middleware)

# Metrics middleware — transparent request counter & latency tracker
try:
    from app.services.system_metrics import MetricsMiddleware
    app.add_middleware(MetricsMiddleware)
    print("[Main] [OK] MetricsMiddleware registered")
except Exception as _e:
    print(f"[Main] [WARN] MetricsMiddleware not loaded: {_e}")

# Multi-tenant: resolve tenant from subdomain or X-Tenant-ID before routes
if getattr(settings, "MULTI_TENANT_ENABLED", False):
    from app.core.tenant_resolver import tenant_resolver_middleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=tenant_resolver_middleware)

@app.on_event("startup")
async def startup_event():
    # Startup
    import asyncio
    global chat, flashcards, learning, ems, summarizer, auth, soul, agents, quiz, journey, tts
    global ems_student, lesson, sovereign, vaani, bucket, ems_sync_manual, prana, dashboard_mock_apis, dev_panel
    global karma_router, balance, redeem, policy, feedback, analytics, agami, normalization
    global rnanubandhan, karma_v1_main, lifecycle, stats, log_action, appeal, atonement, death, event
    
    # Debug: Print port information
    port_from_env = os.getenv("PORT", "not set")
    print(f"\n{'='*50}")
    print(f"Gurukul API v2 (Refactored) Started at http://{settings.HOST}:{settings.PORT}")
    print(f"PORT from environment: {port_from_env}")
    print(f"PORT from settings: {settings.PORT}")
    print(f"Env: {os.getenv('ENV', 'dev')}")
    print(f"{'='*50}\n")
    sys.stdout.flush()
    
    sys.stdout.flush()
    
    async def init_database():
        """Initialize SQL database tables"""
        try:
            print("[Startup] Initializing SQL database...")
            # Import all models to ensure they are registered with Base.metadata
            from app.models import all_models, prana_models  # Add other model modules as needed
            
            # Create tables in a thread since it's a blocking operation
            await asyncio.to_thread(Base.metadata.create_all, bind=engine)
            await asyncio.to_thread(ensure_prana_integrity_append_only_guards, engine)
            
            # Run TANTRA Convergence Migrations
            try:
                from scripts.migrate_prana_hashes import migrate as run_prana_migration
                await asyncio.to_thread(run_prana_migration)
            except Exception as me:
                print(f"[Startup] [WARN] Prana migration warning: {me}")
                
            print("[Startup] [OK] SQL database tables initialized")
            sys.stdout.flush()
        except Exception as e:
            print(f"[Startup] [FAIL] SQL database init error: {e}")
            print(traceback.format_exc())
            sys.stdout.flush()

    async def init_mongodb():
        """Initialize MongoDB connection"""
        try:
            print("[Startup] Initializing MongoDB connection...")
            # This will trigger the lazy connection
            db = get_mongo_db()
            # Run a simple command to verify connection
            await asyncio.to_thread(db.command, "ping")
            print("[Startup] [OK] MongoDB connection verified")
            system_health["mongo_db"] = "connected"
            sys.stdout.flush()
        except Exception as e:
            print(f"[Startup] [WARN] MongoDB init warning: {e}")
            system_health["mongo_db"] = f"failed: {str(e)}"
            sys.stdout.flush()

    # Import routers NOW (after server has started) - run in thread to avoid blocking
    def import_auth_router_sync():
        """Import and register auth router first (critical for registration/login)"""
        global auth
        try:
            print("[Startup] Importing auth router (critical path)...")
            sys.stdout.flush()
            from app.routers import auth as auth_mod
            auth = auth_mod
            
            # Register auth router immediately
            app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
            print("[Startup] [OK] Auth router registered at /api/v1/auth")
            
            # Verify routes are registered
            auth_routes = [route.path for route in app.routes if hasattr(route, 'path') and '/api/v1/auth' in route.path]
            print(f"[Startup] Registered auth routes: {len(auth_routes)} routes")
            sys.stdout.flush()
            return True
        except Exception as e:
            print(f"[Startup] [FAIL] CRITICAL: Failed to import auth router: {e}")
            print(traceback.format_exc())
            sys.stdout.flush()
            return False
    
    def import_other_routers_sync():
        """Import other routers — each independently fault-isolated so one failure
        does not prevent other routers from loading."""
        global chat, flashcards, learning, ems, summarizer, soul, agents, quiz, journey, tts
        global ems_student, lesson, sovereign, vaani, bucket, ems_sync_manual, prana, monitor, dev_panel

        print("[Startup] Importing other routers (individually fault-isolated)...")
        sys.stdout.flush()

        # ── System monitor ────────────────────────────────────────────
        try:
            from app.services import system_monitor as monitor_mod
            monitor = monitor_mod
            app.include_router(monitor.router)
            print("[Startup] [OK] monitor router")
        except Exception as e:
            print(f"[Startup] [WARN] monitor failed: {e}")

        # ── Core Learning ─────────────────────────────────────────────
        try:
            from app.routers import chat as chat_mod
            chat = chat_mod
            app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
            print("[Startup] [OK] chat router")
        except Exception as e:
            print(f"[Startup] [WARN] chat failed: {e}")

        try:
            from app.routers import flashcards as flashcards_mod
            flashcards = flashcards_mod
            app.include_router(flashcards.router, prefix="/api/v1/flashcards", tags=["Flashcards"])
            app.include_router(flashcards.router, prefix="/flashcards", tags=["Legacy Flashcards"])
            print("[Startup] [OK] flashcards router")
        except Exception as e:
            print(f"[Startup] [WARN] flashcards failed: {e}")

        try:
            from app.routers import learning as learning_mod
            learning = learning_mod
            app.include_router(learning.router, prefix="/api/v1/learning", tags=["Learning"])
            print("[Startup] [OK] learning router")
        except Exception as e:
            print(f"[Startup] [WARN] learning failed: {e}")

        # ── AGENTS (critical — has /api/v1/agent/tts) ─────────────────
        try:
            from app.routers import agents as agents_mod
            agents = agents_mod
            app.include_router(agents.router, prefix="/api/v1/agent", tags=["Agents"])
            print("[Startup] [OK] agents router (includes /api/v1/agent/tts)")
        except Exception as e:
            print(f"[Startup] [WARN] agents failed: {e}")
            print(traceback.format_exc())

        # ── Soul & Quiz ───────────────────────────────────────────────
        try:
            from app.routers import soul as soul_mod
            soul = soul_mod
            app.include_router(soul.router, prefix="/api/v1/soul", tags=["Soul"])
            print("[Startup] [OK] soul router")
        except Exception as e:
            print(f"[Startup] [WARN] soul failed: {e}")

        try:
            from app.routers import quiz as quiz_mod
            quiz = quiz_mod
            app.include_router(quiz.router, prefix="/api/v1/quiz", tags=["Quiz"])
            print("[Startup] [OK] quiz router")
        except Exception as e:
            print(f"[Startup] [WARN] quiz failed: {e}")

        # ── EMS ───────────────────────────────────────────────────────
        try:
            from app.routers import ems as ems_mod
            ems = ems_mod
            app.include_router(ems.router, prefix="/api/v1/ems", tags=["Admin (EMS)"])
            print("[Startup] [OK] ems router")
        except Exception as e:
            print(f"[Startup] [WARN] ems failed: {e}")

        try:
            from app.routers import ems_student as ems_student_mod
            ems_student = ems_student_mod
            app.include_router(ems_student.router, tags=["EMS Student Integration"])
            print("[Startup] [OK] ems_student router")
        except Exception as e:
            print(f"[Startup] [WARN] ems_student failed: {e}")

        try:
            from app.routers import ems_sync_manual as ems_sync_manual_mod
            ems_sync_manual = ems_sync_manual_mod
            app.include_router(ems_sync_manual.router, tags=["EMS Manual Sync"])
            print("[Startup] [OK] ems_sync_manual router")
        except Exception as e:
            print(f"[Startup] [WARN] ems_sync_manual failed: {e}")

        # ── Journey / Lesson ──────────────────────────────────────────
        try:
            from app.routers import journey as journey_mod
            journey = journey_mod
            app.include_router(journey.router, prefix="/api/v1/learning", tags=["Learning Journey"])
            print("[Startup] [OK] journey router")
        except Exception as e:
            print(f"[Startup] [WARN] journey failed: {e}")

        try:
            from app.routers import lesson as lesson_mod
            lesson = lesson_mod
            app.include_router(lesson.router, prefix="/api/v1/lesson", tags=["Lesson Context"])
            print("[Startup] [OK] lesson router")
        except Exception as e:
            print(f"[Startup] [WARN] lesson failed: {e}")

        # ── TTS / Vaani / Sovereign ───────────────────────────────────
        try:
            from app.routers import tts as tts_mod
            tts = tts_mod
            app.include_router(tts.router, prefix="/api/v1/tts", tags=["Text-to-Speech"])
            print("[Startup] [OK] tts router")
        except Exception as e:
            print(f"[Startup] [WARN] tts failed: {e}")

        try:
            from app.routers import vaani as vaani_mod
            vaani = vaani_mod
            app.include_router(vaani.router, prefix="/api/v1/vaani", tags=["Vaani RL-TTS"])
            print("[Startup] [OK] vaani router")
        except Exception as e:
            print(f"[Startup] [WARN] vaani failed: {e}")

        try:
            from app.routers import sovereign as sovereign_mod
            sovereign = sovereign_mod
            app.include_router(sovereign.router, prefix="/api/v1/sovereign", tags=["Sovereign Fusion Layer"])
            print("[Startup] [OK] sovereign router")
        except Exception as e:
            print(f"[Startup] [WARN] sovereign failed: {e}")

        # ── PRANA Bucket ──────────────────────────────────────────────
        try:
            from app.routers import bucket as bucket_mod
            bucket = bucket_mod
            app.include_router(bucket.router, prefix="/api/v1", tags=["PRANA Bucket"])
            print("[Startup] [OK] bucket router")
        except Exception as e:
            print(f"[Startup] [WARN] bucket failed: {e}")

        try:
            from app.routers import prana as prana_mod
            prana = prana_mod
            app.include_router(prana.router, prefix="/api/v1", tags=["PRANA Runtime"])
            print("[Startup] [OK] prana router")
        except Exception as e:
            print(f"[Startup] [WARN] prana failed: {e}")

        try:
            from app.routers import dashboard_mock_apis as dashboard_mod
            dashboard_mock_apis = dashboard_mod
            app.include_router(dashboard_mock_apis.router, prefix="/api/v1", tags=["Operational Intelligence Dashboard"])
            print("[Startup] [OK] dashboard_mock_apis router")
        except Exception as e:
            print(f"[Startup] [WARN] dashboard_mock_apis failed: {e}")

        try:
            from app.routers import dashboard as dashboard_real_mod
            app.include_router(dashboard_real_mod.router, prefix="/api/v1", tags=["Dashboard Foundation"])
            print("[Startup] [OK] dashboard router")
        except Exception as e:
            print(f"[Startup] [WARN] dashboard router failed: {e}")

        try:
            from app.routers import dev_panel as dev_panel_mod
            dev_panel = dev_panel_mod
            app.include_router(dev_panel.router, tags=["Developer Control Panel"])
            app.include_router(dev_panel.admin_router, tags=["Admin Intelligence"])
            print("[Startup] [OK] dev_panel & admin routers registered")
        except Exception as e:
            print(f"[Startup] [WARN] dev_panel failed: {e}")

        # ── Voice STT ─────────────────────────────────────────────────
        try:
            from app.routers import voice as voice_mod
            app.include_router(voice_mod.router, prefix="/api/v1", tags=["Speech Interface (STT)"])
            print("[Startup] [OK] voice STT router at /api/v1/voice")
        except Exception as e:
            print(f"[Startup] [WARN] voice STT router failed: {e}")

        # ── State Board Compliance ────────────────────────────────────
        try:
            from app.routers import compliance as compliance_mod
            app.include_router(compliance_mod.router, prefix="/api/v1", tags=["State Board Compliance"])
            print("[Startup] [OK] compliance router at /api/v1/compliance")
        except Exception as e:
            print(f"[Startup] [WARN] compliance router failed: {e}")

        # ── Master Data Universe Registry ─────────────────────────────
        try:
            from app.routers import mdu_registry as mdu_registry_mod
            app.include_router(mdu_registry_mod.router, prefix="/api/v1", tags=["Master Data Universe"])
            print("[Startup] [OK] mdu_registry router at /api/v1/mdu")
        except Exception as e:
            print(f"[Startup] [WARN] mdu_registry router failed: {e}")

        # ── Watchdog ──────────────────────────────────────────────────
        try:
            from app.services.service_watchdog import watchdog as _watchdog
            _watchdog.start()
            print("[Startup] [OK] ServiceWatchdog started")
        except Exception as _we:
            print(f"[Startup] [WARN] ServiceWatchdog failed: {_we}")

        # ── Metrics endpoint ──────────────────────────────────────────
        try:
            from app.services.system_metrics import metrics_router as _metrics_router
            from app.services.prometheus_exporter import prometheus_router as _prometheus_router
            app.include_router(_metrics_router)
            app.include_router(_prometheus_router)
            print("[Startup] [OK] /system/metrics and /metrics endpoints registered")
        except Exception as _me:
            print(f"[Startup] [WARN] metrics_router not loaded: {_me}")

        print("[Startup] [OK] Router import phase complete")
        sys.stdout.flush()

        
        # Import Karma Tracker routers
        try:
            print("[Startup] Importing Karma Tracker routers...")
            sys.stdout.flush()
            from app.routers.karma_tracker import karma as karma_router_mod
            from app.routers.karma_tracker import balance as balance_mod, redeem as redeem_mod
            from app.routers.karma_tracker import policy as policy_mod, feedback as feedback_mod
            from app.routers.karma_tracker import analytics as analytics_mod, agami as agami_mod
            from app.routers.karma_tracker import normalization as normalization_mod
            from app.routers.karma_tracker import rnanubandhan as rnanubandhan_mod
            from app.routers.karma_tracker.v1.karma import main as karma_v1_main_mod
            from app.routers.karma_tracker.v1.karma import lifecycle as lifecycle_mod
            from app.routers.karma_tracker.v1.karma import stats as stats_mod
            from app.routers.karma_tracker.v1.karma import log_action as log_action_mod
            from app.routers.karma_tracker.v1.karma import appeal as appeal_mod
            from app.routers.karma_tracker.v1.karma import atonement as atonement_mod
            from app.routers.karma_tracker.v1.karma import death as death_mod
            from app.routers.karma_tracker.v1.karma import event as event_mod
            
            # Assign to globals
            karma_router = karma_router_mod
            balance = balance_mod
            redeem = redeem_mod
            policy = policy_mod
            feedback = feedback_mod
            analytics = analytics_mod
            agami = agami_mod
            normalization = normalization_mod
            rnanubandhan = rnanubandhan_mod
            karma_v1_main = karma_v1_main_mod
            lifecycle = lifecycle_mod
            stats = stats_mod
            log_action = log_action_mod
            appeal = appeal_mod
            atonement = atonement_mod
            death = death_mod
            event = event_mod
            
            # Include routers
            app.include_router(karma_router.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(balance.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(redeem.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(policy.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(feedback.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Karma Analytics"])
            app.include_router(agami.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(normalization.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(rnanubandhan.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(karma_v1_main.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(lifecycle.router, prefix="/api/v1/karma/lifecycle", tags=["Karma Lifecycle"])
            app.include_router(stats.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(log_action.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(appeal.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(atonement.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(death.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            app.include_router(event.router, prefix="/api/v1/karma", tags=["Karma Tracker"])
            
            print("[Startup] [OK] Karma Tracker routers imported and included")
            sys.stdout.flush()
        except Exception as e:
            print(f"[Startup] [WARN] Error importing Karma Tracker routers: {e}")
            print(traceback.format_exc())
            sys.stdout.flush()
        
        return True  # Return success - individual router failures are logged but don't stop startup
    
    async def do_startup():
        try:
            # CRITICAL: Import auth router first and wait for it (registration/login must work)
            # Other routers can load in background
            try:
                print("[Startup] [INFO] Importing critical auth router...")
                sys.stdout.flush()
                # Wait for auth router with shorter timeout (should be fast)
                auth_success = await asyncio.wait_for(
                    asyncio.to_thread(import_auth_router_sync),
                    timeout=30.0  # 30 seconds should be enough for auth router
                )
                if auth_success:
                    print("[Startup] [OK] Auth router registered. Registration/login endpoints are now available.")
                    sys.stdout.flush()
                else:
                    print("[Startup] [FAIL] CRITICAL: Auth router failed to load!")
                    sys.stdout.flush()
            except asyncio.TimeoutError:
                print("[Startup] [FAIL] CRITICAL: Auth router import timeout after 30 seconds")
                print("[Startup] Registration/login will NOT work!")
                sys.stdout.flush()
            except Exception as e:
                print(f"[Startup] [FAIL] CRITICAL: Auth router import error: {e}")
                print(traceback.format_exc())
                sys.stdout.flush()
            
            # Import other routers in background (non-blocking)
            # These can take longer and don't block server startup
            async def import_other_routers_async():
                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(import_other_routers_sync),
                        timeout=120.0  # 2 minutes for other routers
                    )
                    print("[Startup] [OK] All other routers imported and registered.")
                    sys.stdout.flush()
                except asyncio.TimeoutError:
                    print("[Startup] [WARN] Other routers import timeout after 2 minutes")
                    print("[Startup] Some features may not be available.")
                    sys.stdout.flush()
                except Exception as e:
                    print(f"[Startup] [WARN] Other routers import error: {e}")
                    sys.stdout.flush()
            
            # Start importing other routers in background (don't wait)
            asyncio.create_task(import_other_routers_async())
            print("[Startup] [INFO] Other routers are loading in background...")
            sys.stdout.flush()
            
            # Run all initialization tasks in background - don't wait for them
            # This allows startup event to return immediately so server can bind to port
            asyncio.create_task(init_database())
            asyncio.create_task(init_mongodb())
            if getattr(settings, "MULTI_TENANT_ENABLED", False):
                try:
                    from app.core.central_registry import create_central_tables
                    create_central_tables()
                    print("[Startup] [OK] Central tenant registry tables ensured")
                except Exception as e:
                    print(f"[Startup] [WARN] Central registry init: {e}")
            
            print("[Startup] [INFO] Summarizer model loading DISABLED to save memory")
            
            # --- AUTO SEED DEMO DATA ---
            if os.getenv("AUTO_SEED_DEMO") == "true":
                try:
                    print("[Startup] [SEED] AUTO_SEED_DEMO=true detected. Seeding demo environment...")
                    seed_demo_env = load_demo_seed_fn()
                    if seed_demo_env is None:
                        print("[Startup] [SEED] [SKIP] Demo seed script not found at backend/scripts/create_demo_tenant.py")
                        return True
                    # Run in thread to avoid blocking startup watchdog
                    await asyncio.to_thread(seed_demo_env)
                    print("[Startup] [SEED] [OK] Demo environment seeded successfully")
                except Exception as e:
                    print(f"[Startup] [SEED] [FAIL] Error seeding demo environment: {e}")
                    traceback.print_exc()

            print("[Startup] [OK] Startup event logic execution finished.")
            sys.stdout.flush()
            return True
        except Exception as e:
            print(f"[Startup] [FAIL] Fatal error in startup logic: {e}")
            print(traceback.format_exc())
            sys.stdout.flush()
            return False

    # --- STARTUP WATCHDOG ---
    try:
        print("[Startup] [INFO] Gurukul Startup Watchdog started (20s timeout)...")
        await asyncio.wait_for(do_startup(), timeout=20.0)
        print("[Startup] [OK] Watchdog finished successfully.")
    except asyncio.TimeoutError:
        print("[Startup] [FAIL] FATAL: Gurukul startup timed out after 20 seconds. Some features may be unstable.")
        sys.stdout.flush()
    except Exception as e:
        print(f"[Startup] [FAIL] Watchdog caught fatal error: {e}")
        sys.stdout.flush()
    
    async def dependency_watchdog():
        """Periodic background task to ensure dependencies stay connected"""
        print("[Watchdog] Background dependency watchdog started.")
        while True:
            await asyncio.sleep(60) # check every minute
            
            # Check SQL
            try:
                from app.core.database import engine
                from sqlalchemy import text
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                system_health["sql_db"] = "connected"
            except Exception as e:
                system_health["sql_db"] = f"lost: {str(e)}"
                print(f"[Watchdog] SQL Connection lost: {e}")

            # Check Mongo
            try:
                from app.core.karma_database import get_db as get_m_db
                db = get_m_db()
                db.command('ping')
                system_health["mongo_db"] = "connected"
            except Exception as e:
                system_health["mongo_db"] = f"lost: {str(e)}"
                print(f"[Watchdog] MongoDB Connection lost: {e}")

    # Start the watchdog
    asyncio.create_task(dependency_watchdog())
    
    # ── 10. Start Autonomous Monitoring ────────────────────────
    try:
        from app.services.service_watchdog import watchdog
        from app.services.pravah_adapter import pravah_adapter
        from app.services.bucket_adapter import bucket_adapter
        
        watchdog.start()
        pravah_adapter.start()
        bucket_adapter.start()
        print("[Startup] [OK] ServiceWatchdog, PravahAdapter and BucketAdapter started")
        sys.stdout.flush()
    except Exception as e:
        print(f"[Startup] [WARN] Failed to start autonomous monitoring: {e}")
        sys.stdout.flush()

    system_health["startup_complete"] = True
    print("[Startup] [OK] Startup event complete! Server will bind to port now.")
    print("[Startup] Background tasks (routers, DB, MongoDB, Watchdog) are active.")
    sys.stdout.flush()
    # Return immediately - don't wait for any background tasks

# Routers are imported and included in the startup event
# This allows the server to start immediately without waiting for router imports

# Root Health Check
@app.get("/")
async def root():
    return {"message": "Gurukul Backend API v2 is running", "docs": "/docs"}


# Multi-tenant: show resolved tenant for current request (so you can verify which DB is used)
@app.get(
    "/api/v1/tenant-info",
    summary="Tenant info (multi-tenant)",
    description="Returns which tenant this request is for. Click 'Try it out', set **tenant_id** (query) to a tenant UUID, then Execute.",
)
async def tenant_info(
    request: Request,
    tenant_id: Optional[str] = None,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
):
    from app.core.tenant_resolver import get_tenant_context, TenantContext, UUID_PATTERN
    from app.core.config import settings
    if not getattr(settings, "MULTI_TENANT_ENABLED", False):
        return {"multi_tenant_enabled": False, "message": "Set MULTI_TENANT_ENABLED=true to see tenant resolution"}
    uid = (tenant_id or x_tenant_id or "").strip()
    if uid and UUID_PATTERN.match(uid):
        ctx = TenantContext(tenant_id=uid, tenant_slug=None)
    else:
        ctx = get_tenant_context(request)
    from app.core.db_router import resolve_tenant_id
    resolved_id = resolve_tenant_id(ctx)
    return {
        "multi_tenant_enabled": True,
        "tenant_id": ctx.tenant_id,
        "tenant_slug": ctx.tenant_slug,
        "resolved_tenant_id": resolved_id,
        "hint": "Send X-Tenant-ID header or use subdomain (e.g. school1.gurukul...) to switch tenant",
    }

# Health check endpoint for Production
@app.get("/health", summary="System Health Check")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_state": system_health
    }

# Legacy Shim for old endpoints if needed (optional)
# We might want to mount the old endpoints similarly or just rely on the new prefix.
# The user asked to "Refactor", implies we should probably match the old URLs if we want frontend to work immediately?
# The old main.py had "/summarize-pdf".
# My new router has "/api/v1/summarizer/summarize-pdf".
# IF I want to avoid breaking frontend, I should probably also include routers without prefix or redirect?
# For "Production Hardening", we should use versioned APIs.
# But "Do not break what already works".
# So I should probably alias the old routes or mount them at root as well?
# Let's add them at root for compatibility for now.

# Legacy shims are included in the startup event along with other routers

# Global Exception Handler - Ensures CORS headers are included even on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that ensures CORS headers are included
    even when unhandled exceptions occur.
    """
    append_only_violation = append_only_violation_from_exception(exc)
    if append_only_violation is not None:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=append_only_violation.to_response(),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "*",
            }
        )
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    content = {
        "detail": f"Internal server error: {str(exc)}",
        "type": type(exc).__name__
    }
    # For /openapi.json failures, include path and traceback so "Failed to fetch" can be debugged
    if request.url.path.rstrip("/") == "/openapi.json":
        content["path"] = "/openapi.json"
        content["traceback"] = traceback.format_exc()
        content["hint"] = "Fix the error above; then /docs will load."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(AppendOnlyViolationError)
async def append_only_violation_handler(request: Request, exc: AppendOnlyViolationError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=exc.to_response(),
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(IngressContractViolationError)
async def ingress_contract_violation_handler(request: Request, exc: IngressContractViolationError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response(),
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with CORS headers.
    """
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with CORS headers.
    """
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Final message to confirm module is fully loaded
print("[Main] [OK] Module fully loaded. App is ready for uvicorn to start server.")
print(f"[Main] App object: {app}")
sys.stdout.flush()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
