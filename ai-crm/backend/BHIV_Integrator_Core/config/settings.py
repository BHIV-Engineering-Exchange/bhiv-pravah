"""
Configuration settings for BHIV Integrator Core
"""

import os
from typing import Dict, Any

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bhiv_integrator.db")

# BHIV Core settings
BHIV_CORE_URL = os.getenv("BHIV_CORE_URL", "http://localhost:8002")
BHIV_CORE_API_KEY = os.getenv("BHIV_CORE_API_KEY", "uniguru-dev-key-2025")

# UniGuru settings
UNIGURU_URL = os.getenv("UNIGURU_URL", "http://localhost:8001")
UNIGURU_API_KEY = os.getenv("UNIGURU_API_KEY", "uniguru-dev-key-2025")

# Gurukul settings
GURUKUL_URL = os.getenv("GURUKUL_URL", "http://localhost:8001")

# Event Broker settings
EVENT_BROKER_PORT = int(os.getenv("EVENT_BROKER_PORT", "8006"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "bhiv_events")
RABBITMQ_QUEUE_PREFIX = os.getenv("RABBITMQ_QUEUE_PREFIX", "bhiv_queue_")

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Compliance settings
COMPLIANCE_ENABLED = os.getenv("COMPLIANCE_ENABLED", "true").lower() == "true"
SANKALP_COMPLIANCE_URL = os.getenv("SANKALP_COMPLIANCE_URL", "http://localhost:8007")

# Module endpoints (relative to this integrator)
LOGISTICS_BASE_URL = os.getenv("LOGISTICS_BASE_URL", "http://localhost:8000")
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "http://localhost:8502")
TASK_BASE_URL = os.getenv("TASK_BASE_URL", "http://localhost:8000")

# Event triggers configuration
EVENT_TRIGGERS = {
    "order_created": ["create_crm_lead", "create_task"],
    "delivery_delayed": ["escalate_task", "notify_crm", "send_slack_alert", "send_teams_alert"],
    "account_status_changed": ["update_dashboard", "compliance_check"],
    "task_completed": ["update_crm_opportunity", "log_compliance"],
    "inventory_low": ["send_slack_alert"],
    "compliance_violation": ["send_teams_alert", "escalate_task"]
}

# DHI Score configuration
DHI_SCORE_WEIGHTS = {
    "compliance": 0.4,
    "efficiency": 0.3,
    "quality": 0.2,
    "timeliness": 0.1
}

# Compliance flags
COMPLIANCE_FLAGS = {
    "gdpr_compliant": False,
    "data_encrypted": False,
    "audit_trail": True,
    "access_controlled": False
}

# Notification settings
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")

settings = {
    "database_url": DATABASE_URL,
    "bhiv_core_url": BHIV_CORE_URL,
    "bhiv_core_api_key": BHIV_CORE_API_KEY,
    "uniguru_url": UNIGURU_URL,
    "uniguru_api_key": UNIGURU_API_KEY,
    "gurukul_url": GURUKUL_URL,
    "event_broker_port": EVENT_BROKER_PORT,
    "redis_url": REDIS_URL,
    "rabbitmq_url": RABBITMQ_URL,
    "rabbitmq_exchange": RABBITMQ_EXCHANGE,
    "rabbitmq_queue_prefix": RABBITMQ_QUEUE_PREFIX,
    "log_level": LOG_LEVEL,
    "log_format": LOG_FORMAT,
    "compliance_enabled": COMPLIANCE_ENABLED,
    "sankalp_compliance_url": SANKALP_COMPLIANCE_URL,
    "logistics_base_url": LOGISTICS_BASE_URL,
    "crm_base_url": CRM_BASE_URL,
    "task_base_url": TASK_BASE_URL,
    "event_triggers": EVENT_TRIGGERS,
    "dhi_score_weights": DHI_SCORE_WEIGHTS,
    "compliance_flags": COMPLIANCE_FLAGS,
    "slack_webhook_url": SLACK_WEBHOOK_URL,
    "teams_webhook_url": TEAMS_WEBHOOK_URL
}