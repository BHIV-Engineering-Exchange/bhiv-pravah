"""
Central tenant registry: one DB holds tenant_id -> database_url and subdomain_slug.
Used only when MULTI_TENANT_ENABLED=True. Per-tenant DBs hold app data.
"""
from contextlib import contextmanager
import logging
import re
from typing import Optional, Generator
from sqlalchemy import Column, String, DateTime, create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.sql import func
from app.core.config import settings

logger = logging.getLogger(__name__)

CentralBase = declarative_base()


class TenantRegistry(CentralBase):
    """One row per tenant: id (tenant_id), name, type, database_url, subdomain_slug."""
    __tablename__ = "tenant_registry"

    id = Column(String, primary_key=True)  # tenant_id (UUID)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    database_url = Column(String, nullable=False)
    subdomain_slug = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def _ensure_central_database_exists(url: str) -> None:
    """Create the central PostgreSQL database if it does not exist (no-op for SQLite)."""
    if not url or "postgresql" not in url.split(":")[0].lower():
        return
    dbname = None
    try:
        base = url.split("?")[0].rstrip("/")
        if "/" not in base:
            return
        parts = base.rsplit("/", 1)
        postgres_url = parts[0] + "/postgres" + ("?" + url.split("?")[1] if "?" in url else "")
        dbname = parts[1].strip()
        if not dbname or dbname in ("postgres", "template1"):
            return
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", dbname):
            return
        eng = create_engine(postgres_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
        with eng.connect() as conn:
            r = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": dbname})
            if r.scalar() is None:
                conn.execute(text(f'CREATE DATABASE "{dbname}"'))
                logger.info("Created database %s", dbname)
        eng.dispose()
    except Exception as e:
        logger.warning("Could not auto-create central DB %s: %s (create it manually if needed)", dbname or "?", e)


def _central_engine():
    url = getattr(settings, "CENTRAL_DATABASE_URL", None) or settings.DATABASE_URL
    if not url:
        return None
    _ensure_central_database_exists(url)
    connect_args = {}
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=5,
    )


_central_engine_instance = None
_central_session_factory = None


def get_central_engine():
    global _central_engine_instance
    if _central_engine_instance is None:
        _central_engine_instance = _central_engine()
    return _central_engine_instance


def get_central_session_factory():
    global _central_session_factory
    if _central_session_factory is None:
        eng = get_central_engine()
        if eng is None:
            return None
        _central_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    return _central_session_factory


def create_central_tables():
    """Create tenant_registry table if not exists."""
    eng = get_central_engine()
    if eng:
        CentralBase.metadata.create_all(bind=eng)


@contextmanager
def get_central_db() -> Generator[Optional[Session], None, None]:
    """Session for central DB (tenant registry). Use for tenant lookup only."""
    factory = get_central_session_factory()
    if factory is None:
        yield None
        return
    db = factory()
    try:
        yield db
    finally:
        db.close()
