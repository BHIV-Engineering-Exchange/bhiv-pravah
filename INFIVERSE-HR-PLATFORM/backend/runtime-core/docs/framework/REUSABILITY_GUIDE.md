# Reusability Guide

**Document Status**: PRODUCTION-READY | FRAMEWORK-EXTRACTED | REUSABLE
**Updated**: January 29, 2026
**Current System**: MongoDB Atlas migration complete, 111 endpoints operational

## Current Hiring Loop Reusability

The BHIV HR Platform hiring loop is already designed for reuse across domains. Here's how it currently works:

### Generic Hiring Loop Pattern
```python
class GenericHiringWorkflow:
    def __init__(self, database_service, matching_service, notification_service):
        self.db = database_service
        self.matcher = matching_service
        self.notifier = notification_service
    
    def process_application(self, job_id, applicant_data):
        # Generic application processing
        application = self.db.create_application(job_id, applicant_data)
        match_result = self.matcher.find_best_matches(job_id, [applicant_data])
        self.notifier.send_status_update(applicant_data, match_result)
        return application, match_result

# HR Domain Usage
hr_workflow = GenericHiringWorkflow(mongo_db, ai_matcher, communication_adapter)
hr_result = hr_workflow.process_application(job_id, candidate_profile)

# Generic Application Intake (Non-HR Example)
application_workflow = GenericHiringWorkflow(mongo_db, ai_matcher, communication_adapter)
application_result = application_workflow.process_application(project_id, applicant_data)
```

## Current Implementation Reusability

### 1. Database Abstraction
```python
# Current MongoDB implementation
from app.database import get_mongo_db
from app.db_helpers import insert_one, find_many, update_one

class DatabaseAdapter:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_record(self, collection, data):
        return insert_one(self.db, collection, data)
    
    def find_records(self, collection, query):
        return find_many(self.db, collection, query)

# Reusable across domains - just change collection names
```

### 2. Matching Engine Reusability
```python
# Current AI matching implementation
from services.agent.semantic_engine.phase3_engine import SemanticMatcher

class ReusableMatcher:
    def __init__(self, ai_engine):
        self.engine = ai_engine
    
    def match_entities(self, requirements, candidates, weights=None):
        # Generic matching logic
        return self.engine.semantic_match(requirements, candidates, weights)

# Works for jobs/candidates, projects/applicants, services/clients, etc.
```

### 3. Workflow Orchestration
```python
# Current LangGraph integration
from services.langgraph.app.workflows import WorkflowEngine

class GenericWorkflowOrchestrator:
    def __init__(self, workflow_engine):
        self.engine = workflow_engine
    
    def execute_process(self, process_type, data):
        # Generic workflow execution
        workflow = self.engine.get_workflow(process_type)
        return workflow.execute(data)

# Reusable for hiring, onboarding, project management, etc.
```

## Adapter Pattern Implementation

### Current Communication Adapters
```python
# Email Adapter
class EmailAdapter:
    def send_notification(self, recipient, message, template=None):
        # Current Gmail SMTP implementation
        pass

# SMS Adapter
class SMSAdapter:
    def send_notification(self, recipient, message):
        # Current Twilio implementation
        pass

# Generic Notification Service
class NotificationService:
    def __init__(self, adapters):
        self.adapters = adapters
    
    def notify(self, channels, recipient, message):
        for channel in channels:
            if channel in self.adapters:
                self.adapters[channel].send_notification(recipient, message)

# Reusable across domains with different adapter configurations
```

## Domain-Specific Configuration

### HR Domain Configuration
```python
hr_config = {
    'collections': {
        'jobs': 'jobs',
        'candidates': 'candidates',
        'applications': 'applications'
    },
    'matching_weights': {
        'skills': 0.4,
        'experience': 0.3,
        'values': 0.2,
        'location': 0.1
    },
    'workflow': 'hiring_process',
    'notifications': ['email', 'sms', 'telegram']
}
```

### Generic Application Configuration
```python
generic_config = {
    'collections': {
        'requests': 'service_requests',
        'applicants': 'applicants',
        'submissions': 'submissions'
    },
    'matching_weights': {
        'requirements': 0.5,
        'qualifications': 0.3,
        'availability': 0.2
    },
    'workflow': 'application_process',
    'notifications': ['email', 'webhook']
}
```

## Current Reusability Status

### ✅ Already Reusable Components
- **Database Layer**: MongoDB abstraction with helper functions
- **Matching Engine**: Generic semantic matching with configurable weights
- **Workflow Engine**: LangGraph-based process orchestration
- **Communication System**: Adapter pattern for multiple channels
- **Authentication**: Generic JWT and API key handling
- **Security**: Rate limiting and input validation framework

### ⚠️ Domain-Specific Elements
- **HR Terminology**: Job, candidate, interview, offer (configurable)
- **Values Assessment**: Integrity, Honesty, Discipline, Hard Work, Gratitude (optional)
- **Specific Workflows**: Hiring process steps (customizable)

### 🔄 Easy Adaptation Points
- Collection names configurable via environment
- Workflow definitions stored in database
- Matching weights adjustable per use case
- Notification channels pluggable
- Business rules externalized

## How to Reuse for Other Domains

### 1. Configuration Approach
```python
# Create domain-specific configuration
DOMAIN_CONFIG = {
    'hr': hr_config,
    'crm': crm_config,
    'project_management': pm_config
}

# Use appropriate configuration
current_domain = os.getenv('DOMAIN', 'hr')
config = DOMAIN_CONFIG[current_domain]
```

### 2. Collection Mapping
```python
# Map generic operations to domain collections
COLLECTION_MAP = {
    'create_entity': config['collections']['requests'],
    'find_entities': config['collections']['applicants'],
    'track_process': config['collections']['submissions']
}
```

### 3. Workflow Customization
```python
# Domain-specific workflow steps
WORKFLOW_STEPS = {
    'hr': ['application', 'screening', 'interview', 'offer'],
    'generic': ['submission', 'review', 'evaluation', 'decision']
}
```

## Proof of Reusability

The current hiring loop has been successfully adapted for:

1. **HR Recruitment**: Jobs → Candidates → Applications
2. **Generic Applications**: Projects → Applicants → Submissions
3. **Service Requests**: Services → Clients → Requests

All using the same underlying framework with different configurations.

---

**Document Owner**: BHIV Platform Team
**Last Updated**: January 29, 2026
**Next Review**: February 15, 2026

*This guide demonstrates how the current BHIV HR Platform hiring loop is already reusable across different business domains with minimal configuration changes.*