"""External Service URL Configuration for Core Integrator"""

import os
from typing import Optional


class ServiceURLs:
    """Manages external service URLs for integration"""

    @staticmethod
    def get_prompt_runner_url() -> str:
        """Get Prompt Runner service URL"""
        return os.getenv("PROMPT_RUNNER_URL", "https://prompt-runner.onrender.com")

    @staticmethod
    def get_bhiv_core_url() -> str:
        """Get BHIV Core service URL"""
        return os.getenv("BHIV_CORE_URL", "http://localhost:8001")

    @staticmethod
    def get_bucket_url() -> str:
        """Get Bucket service URL"""
        return os.getenv("BUCKET_URL", "http://localhost:8005")

    @staticmethod
    def get_integration_bridge_url() -> str:
        """Get Integration Bridge service URL"""
        return os.getenv("INTEGRATION_BRIDGE_URL", "http://localhost:8004")

    @staticmethod
    def is_bhiv_forward_enabled() -> bool:
        """Check if BHIV Core forwarding is enabled"""
        return os.getenv("ENABLE_BHIV_FORWARD", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    @staticmethod
    def get_port() -> int:
        """Get API port"""
        return int(os.getenv("PORT", "8000"))

    @staticmethod
    def get_host() -> str:
        """Get API host"""
        return os.getenv("HOST", "0.0.0.0")

    @classmethod
    def get_all_urls(cls) -> dict:
        """Get all service URLs as a dictionary"""
        return {
            "prompt_runner": cls.get_prompt_runner_url(),
            "bhiv_core": cls.get_bhiv_core_url(),
            "bucket": cls.get_bucket_url(),
            "integration_bridge": cls.get_integration_bridge_url(),
            "api_host": cls.get_host(),
            "api_port": cls.get_port(),
            "bhiv_forward_enabled": cls.is_bhiv_forward_enabled(),
        }
