"""
Sync with Gurukul: students (register) and tenants (provision when EMS creates a school).
"""
import logging
from typing import Optional

import requests

from app.config import settings

logger = logging.getLogger(__name__)

# Timeout so we don't block EMS if Gurukul is slow or down
GURUKUL_REGISTER_TIMEOUT = 10
GURUKUL_PROVISION_TIMEOUT = 15


def provision_tenant_to_gurukul(school_id: int, school_name: str) -> bool:
    """
    Call Gurukul POST /api/v1/ems/provision-tenant when EMS creates a new school.
    One school in EMS = one tenant in Gurukul (same concept). Gurukul will then
    use this tenant for requests with X-Tenant-ID or subdomain (e.g. school_1).
    Returns True if provisioned or already exists, False on error.
    """
    base_url = getattr(settings, "GURUKUL_API_BASE_URL", None)
    if not base_url:
        logger.debug("GURUKUL_API_BASE_URL not set; skip provision-tenant")
        return False
    url = base_url.rstrip("/") + "/api/v1/ems/provision-tenant"
    slug = f"school_{school_id}"
    payload = {"name": school_name, "subdomain_slug": slug}
    headers = {"Content-Type": "application/json"}
    api_key = getattr(settings, "GURUKUL_API_KEY", None)
    if api_key:
        headers["X-API-Key"] = api_key
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=GURUKUL_PROVISION_TIMEOUT)
        if r.status_code in (200, 201):
            data = r.json() or {}
            logger.info("Gurukul: provisioned tenant for school %s (%s) -> tenant_id %s", school_id, school_name, data.get("tenant_id"))
            return True
        if r.status_code == 409 or (r.status_code == 201 and "already exists" in (r.json() or {}).get("message", "")):
            return True
        logger.warning("Gurukul provision-tenant failed for school %s: %s %s", school_id, r.status_code, r.text[:200])
        return False
    except Exception as e:
        logger.warning("Gurukul provision-tenant failed for school %s: %s", school_id, e)
        return False


def sync_student_to_gurukul(
    base_url: str,
    email: str,
    password: str,
    full_name: str,
) -> bool:
    """
    Register the student in Gurukul (POST /api/v1/auth/register).
    Returns True if created or already exists (400 email already registered), False on other errors.
    Sync/blocking; run from asyncio.to_thread() if needed.
    """
    url = base_url.rstrip("/") + "/api/v1/auth/register"
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name or email.split("@")[0],
        "role": "STUDENT",
    }
    try:
        r = requests.post(url, json=payload, timeout=GURUKUL_REGISTER_TIMEOUT)
        if r.status_code in (200, 201):
            logger.info("Gurukul: created student %s", email)
            return True
        if r.status_code == 400:
            detail = (r.json() or {}).get("detail", "")
            if "already registered" in str(detail).lower():
                logger.info("Gurukul: student %s already exists", email)
                return True
            logger.warning("Gurukul register failed for %s: %s", email, detail)
            return False
        logger.warning("Gurukul register failed for %s: %s %s", email, r.status_code, r.text[:200])
        return False
    except Exception as e:
        logger.warning("Gurukul sync failed for %s: %s", email, e)
        return False
