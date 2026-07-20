import os
from pathlib import Path
from typing import Dict, Any

# Database configuration
DB_PATH = os.getenv("DB_PATH", "data/context.db")

# Ensure db directory exists
Path(DB_PATH).parent.mkdir(exist_ok=True)

# Noopur integration
NOOPUR_BASE_URL = os.getenv("NOOPUR_BASE_URL", "http://localhost:5001")
# Toggle remote integration; set to "1" or "true" to enable
INTEGRATOR_USE_NOOPUR = os.getenv("INTEGRATOR_USE_NOOPUR", "false").lower() in ("1", "true", "yes")
NOOPUR_API_KEY = os.getenv("NOOPUR_API_KEY", "")
# SSPL config
# Allowed clock drift (seconds) for timestamps
SSPL_ALLOW_DRIFT_SECONDS = int(os.getenv("SSPL_ALLOW_DRIFT_SECONDS", "300"))

# MongoDB configuration
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
MONGODB_DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "core_integrator")
USE_MONGODB = os.getenv("USE_MONGODB", "false").lower() in ("1", "true", "yes")

# Video Service configuration (Text-to-Video)
VIDEO_SERVICE_URL = os.getenv("VIDEO_SERVICE_URL", "http://localhost:5002")
VIDEO_SERVICE_TIMEOUT = int(os.getenv("VIDEO_SERVICE_TIMEOUT", "300"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def validate_config() -> None:
    """Validate critical configuration on startup and fail fast if missing."""
    critical_env_vars = []

    # Authentication
    auth_enabled = os.getenv("AUTH_ENABLED", "true").lower() in ("1", "true", "yes")
    if auth_enabled:
        if not os.getenv("AUTH_SECRET_KEY"):
            critical_env_vars.append("AUTH_SECRET_KEY")
        if not os.getenv("AUTH_API_KEY"):
            critical_env_vars.append("AUTH_API_KEY")

    # Check database configuration
    if USE_MONGODB and not MONGODB_CONNECTION_STRING:
        critical_env_vars.append("MONGODB_CONNECTION_STRING")

    # Check Noopur integration
    if INTEGRATOR_USE_NOOPUR:
        if not NOOPUR_BASE_URL:
            critical_env_vars.append("NOOPUR_BASE_URL")
        if not NOOPUR_API_KEY:
            critical_env_vars.append("NOOPUR_API_KEY")

    # Check video service
    if not VIDEO_SERVICE_URL:
        critical_env_vars.append("VIDEO_SERVICE_URL")

    if critical_env_vars:
        raise ValueError(f"Missing critical environment variables: {', '.join(critical_env_vars)}")

def get_config_summary() -> Dict[str, Any]:
    """Return configuration summary for diagnostics."""
    return {
        "db_mode": "mongodb" if USE_MONGODB else ("noopur" if INTEGRATOR_USE_NOOPUR else "sqlite"),
        "noopur_enabled": INTEGRATOR_USE_NOOPUR,
        "video_service_url": VIDEO_SERVICE_URL,
        "log_level": LOG_LEVEL,
        "sspl_enabled": os.getenv("SSPL_ENABLED", "false").lower() in ("1", "true", "yes")
    }