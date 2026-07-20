"""
Registry Validation Logic
Enforces strict module contract validation before execution
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ModuleRegistryEntry:
    """Registry entry for a validated module"""
    module_id: str
    schema_version: str
    dependencies: List[str]
    contract_hash: str
    enabled: bool
    truth_classification_level: str

class RegistryValidationError(Exception):
    """Raised when registry validation fails"""
    pass

class ModuleRegistry:
    """Module registry for contract validation"""
    
    def __init__(self, registry_path: str = "src/core/module_registry.json"):
        self.registry_path = registry_path
        self._registry: Dict[str, ModuleRegistryEntry] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load module registry from file"""
        if not os.path.exists(self.registry_path):
            self._create_default_registry()
        
        try:
            with open(self.registry_path, 'r') as f:
                registry_data = json.load(f)
            
            for module_id, entry_data in registry_data.items():
                self._registry[module_id] = ModuleRegistryEntry(
                    module_id=entry_data["module_id"],
                    schema_version=entry_data["schema_version"],
                    dependencies=entry_data.get("dependencies", []),
                    contract_hash=entry_data["contract_hash"],
                    enabled=entry_data.get("enabled", True),
                    truth_classification_level=entry_data.get("truth_classification_level", "unclassified")
                )
        except Exception as e:
            raise RegistryValidationError(f"Failed to load module registry: {e}")
    
    def _create_default_registry(self):
        """Create default registry with current modules"""
        default_registry = {
            "sample_text": {
                "module_id": "sample_text",
                "schema_version": "1.0.0",
                "dependencies": [],
                "contract_hash": "sha256:sample_text_v1_0_0",
                "enabled": True,
                "truth_classification_level": "unclassified"
            },
            "finance": {
                "module_id": "finance",
                "schema_version": "1.0.0", 
                "dependencies": [],
                "contract_hash": "sha256:finance_v1_0_0",
                "enabled": True,
                "truth_classification_level": "restricted"
            },
            "creator": {
                "module_id": "creator",
                "schema_version": "1.0.0",
                "dependencies": [],
                "contract_hash": "sha256:creator_v1_0_0",
                "enabled": True,
                "truth_classification_level": "unclassified"
            },
            "education": {
                "module_id": "education",
                "schema_version": "1.0.0",
                "dependencies": [],
                "contract_hash": "sha256:education_v1_0_0",
                "enabled": True,
                "truth_classification_level": "unclassified"
            },
            "video": {
                "module_id": "video",
                "schema_version": "1.0.0",
                "dependencies": ["creator"],
                "contract_hash": "sha256:video_v1_0_0",
                "enabled": True,
                "truth_classification_level": "unclassified"
            },
            "example_math": {
                "module_id": "example_math",
                "schema_version": "1.0.0",
                "dependencies": [],
                "contract_hash": "sha256:example_math_v1_0_0",
                "enabled": True,
                "truth_classification_level": "unclassified"
            },
            "example_validation": {
                "module_id": "example_validation",
                "schema_version": "1.0.0",
                "dependencies": [],
                "contract_hash": "sha256:example_validation_v1_0_0",
                "enabled": True,
                "truth_classification_level": "unclassified"
            }
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        
        with open(self.registry_path, 'w') as f:
            json.dump(default_registry, f, indent=2)
    
    def validate_module(self, module_id: str, schema_version: Optional[str] = None) -> ModuleRegistryEntry:
        """
        Validate module against registry
        
        Args:
            module_id: Module identifier
            schema_version: Expected schema version (optional)
            
        Returns:
            ModuleRegistryEntry if valid
            
        Raises:
            RegistryValidationError if validation fails
        """
        # Check if module exists in registry
        if module_id not in self._registry:
            raise RegistryValidationError(f"Module '{module_id}' not found in registry")
        
        entry = self._registry[module_id]
        
        # Check if module is enabled
        if not entry.enabled:
            raise RegistryValidationError(f"Module '{module_id}' is disabled in registry")
        
        # Check schema version if provided
        if schema_version and entry.schema_version != schema_version:
            raise RegistryValidationError(
                f"Module '{module_id}' schema version mismatch. "
                f"Expected: {schema_version}, Registry: {entry.schema_version}"
            )
        
        # Validate dependencies
        for dep in entry.dependencies:
            if dep not in self._registry:
                raise RegistryValidationError(
                    f"Module '{module_id}' dependency '{dep}' not found in registry"
                )
            
            dep_entry = self._registry[dep]
            if not dep_entry.enabled:
                raise RegistryValidationError(
                    f"Module '{module_id}' dependency '{dep}' is disabled"
                )
        
        return entry
    
    def get_module_entry(self, module_id: str) -> Optional[ModuleRegistryEntry]:
        """Get registry entry for module"""
        return self._registry.get(module_id)
    
    def list_enabled_modules(self) -> List[str]:
        """List all enabled modules"""
        return [module_id for module_id, entry in self._registry.items() if entry.enabled]
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """Get registry summary for diagnostics"""
        return {
            "total_modules": len(self._registry),
            "enabled_modules": len([e for e in self._registry.values() if e.enabled]),
            "disabled_modules": len([e for e in self._registry.values() if not e.enabled]),
            "modules": {
                module_id: {
                    "schema_version": entry.schema_version,
                    "enabled": entry.enabled,
                    "dependencies": entry.dependencies,
                    "truth_classification_level": entry.truth_classification_level
                }
                for module_id, entry in self._registry.items()
            }
        }

class RegistryValidator:
    """Registry validation service for gateway integration"""
    
    def __init__(self):
        self.registry = ModuleRegistry()
    
    def validate_execution_request(self, module_id: str, intent: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate execution request against registry
        
        Args:
            module_id: Module to execute
            intent: Execution intent
            data: Request data
            
        Returns:
            Validation result with registry entry
            
        Raises:
            RegistryValidationError if validation fails
        """
        try:
            # Validate module against registry
            registry_entry = self.registry.validate_module(module_id)
            
            # Additional validation logic can be added here
            # e.g., intent validation, data schema validation
            
            return {
                "valid": True,
                "registry_entry": registry_entry,
                "validation_timestamp": __import__('datetime').datetime.utcnow().isoformat(),
                "contract_hash": registry_entry.contract_hash,
                "truth_classification_level": registry_entry.truth_classification_level
            }
            
        except RegistryValidationError as e:
            return {
                "valid": False,
                "error": str(e),
                "validation_timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status for health checks"""
        return {
            "registry_loaded": True,
            "registry_path": self.registry.registry_path,
            "summary": self.registry.get_registry_summary()
        }