# Generic Framework Refactoring Plan

## Overview
This document outlines the approach to refactor HR-specific logic into a generic, reusable framework while maintaining the HR functionality as a specialized implementation.

## Current Architecture Analysis

### Runtime Core (Generic Framework)
The `runtime-core` already contains a well-designed, generic framework with:
- Authentication service (generic)
- Tenant resolution service (generic)
- Role enforcement service (generic)
- Audit logging service (generic)
- Workflow engine (generic)
- Integration adapters (generic)

### Gateway Service (HR-Specific)
The `services/gateway/app/main.py` contains HR-specific logic including:
- Job posting and management
- Candidate management
- AI matching engine
- Values assessment
- Interview scheduling
- Job offers

## Refactoring Strategy

### 1. Core Framework Components (Already Generic)

#### Authentication Service
```python
# Already generic - no changes needed
- JWT token management
- API key authentication
- 2FA with TOTP
- Password management
- Session management
```

#### Tenant Service
```python
# Already generic - no changes needed
- Tenant identification
- Cross-tenant access prevention
- Context injection
- Validation mechanisms
```

#### Role Enforcement Service
```python
# Already generic - no changes needed
- Role definitions
- Permission system
- Dynamic assignment
- Middleware integration
```

#### Audit Logging Service
```python
# Already generic - no changes needed
- Event tracking
- Provenance tracking
- Multi-tenancy support
- Flexible storage backends
```

#### Workflow Engine
```python
# Already generic - no changes needed
- Workflow definitions
- Task management
- State management
- Multi-tenancy support
```

### 2. Domain-Specific Extensions

#### HR Domain Module
Instead of embedding HR logic in the gateway, create a separate HR domain module:

```python
# hr_module/hr_entities.py
class Job:
    def __init__(self, title, department, location, requirements, description, **kwargs):
        self.title = title
        self.department = department
        self.location = location
        self.requirements = requirements
        self.description = description
        # Generic attributes can be stored in kwargs

class Candidate:
    def __init__(self, name, email, phone, skills, experience, **kwargs):
        self.name = name
        self.email = email
        self.phone = phone
        self.skills = skills
        self.experience = experience
        # Generic attributes can be stored in kwargs

# hr_module/hr_workflows.py
class RecruitmentWorkflow:
    def __init__(self):
        # Define recruitment-specific workflow
        pass

# hr_module/hr_adapters.py
class HRCustomAdapter:
    # HR-specific adapter implementations
    pass
```

#### Generic Entity Framework
Create a generic entity management system in the framework:

```python
# framework/entities.py
class BaseEntity:
    def __init__(self, **kwargs):
        # Generic entity with extensible attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

class EntityManager:
    def create_entity(self, entity_type, **attributes):
        # Generic entity creation
        pass

    def query_entities(self, entity_type, filters):
        # Generic entity querying
        pass
```

### 3. API Layer Abstraction

#### Generic API Router
Instead of HR-specific endpoints, create a generic router:

```python
# framework/api/generic_router.py
from fastapi import APIRouter, Depends
from typing import Dict, Any

router = APIRouter()

@router.post("/{entity_type}")
async def create_entity(
    entity_type: str,
    data: Dict[str, Any],
    auth = Depends(get_auth)
):
    """Generic entity creation endpoint"""
    # Delegate to domain-specific handler
    pass

@router.get("/{entity_type}/{entity_id}")
async def get_entity(
    entity_type: str,
    entity_id: str,
    auth = Depends(get_auth)
):
    """Generic entity retrieval endpoint"""
    pass

@router.put("/{entity_type}/{entity_id}")
async def update_entity(
    entity_type: str,
    entity_id: str,
    data: Dict[str, Any],
    auth = Depends(get_auth)
):
    """Generic entity update endpoint"""
    pass
```

#### HR-Specific Implementation
The HR application would then specialize the generic endpoints:

```python
# hr_app/api/hr_router.py
from framework.api.generic_router import router as generic_router
from hr_module.hr_entities import Job, Candidate

# HR-specific route extensions or overrides
@router.post("/jobs")
async def create_job(job_data: JobCreate, auth = Depends(get_auth)):
    # HR-specific job creation logic
    pass

@router.post("/candidates")
async def create_candidate(candidate_data: CandidateCreate, auth = Depends(get_auth)):
    # HR-specific candidate creation logic
    pass
```

### 4. Configuration-Driven Behavior

#### Domain Configuration
Use configuration to drive domain-specific behavior:

```python
# config/domains/hr_config.py
HR_DOMAIN_CONFIG = {
    "entities": {
        "job": {
            "required_fields": ["title", "department", "location"],
            "optional_fields": ["salary", "benefits"],
            "validation_rules": {
                "title": {"min_length": 1, "max_length": 200},
                "department": {"enum": ["engineering", "marketing", "sales"]}
            }
        },
        "candidate": {
            "required_fields": ["name", "email"],
            "optional_fields": ["phone", "experience", "skills"],
            "validation_rules": {
                "email": {"pattern": r"^[^@]+@[^@]+\.[^@]+$"}
            }
        }
    },
    "workflows": {
        "recruitment": {
            "steps": ["application", "screening", "interview", "offer", "onboarding"]
        }
    },
    "permissions": {
        "job_create": ["admin", "recruiter"],
        "candidate_view": ["admin", "recruiter", "hiring_manager"]
    }
}
```

#### Generic Configuration Handler
```python
# framework/config_handler.py
class ConfigDrivenEntity:
    def __init__(self, entity_type, config):
        self.entity_type = entity_type
        self.config = config
        self.required_fields = config.get("required_fields", [])
        self.optional_fields = config.get("optional_fields", [])
        self.validation_rules = config.get("validation_rules", {})
    
    def validate(self, data):
        # Generic validation based on configuration
        pass
```

### 5. Plugin Architecture

#### Domain Plugin Interface
```python
# framework/plugin_interface.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class DomainPlugin(ABC):
    @abstractmethod
    def get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
        """Return schema for the specified entity type"""
        pass
    
    @abstractmethod
    def validate_entity(self, entity_type: str, data: Dict[str, Any]) -> bool:
        """Validate entity data"""
        pass
    
    @abstractmethod
    def execute_domain_workflow(self, workflow_name: str, context: Dict[str, Any]) -> Any:
        """Execute domain-specific workflow"""
        pass
    
    @abstractmethod
    def get_permissions_mapping(self) -> Dict[str, Any]:
        """Return permission mappings for the domain"""
        pass
```

#### HR Plugin Implementation
```python
# hr_plugin/hr_plugin.py
from framework.plugin_interface import DomainPlugin

class HRPlugin(DomainPlugin):
    def get_entity_schema(self, entity_type: str):
        if entity_type == "job":
            return {
                "title": {"type": "string", "required": True},
                "department": {"type": "string", "required": True},
                "location": {"type": "string", "required": True},
                # ... other fields
            }
        elif entity_type == "candidate":
            return {
                "name": {"type": "string", "required": True},
                "email": {"type": "string", "required": True},
                # ... other fields
            }
        # ... other entity types
    
    def validate_entity(self, entity_type: str, data: Dict[str, Any]) -> bool:
        # HR-specific validation logic
        pass
    
    def execute_domain_workflow(self, workflow_name: str, context: Dict[str, Any]) -> Any:
        # HR-specific workflow execution
        pass
    
    def get_permissions_mapping(self) -> Dict[str, Any]:
        return {
            "job_create": ["admin", "recruiter"],
            "candidate_view": ["admin", "recruiter", "hiring_manager"],
            # ... other permissions
        }
```

### 6. Migration Path

#### Phase 1: Extract Common Patterns
- Identify HR-specific patterns in the gateway service
- Create generic abstractions for these patterns
- Maintain backward compatibility

#### Phase 2: Implement Plugin System
- Develop the plugin interface
- Migrate HR logic to the HR plugin
- Update the framework to use plugins

#### Phase 3: Domain Registration
- Implement domain registration system
- Allow multiple domains to coexist
- Ensure proper tenant isolation across domains

#### Phase 4: Configuration Migration
- Migrate HR-specific configurations to domain config
- Implement configuration validation
- Ensure smooth transition for existing deployments

## Benefits of This Approach

### 1. True Reusability
- Framework can be used for HR, CRM, ERP, etc.
- Each domain implements only what's specific to it
- Common infrastructure is shared

### 2. Maintainability
- Changes to framework don't affect domain logic
- Domain-specific changes don't affect framework
- Clear separation of concerns

### 3. Extensibility
- New domains can be added without changing framework
- Existing domains can be modified independently
- Configuration-driven customization

### 4. Testing
- Framework can be tested independently
- Domains can be tested in isolation
- Integration testing between framework and domains

## Implementation Considerations

### 1. Performance
- Plugin system should not significantly impact performance
- Caching mechanisms for configuration
- Efficient entity validation

### 2. Security
- Plugin sandboxing if needed
- Proper validation of plugin inputs
- Tenant isolation maintained across domains

### 3. Compatibility
- Maintain backward compatibility during migration
- Provide migration tools/scripts
- Clear upgrade path for existing installations

## Next Steps

1. Implement the plugin interface in the framework
2. Create the HR domain plugin
3. Update the gateway service to use the plugin system
4. Develop configuration management system
5. Create migration scripts for existing data
6. Update documentation and examples

---

**Document Version**: 1.0  
**Last Updated**: January 17, 2026  
**Owner**: BHIV Development Team  
**Review Cycle**: Quarterly