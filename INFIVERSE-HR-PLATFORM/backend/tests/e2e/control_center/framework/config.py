"""Environment-backed configuration for Control Center E2E runs."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class E2EConfig:
    gateway_url: str = "http://localhost:8000"
    agent_url: str = "http://localhost:9000"
    langgraph_url: str = "http://localhost:9001"
    api_key_secret: str = ""
    jwt_secret_key: str = ""
    candidate_jwt_secret_key: str = ""
    mongodb_uri: str = ""
    client_login_id: str = ""
    client_login_password: str = ""
    request_timeout_s: float = 30.0
    results_dir: str = ""

    @classmethod
    def from_env(cls) -> "E2EConfig":
        return cls(
            gateway_url=os.getenv("GATEWAY_URL", "http://localhost:8000").rstrip("/"),
            agent_url=os.getenv("AGENT_URL", "http://localhost:9000").rstrip("/"),
            langgraph_url=os.getenv("LANGGRAPH_URL", "http://localhost:9001").rstrip("/"),
            api_key_secret=os.getenv("API_KEY_SECRET", os.getenv("API_KEY", "")).strip(),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "").strip(),
            candidate_jwt_secret_key=os.getenv("CANDIDATE_JWT_SECRET_KEY", "").strip(),
            mongodb_uri=os.getenv("MONGODB_URI", os.getenv("MONGO_URI", "")).strip(),
            # Archived demo TECH001/demo123 is NOT valid on production; set explicitly for local seed DB only.
            client_login_id=os.getenv("E2E_CLIENT_ID", "").strip(),
            client_login_password=os.getenv("E2E_CLIENT_PASSWORD", "").strip(),
            request_timeout_s=float(os.getenv("E2E_HTTP_TIMEOUT", "30")),
            results_dir=os.getenv(
                "E2E_RESULTS_DIR",
                os.path.join(os.path.dirname(__file__), "..", "results"),
            ),
        )

    def optional_vite_documentation(self) -> List[str]:
        """Document frontend vars (not required for API-only E2E)."""
        return [
            "VITE_API_BASE_URL (defaults to gateway in dev)",
            "VITE_ENABLE_CONTROL_CENTER=true",
            "VITE_AGENT_SERVICE_URL / VITE_LANGGRAPH_SERVICE_URL (optional direct health from UI)",
        ]
