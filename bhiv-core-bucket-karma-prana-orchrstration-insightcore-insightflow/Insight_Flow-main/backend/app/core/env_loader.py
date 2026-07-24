# app/core/env_loader.py
"""
Environment Loader

Standardized environment variable loading using Bucket team's pattern.
Supports .env files, environment variables, and secrets manager.
"""

import os
import logging
from typing import Any, Optional, Dict
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class EnvironmentLoader:
    """
    Load environment variables with fallbacks and validation.
    
    Priority (highest to lowest):
    1. System environment variables
    2. .env file
    3. Secrets manager (if configured)
    4. Default values
    """
    
    def __init__(
        self,
        env_file: str = ".env",
        secrets_manager_url: Optional[str] = None
    ):
        """
        Initialize environment loader.
        
        Args:
            env_file: Path to .env file
            secrets_manager_url: Optional secrets manager endpoint
        """
        self.env_file = env_file
        self.secrets_manager_url = secrets_manager_url
        
        # Load .env file if exists
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_file}")
        else:
            logger.warning(f"Environment file not found: {env_file}")
    
    def get(
        self,
        key: str,
        default: Any = None,
        required: bool = False,
        value_type: type = str
    ) -> Any:
        """
        Get environment variable with type conversion and validation.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: Raise error if not found and no default
            value_type: Type to convert value to
        
        Returns:
            Environment variable value
        
        Raises:
            ValueError: If required variable not found
        """
        # Try system environment first
        value = os.getenv(key)
        
        # Try secrets manager if configured
        if value is None and self.secrets_manager_url:
            value = self._get_from_secrets_manager(key)
        
        # Use default if still None
        if value is None:
            if required and default is None:
                raise ValueError(f"Required environment variable not found: {key}")
            value = default
        
        # Type conversion
        if value is not None and value_type != str:
            try:
                if value_type == bool:
                    value = str(value).lower() in ('true', '1', 'yes', 'on')
                elif value_type == int:
                    value = int(value)
                elif value_type == float:
                    value = float(value)
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Failed to convert {key} to {value_type.__name__}: {e}"
                )
                if required:
                    raise
        
        logger.debug(f"Loaded env var: {key}={value}")
        return value
    
    def get_all(self) -> Dict[str, str]:
        """
        Get all environment variables.
        
        Returns:
            Dictionary of all env vars
        """
        return dict(os.environ)
    
    def _get_from_secrets_manager(self, key: str) -> Optional[str]:
        """
        Fetch secret from secrets manager.
        
        Args:
            key: Secret key
        
        Returns:
            Secret value or None
        """
        # TODO: Implement actual secrets manager integration
        # This is a placeholder for Bucket team's secrets manager
        logger.debug(f"Attempting to fetch secret: {key}")
        return None


# Global environment loader instance
_env_loader: Optional[EnvironmentLoader] = None


def get_env_loader(
    env_file: str = ".env",
    secrets_manager_url: Optional[str] = None
) -> EnvironmentLoader:
    """
    Get or create global environment loader.
    
    Args:
        env_file: Path to .env file
        secrets_manager_url: Optional secrets manager URL
    
    Returns:
        EnvironmentLoader instance
    """
    global _env_loader
    
    if _env_loader is None:
        _env_loader = EnvironmentLoader(
            env_file=env_file,
            secrets_manager_url=secrets_manager_url
        )
    
    return _env_loader