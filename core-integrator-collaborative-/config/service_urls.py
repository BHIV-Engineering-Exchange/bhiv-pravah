"""
Service URL Configuration for Independent Deployment
=====================================================
Each service can be deployed separately and configured via environment variables.
"""

from typing import Dict

from config.config_manager import ConfigManager

SERVICE_KEYS = [
    "prompt_runner",
    "creator_core",
    "bhiv_core",
    "integration_bridge",
    "bucket",
    "cet",
    "sarathi",
    "gate",
    "control_plane",
    "telemetry",
]


def get_service_url(service_name: str) -> str:
    """Get URL for a specific service"""
    try:
        return ConfigManager.get_service_url(service_name)
    except Exception:
        return "http://127.0.0.1:8000"


def get_all_service_urls() -> Dict[str, str]:
    """Get all service URLs"""
    return {name: get_service_url(name) for name in SERVICE_KEYS}


def print_service_urls():
    """Print all configured service URLs"""
    print("\n" + "="*70)
    print("SERVICE URLS CONFIGURATION")
    print("="*70)
    for name, url in get_all_service_urls().items():
        env_var = f"{name.upper()}_URL"
        print(f"  {name:20s} -> {url}")
        print(f"  {'(set via ' + env_var + ')':20s}")
    print("="*70 + "\n")


# Environment template for deployment
DEPLOYMENT_ENV_TEMPLATE = """
# BHIV Services URL Configuration
# Copy this to your .env file and update URLs for your deployment

# Prompt Runner Service
PROMPT_RUNNER_URL=http://your-prompt-runner-host:8003

# Creator Core Service
CREATOR_CORE_URL=http://your-creator-core-host:8000

# BHIV Core Service
BHIV_CORE_URL=http://your-bhiv-core-host:8001

# Integration Bridge Service
INTEGRATION_BRIDGE_URL=http://your-bridge-host:8004

# Bucket Service
BUCKET_URL=http://your-bucket-host:8005

# Database Configuration (for BHIV Core)
USE_MONGODB=false
MONGODB_CONNECTION_STRING=mongodb://localhost:27017
MONGODB_DATABASE_NAME=bhiv_production

# Optional: Noopur Integration
INTEGRATOR_USE_NOOPUR=false
NOOPUR_BASE_URL=http://localhost:5001
"""


if __name__ == "__main__":
    print_service_urls()
    print("\nFor deployment, set these environment variables:")
    print(DEPLOYMENT_ENV_TEMPLATE)
