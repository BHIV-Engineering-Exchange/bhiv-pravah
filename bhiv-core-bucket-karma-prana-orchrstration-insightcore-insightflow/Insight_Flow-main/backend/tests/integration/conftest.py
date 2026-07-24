# tests/integration/conftest.py
"""
Configuration for integration tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def temp_config_dir():
    """Create temporary directory for test configurations"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_scoring_config():
    """Sample scoring configuration for tests"""
    return {
        "scoring_weights": {
            "rule_based": 0.4,
            "feedback_based": 0.4,
            "availability": 0.2
        },
        "normalization": {
            "method": "min_max",
            "bounds": [0.0, 1.0]
        }
    }