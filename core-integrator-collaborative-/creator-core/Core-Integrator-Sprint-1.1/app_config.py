import os
from pathlib import Path
from config.service_urls import ServiceURLs

# Database configuration
DB_PATH = os.getenv("DB_PATH", "db/context.db")

# Ensure db directory exists
Path(DB_PATH).parent.mkdir(exist_ok=True)

# Load external service URLs
SERVICE_URLS = ServiceURLs.get_all_urls()

# API Configuration
PORT = ServiceURLs.get_port()
HOST = ServiceURLs.get_host()

# BHIV Core Configuration
BHIV_CORE_URL = ServiceURLs.get_bhiv_core_url()
ENABLE_BHIV_FORWARD = ServiceURLs.is_bhiv_forward_enabled()

# Prompt Runner Configuration
PROMPT_RUNNER_URL = "https://prompt-runner.onrender.com"

# Bucket Configuration
BUCKET_URL = ServiceURLs.get_bucket_url()

# Integration Bridge Configuration
INTEGRATION_BRIDGE_URL = ServiceURLs.get_integration_bridge_url()