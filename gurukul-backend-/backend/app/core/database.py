
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import Request
from app.core.config import settings

# Determine DB URL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.strip() if settings.DATABASE_URL else None

if not SQLALCHEMY_DATABASE_URL or "postgresql" not in SQLALCHEMY_DATABASE_URL:
    raise RuntimeError(
        "CRITICAL DATABASE ERROR: DATABASE_URL must be configured with a valid PostgreSQL connection string. "
        "SQLite fallback databases are disabled in production runtime."
    )

print(f"[Database] Connecting to production database: {SQLALCHEMY_DATABASE_URL.split('@')[-1] if '@' in SQLALCHEMY_DATABASE_URL else 'Remote'}")
connect_args = {}

def create_resilient_engine():
    """Create SQLAlchemy engine with pool configurations for production.
    Does not test connection immediately on import to prevent blocking Uvicorn startup.
    """
    try:
        new_engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args=connect_args,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=10,        # Permanent connections
            max_overflow=20,     # Burst capacity
            pool_timeout=30,     # Wait budget for connection
            pool_recycle=1800    # Refresh connections every 30m
        )
        return new_engine
    except Exception as e:
        print(f"[Database] Error creating engine: {e}", flush=True)
        return create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

engine = create_resilient_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def _single_db_session():
    """Single-tenant: yield one session from default engine."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db(request: Request = None):
    """
    Yield DB session. When MULTI_TENANT_ENABLED, uses request to resolve tenant and yields
    that tenant's DB session. Otherwise yields default DB.
    """
    import os
    # Re-read from env at runtime so changes take effect without restart
    multi_tenant = os.environ.get("MULTI_TENANT_ENABLED", "false").lower() == "true"
    if multi_tenant and request:
        from app.core.db_router import get_tenant_db
        for session in get_tenant_db(request):
            yield session
        return
    yield from _single_db_session()
