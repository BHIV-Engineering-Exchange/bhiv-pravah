"""
Multi-database connection manager: DB-per-tenant. Routes each request to the correct tenant DB.
Uses central registry to resolve tenant_slug -> tenant_id and get database_url.
"""
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Request

from app.core.config import settings
from app.core.central_registry import (
    get_central_engine,
    get_central_session_factory,
    get_central_db,
    TenantRegistry,
)
from app.core.tenant_resolver import TenantContext, get_tenant_context


# Cache: database_url -> (engine, session_factory)
_tenant_engines: dict[str, tuple] = {}
_lock = None

def _tenant_engine(database_url: str):
    global _tenant_engines
    if database_url not in _tenant_engines:
        connect_args = {}
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,
        )
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        _tenant_engines[database_url] = (engine, session_factory)
    return _tenant_engines[database_url]


def resolve_tenant_id(ctx: TenantContext) -> Optional[str]:
    """Resolve TenantContext to tenant_id. If slug, lookup in central registry."""
    if ctx.tenant_id:
        return ctx.tenant_id
    if not ctx.tenant_slug:
        return None
    with get_central_db() as db:
        if db is None:
            return None
        row = db.query(TenantRegistry).filter(
            TenantRegistry.subdomain_slug == ctx.tenant_slug
        ).first()
        return row.id if row else None


def get_tenant_database_url(tenant_id: str) -> Optional[str]:
    """Return database_url for tenant_id from central registry."""
    with get_central_db() as db:
        if db is None:
            return None
        row = db.query(TenantRegistry).filter(TenantRegistry.id == tenant_id).first()
        return row.database_url if row else None


def get_tenant_db_session(tenant_id: str) -> Optional[Session]:
    """Return a new Session for the given tenant's DB. Caller must close."""
    url = get_tenant_database_url(tenant_id)
    if not url:
        return None
    _, session_factory = _tenant_engine(url)
    return session_factory()


def get_tenant_db(request: Request):
    """
    FastAPI dependency: yield a DB session for the current request's tenant.
    Resolves tenant from request (X-Tenant-ID or subdomain via central registry).
    When MULTI_TENANT_ENABLED is False, falls back to default single DB from app.core.database.
    """
    if not getattr(settings, "MULTI_TENANT_ENABLED", False):
        from app.core.database import get_db
        yield from get_db()
        return

    ctx = get_tenant_context(request)
    tenant_id = resolve_tenant_id(ctx)
    if not tenant_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Tenant required: set X-Tenant-ID header or use tenant subdomain",
        )

    url = get_tenant_database_url(tenant_id)
    if not url:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tenant not found")

    _, session_factory = _tenant_engine(url)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
