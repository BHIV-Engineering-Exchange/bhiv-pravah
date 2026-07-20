"""
Sovereign Application Runtime (SAR) Integration Framework

The Integration Framework provides pluggable adapter patterns for connecting external systems 
and services to the SAR ecosystem. It supports secure, auditable integrations with third-party 
systems like payroll, finance, and analytics platforms.

Features:
- Pluggable adapter architecture with dynamic loading
- Secure authentication with API keys and JWT tokens
- MongoDB-backed logging and audit trails
- Tenant-aware integration execution
- Fail-safe execution with graceful degradation
- Async/await compatible design

Dependencies:
- PyMongo for MongoDB integration
- PyJWT for token validation
- Python standard library (logging, typing, abc)

Usage:
```python
from runtime_core.integration import AdapterManager

configs = {
    "artha": {
        "name": "Artha Payroll Adapter",
        "enabled": True,
        "artha_api_url": "https://api.arthasystem.com",
        "artha_api_key": "your-key"
    }
}

manager = AdapterManager(configs)
event = {
    "event_id": "evt_123",
    "action": "payroll_processed",
    "tenant_id": "tenant_abc",
    "user_id": "user_123",
    "timestamp": "2026-01-10T17:00:00Z"
}

results = manager.execute_all_adapters(event)
print(results)
```
"""

from .adapter_manager import AdapterManager
from .adapters.base_adapter import BaseIntegrationAdapter
from .adapters.artha_adapter import ArthaAdapter
from .adapters.karya_adapter import KaryaAdapter
from .adapters.insightflow_adapter import InsightFlowAdapter
from .adapters.bucket_adapter import BucketAdapter

__all__ = [
    'AdapterManager',
    'BaseIntegrationAdapter',
    'ArthaAdapter',
    'KaryaAdapter',
    'InsightFlowAdapter',
    'BucketAdapter'
]

def get_all_adapters():
    """
    Returns a dictionary mapping adapter names to their classes.
    This is useful for dynamic adapter loading.
    """
    from .adapters import (
        ArthaAdapter,
        KaryaAdapter,
        InsightFlowAdapter,
        BucketAdapter
    )
    
    return {
        'artha': ArthaAdapter,
        'karya': KaryaAdapter,
        'insightflow': InsightFlowAdapter,
        'bucket': BucketAdapter
    }


# Import the default adapter manager from adapter_manager module
try:
    from .adapter_manager import default_adapter_manager as sar_integration
    print("SAR Integration Framework initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize SAR Integration Framework: {e}")
    import traceback
    traceback.print_exc()
    sar_integration = None