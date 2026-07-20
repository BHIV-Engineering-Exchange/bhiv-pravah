"""
Create tenant PostgreSQL database and apply Gurukul app schema.
Used when provisioning a new tenant (e.g. from EMS create-school).
Runs in Gurukul backend only; EMS does not create DBs.
"""
import re
import logging
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, OperationalError

logger = logging.getLogger(__name__)


def _postgres_db_name_from_url(url: str) -> Optional[str]:
    """Extract database name from postgresql://.../dbname."""
    if not url or "postgresql" not in url.split(":")[0].lower():
        return None
    url = url.rstrip("/")
    parts = url.rsplit("/", 1)
    if len(parts) != 2:
        return None
    name = parts[1].split("?")[0].strip()
    return name if name else None


def _postgres_bootstrap_url(url: str) -> str:
    """Same URL but connect to database 'postgres' (to run CREATE DATABASE)."""
    if not url or "postgresql" not in url.split(":")[0].lower():
        return url
    base = url.rstrip("/").rsplit("/", 1)[0]
    if "?" in (url.rsplit("/", 1)[-1]):
        q = "?" + url.split("?")[-1]
    else:
        q = ""
    return f"{base}/postgres{q}"


def create_tenant_database_and_schema(
    database_url: str,
    bootstrap_url: Optional[str] = None,
) -> bool:
    """
    Create the PostgreSQL database if it does not exist, then create all Gurukul tables.
    - bootstrap_url: URL to an existing DB (e.g. postgres). If None, derived from database_url.
    Returns True on success, False on error (e.g. no permission to create DB).
    """
    db_name = _postgres_db_name_from_url(database_url)
    if not db_name:
        logger.warning("Not a PostgreSQL URL or could not parse DB name: %s", database_url[:50])
        return False

    bootstrap = bootstrap_url or _postgres_bootstrap_url(database_url)

    # 1. Create database (must run with autocommit; CREATE DATABASE cannot run in transaction)
    if not re.match(r"^[a-zA-Z0-9_]+$", db_name):
        logger.warning("Invalid database name (allowed: letters, digits, underscore): %s", db_name)
        return False
    try:
        engine_bootstrap = create_engine(bootstrap, isolation_level="AUTOCOMMIT")
        with engine_bootstrap.connect() as conn:
            # PostgreSQL: CREATE DATABASE fails if exists; catch and ignore
            conn.execute(text(f"CREATE DATABASE {db_name}"))
        engine_bootstrap.dispose()
        logger.info("Created database %s", db_name)
    except ProgrammingError as e:
        if "already exists" in str(e.orig).lower() or "duplicate" in str(e.orig).lower():
            logger.info("Database %s already exists", db_name)
        else:
            logger.warning("Could not create database %s: %s", db_name, e)
            return False
    except Exception as e:
        logger.warning("Bootstrap connection or CREATE DATABASE failed for %s: %s", db_name, e)
        return False

    # 2. Create all app tables in the new database (import models so they register with Base)
    try:
        from app.core.database import Base
        import app.models.all_models  # noqa: F401 - register tables with Base

        engine_tenant = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=1,
            max_overflow=0,
        )
        Base.metadata.create_all(bind=engine_tenant)
        engine_tenant.dispose()
        logger.info("Created schema in database %s", db_name)
        return True
    except Exception as e:
        logger.exception("Schema creation failed for %s: %s", db_name, e)
        return False
