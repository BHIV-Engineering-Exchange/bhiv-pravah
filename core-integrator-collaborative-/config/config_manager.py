"""
Configuration Manager for BHIV Core-Integrator
Loads and manages centralized service configuration from YAML
Single source of truth for all microservices configuration
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Centralized configuration manager for all services"""
    
    _instance = None  # Singleton pattern
    _config = None
    
    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration manager"""
        if self._config is None:
            self.load_config()
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to services.yml. If None, searches default locations
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file not found
            yaml.YAMLError: If config file is invalid YAML
        """
        if config_path is None:
            config_path = cls._find_config_file()
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Expected at: {Path(__file__).parent / 'services.yml'}"
            )
        
        try:
            with open(config_path, 'r') as f:
                cls._config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {config_path}")
                return cls._config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {config_path}: {str(e)}")
    
    @staticmethod
    def _find_config_file() -> str:
        """Find services.yml in standard locations"""
        search_paths = [
            Path(__file__).parent / "services.yml",  # Same directory as this file
            Path(__file__).parent.parent / "config" / "services.yml",  # Parent/config/
            Path.cwd() / "config" / "services.yml",  # Current working directory
        ]
        
        for path in search_paths:
            if path.exists():
                return str(path)
        
        raise FileNotFoundError(
            "services.yml not found. Searched:\n" + 
            "\n".join(str(p) for p in search_paths)
        )
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get entire configuration"""
        if cls._config is None:
            cls.load_config()
        return cls._config
    
    @classmethod
    def get_service(cls, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific service
        
        Args:
            service_name: Name of service (prompt_runner, creator_core, etc.)
            
        Returns:
            Service configuration dictionary
            
        Raises:
            KeyError: If service not found
        """
        config = cls.get_config()
        
        if service_name not in config['services']:
            available = list(config['services'].keys())
            raise KeyError(
                f"Service '{service_name}' not found. "
                f"Available services: {available}"
            )
        
        return config['services'][service_name]
    
    @classmethod
    def get_service_url(cls, service_name: str) -> str:
        """
        Get URL for a service
        
        Args:
            service_name: Service name
            
        Returns:
            Service URL (e.g., http://127.0.0.1:8003)
        """
        service = cls.get_service(service_name)
        protocol = os.getenv(f"{service_name.upper()}_PROTOCOL", "http")
        host = os.getenv(f"{service_name.upper()}_HOST", service['host'])
        port = os.getenv(f"{service_name.upper()}_PORT", service['port'])
        
        return f"{protocol}://{host}:{port}"
    
    @classmethod
    def get_all_service_urls(cls) -> Dict[str, str]:
        """Get URLs for all services"""
        config = cls.get_config()
        urls = {}
        
        for service_name in config['services'].keys():
            urls[service_name] = cls.get_service_url(service_name)
        
        return urls
    
    @classmethod
    def get_global(cls, key: str, default: Any = None) -> Any:
        """Get global configuration value"""
        config = cls.get_config()
        return config.get('global', {}).get(key, default)
    
    @classmethod
    def get_service_port(cls, service_name: str) -> int:
        """Get port for a service"""
        service = cls.get_service(service_name)
        port = os.getenv(f"{service_name.upper()}_PORT", service['port'])
        return int(port)
    
    @classmethod
    def get_service_timeout(cls, service_name: str) -> int:
        """Get timeout for a service"""
        service = cls.get_service(service_name)
        return service.get('timeout', cls.get_global('request_timeout', 30))
    
    @classmethod
    def get_service_dependencies(cls, service_name: str) -> List[str]:
        """Get list of services this service depends on"""
        service = cls.get_service(service_name)
        return service.get('depends_on', [])
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration"""
        config = cls.get_config()
        db_type = os.getenv("DB_TYPE", config['database']['type'])
        
        db_config = config['database'][db_type].copy()
        db_config['type'] = db_type
        
        return db_config
    
    @classmethod
    def get_storage_config(cls) -> Dict[str, Any]:
        """Get storage configuration"""
        config = cls.get_config()
        storage_type = os.getenv("STORAGE_TYPE", config['storage']['type'])
        
        storage_config = config['storage'][storage_type].copy()
        storage_config['type'] = storage_type
        
        return storage_config
    
    @classmethod
    def is_feature_enabled(cls, feature_name: str) -> bool:
        """Check if a feature flag is enabled"""
        config = cls.get_config()
        feature_key = f"FEATURE_{feature_name.upper()}"
        
        # Environment variable takes precedence
        if feature_key in os.environ:
            return os.getenv(feature_key).lower() == 'true'
        
        return config['features'].get(feature_name, False)
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate configuration for completeness and consistency
        
        Returns:
            True if valid, raises exception otherwise
            
        Raises:
            ValueError: If configuration is invalid
        """
        config = cls.get_config()
        
        # Check required top-level keys
        required_keys = ['services', 'global', 'database', 'storage']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config section: {key}")
        
        # Check all services have required fields
        required_service_keys = ['port', 'timeout', 'health_check_endpoint']
        for service_name, service_config in config['services'].items():
            for key in required_service_keys:
                if key not in service_config:
                    raise ValueError(
                        f"Service '{service_name}' missing required field: {key}"
                    )
        
        # Check dependency graph is valid (no missing services)
        all_services = set(config['services'].keys())
        for service_name, service_config in config['services'].items():
            for dep in service_config.get('depends_on', []):
                if dep not in all_services:
                    raise ValueError(
                        f"Service '{service_name}' depends on non-existent "
                        f"service '{dep}'"
                    )
        
        logger.info("✅ Configuration validation passed")
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """Print configuration summary (for debugging)"""
        config = cls.get_config()
        
        print("\n" + "="*60)
        print("BHIV Configuration Summary")
        print("="*60)
        
        print("\nGlobal Settings:")
        for key, value in config['global'].items():
            print(f"  {key}: {value}")
        
        print("\nServices:")
        for service_name, service_config in config['services'].items():
            url = cls.get_service_url(service_name)
            deps = service_config.get('depends_on', [])
            deps_str = ", ".join(deps) if deps else "None"
            print(f"  ✓ {service_name:20s} → {url:40s} (Depends on: {deps_str})")
        
        print("\nDatabase:")
        db_config = cls.get_database_config()
        print(f"  Type: {db_config['type']}")
        
        print("\n" + "="*60)


# Convenience functions for easy access
def get_config() -> Dict[str, Any]:
    """Get entire configuration"""
    return ConfigManager.get_config()


def get_service_url(service_name: str) -> str:
    """Get URL for a service"""
    return ConfigManager.get_service_url(service_name)


def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get configuration for a service"""
    return ConfigManager.get_service(service_name)


if __name__ == "__main__":
    # Setup logging for debugging
    logging.basicConfig(level=logging.INFO)
    
    # Load and validate config
    manager = ConfigManager()
    manager.validate_config()
    manager.print_config()
    
    # Example usage
    print("\n" + "="*60)
    print("Example Usage:")
    print("="*60)
    print(f"Prompt Runner URL: {get_service_url('prompt_runner')}")
    print(f"Creator Core Timeout: {ConfigManager.get_service_timeout('creator_core')}s")
    print(f"Integration Bridge Dependencies: {ConfigManager.get_service_dependencies('integration_bridge')}")
    print(f"Use Noopur: {ConfigManager.is_feature_enabled('use_noopur')}")
