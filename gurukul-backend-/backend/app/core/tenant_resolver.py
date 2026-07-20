"""
Tenant identification layer: resolve tenant_id from subdomain or X-Tenant-ID header.
Subdomain: school1.gurukul.blackholeinfiverse.com -> tenant_slug = "school1"
Header: X-Tenant-ID: <uuid> -> tenant_id directly.
"""
import re
from typing import Optional
from dataclasses import dataclass
from fastapi import Request, HTTPException, status

# UUID-style: 8-4-4-4-12 hex (accept any so example UUIDs and real tenant_registry ids both work)
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


@dataclass
class TenantContext:
    """Resolved tenant from request."""
    tenant_id: Optional[str] = None
    tenant_slug: Optional[str] = None

    @property
    def resolved_id(self) -> Optional[str]:
        return self.tenant_id


def _get_base_domain() -> str:
    """Base domain for subdomain extraction (e.g. gurukul.blackholeinfiverse.com)."""
    from app.core.config import settings
    return getattr(settings, "TENANT_BASE_DOMAIN", "gurukul.blackholeinfiverse.com").lower()


def _subdomain_from_host(host: str, base_domain: str) -> Optional[str]:
    """Extract subdomain if host is like school1.<base_domain>. Returns None if no subdomain."""
    if not host:
        return None
    host = host.split(":")[0].lower()
    base = base_domain.lower()
    if host == base or not host.endswith("." + base):
        return None
    prefix = host[: -len(base) - 1]
    if not prefix or "." in prefix:
        return None
    return prefix


def resolve_tenant_from_request(request: Request) -> TenantContext:
    """
    Resolve tenant from request: X-Tenant-ID header first, then subdomain.
    Does not perform DB lookup; use db_router to resolve tenant_slug -> tenant_id.
    """
    # 1. Header takes precedence (for API clients / same-domain). Try common casings.
    header_tenant = (
        request.headers.get("X-Tenant-ID")
        or request.headers.get("x-tenant-id")
        or ""
    )
    if isinstance(header_tenant, bytes):
        header_tenant = header_tenant.decode("utf-8", errors="ignore")
    header_tenant = header_tenant.strip().strip('"\'')
    if header_tenant and UUID_PATTERN.match(header_tenant):
        return TenantContext(tenant_id=header_tenant, tenant_slug=None)

    # 2. Subdomain: school1.gurukul.blackholeinfiverse.com -> school1
    host = request.headers.get("host") or request.url.hostname or ""
    base = _get_base_domain()
    slug = _subdomain_from_host(host, base)
    if slug:
        return TenantContext(tenant_id=None, tenant_slug=slug)

    return TenantContext(tenant_id=None, tenant_slug=None)


# Paths that must work without tenant (docs, openapi, health)
_TENANT_SKIP_PATHS = {"/openapi.json", "/docs", "/redoc", "/", "/health"}


async def tenant_resolver_middleware(request: Request, call_next):
    """Middleware: set request.state.tenant_context from resolver. Skip public paths."""
    if request.url.path in _TENANT_SKIP_PATHS:
        return await call_next(request)
    request.state.tenant_context = resolve_tenant_from_request(request)
    return await call_next(request)


def get_tenant_context(request: Request) -> TenantContext:
    """FastAPI dependency: return tenant context (must run after middleware)."""
    ctx = getattr(request.state, "tenant_context", None)
    if ctx is None:
        ctx = resolve_tenant_from_request(request)
        request.state.tenant_context = ctx
    return ctx


def require_tenant(request: Request) -> TenantContext:
    """Dependency: return tenant context; raises 400 if no tenant_id and no tenant_slug."""
    ctx = get_tenant_context(request)
    if ctx.tenant_id or ctx.tenant_slug:
        return ctx
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tenant required: set X-Tenant-ID header or use tenant subdomain (e.g. school1.gurukul.blackholeinfiverse.com)",
    )
