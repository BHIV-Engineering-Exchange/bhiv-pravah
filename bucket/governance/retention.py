"""
Document 06: Retention Posture
Data deletion and lifecycle policy
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

# Retention configuration (tunable via environment variables)
RETENTION_CONFIG = {
    "redis_execution_ttl": int(os.getenv("REDIS_EXECUTION_TTL", "86400")),  # 24 hours
    "mongodb_log_retention_days": int(os.getenv("MONGODB_LOG_RETENTION_DAYS", "365")),  # 1 year
    "file_log_max_size": int(os.getenv("FILE_LOG_MAX_SIZE", "10485760")),  # 10MB
    "file_log_backup_count": int(os.getenv("FILE_LOG_BACKUP_COUNT", "5")),
    "error_log_backup_count": int(os.getenv("ERROR_LOG_BACKUP_COUNT", "3")),
    "tombstone_period_days": int(os.getenv("TOMBSTONE_PERIOD_DAYS", "90")),
    "enable_auto_cleanup": os.getenv("ENABLE_AUTO_CLEANUP", "true").lower() == "true",
    "gdpr_anonymize": os.getenv("GDPR_ANONYMIZE", "false").lower() == "true"
}

# Per-artifact retention rules
ARTIFACT_RETENTION_RULES = {
    "agent_specifications": {
        "retention": "permanent",
        "strategy": "keep_forever",
        "notes": "v1 reference baseline"
    },
    "basket_configurations": {
        "retention": "permanent",
        "strategy": "keep_forever",
        "notes": "workflow definitions"
    },
    "execution_metadata": {
        "retention": "1_year",
        "strategy": "ttl_mongodb",
        "redis_ttl": "1_hour",
        "notes": "execution tracking"
    },
    "agent_outputs": {
        "retention": "1_year",
        "strategy": "ttl_mongodb",
        "redis_ttl": "1_hour",
        "notes": "agent results"
    },
    "logs_success": {
        "retention": "1_year",
        "strategy": "file_rotation",
        "backups": 5,
        "notes": "successful executions"
    },
    "logs_error": {
        "retention": "1_year",
        "strategy": "file_rotation",
        "backups": 3,
        "notes": "error tracking"
    },
    "agent_state": {
        "retention": "1_hour",
        "strategy": "ttl_redis",
        "notes": "temporary state"
    },
    "metrics": {
        "retention": "1_month",
        "strategy": "ttl_redis",
        "notes": "aggregate only"
    }
}

# Data lifecycle stages
DATA_LIFECYCLE = {
    "day_0": {
        "stage": "execution",
        "redis": "store_with_ttl_1_24hr",
        "mongodb": "store_with_ttl_1yr",
        "files": "append_to_log"
    },
    "day_1_30": {
        "stage": "available_for_analysis",
        "redis": "may_still_be_available",
        "mongodb": "available",
        "files": "available"
    },
    "day_30": {
        "stage": "data_older_than_1_month",
        "redis": "expired_and_cleaned",
        "mongodb": "still_available",
        "files": "rotated_but_available"
    },
    "day_365": {
        "stage": "data_older_than_1_year",
        "redis": "long_since_expired",
        "mongodb": "ttl_triggers_deletion",
        "files": "moved_to_archive_then_deleted"
    }
}

# GDPR deletion process
GDPR_DELETION_PROCESS = {
    "current": {
        "steps": [
            "user_requests_deletion",
            "audit_review_determines_scope",
            "tombstone_with_deletion_timestamp",
            "wait_90_days_for_audit",
            "hard_delete_after_audit_period",
            "verify_deletion_in_all_systems"
        ],
        "timeline": "90_days",
        "automation": "manual"
    },
    "phase_2_q2_2026": {
        "steps": [
            "automated_pii_detection",
            "automatic_anonymization",
            "audit_trail_of_deletion",
            "compliance_reporting"
        ],
        "timeline": "30_days",
        "automation": "automated"
    }
}

# Legal hold process
LEGAL_HOLD_PROCESS = {
    "trigger": "legal_sends_data_hold_request",
    "actions": [
        "flag_data_as_hold_in_mongodb",
        "prevent_automatic_deletion",
        "wait_for_legal_clearance",
        "proceed_with_normal_retention"
    ],
    "schema": {
        "legal_hold": True,
        "hold_date": "ISO_date",
        "hold_reason": "case_reference"
    }
}

# Storage impact analysis
STORAGE_IMPACT = {
    "current_daily": {
        "executions_per_day": 100,
        "size_per_execution_kb": 50,
        "daily_mb": 5,
        "monthly_mb": 150,
        "yearly_gb": 1.8
    },
    "breakdown": {
        "redis_mb": 50,
        "mongodb_yearly_gb": 1.8,
        "file_logs_mb": 500,
        "total_after_1_year_gb": 2.4
    },
    "scaling_projections": {
        "1000_executions_per_day": "24GB/year",
        "10000_executions_per_day": "240GB/year (archive needed)"
    }
}

# Compliance checklist
COMPLIANCE_CHECKLIST = {
    "retention_policy_documented": {"status": "complete", "reference": "Document 06"},
    "deletion_procedure_tested": {"status": "ready", "notes": "manual and automated"},
    "storage_capacity_planned": {"status": "complete", "capacity": "2.4GB/year baseline"},
    "gdpr_procedures_ready": {"status": "manual", "phase_2": "Q2 2026"},
    "legal_hold_capability": {"status": "ready", "implementation": "mongodb_flag"},
    "backup_strategy": {"status": "complete", "rotation": "5 backups"},
    "disaster_recovery": {"status": "ready", "notes": "file rotation + mongodb"},
    "regular_cleanup_runs": {"status": "automated", "frequency": "daily"}
}


def get_retention_config() -> Dict[str, Any]:
    """Get current retention configuration"""
    return {
        "config": RETENTION_CONFIG,
        "tunable_via": ".env file",
        "parameters": {
            "REDIS_EXECUTION_TTL": "seconds (default: 86400 = 24 hours)",
            "MONGODB_LOG_RETENTION_DAYS": "days (default: 365 = 1 year)",
            "FILE_LOG_MAX_SIZE": "bytes (default: 10485760 = 10MB)",
            "FILE_LOG_BACKUP_COUNT": "count (default: 5)",
            "ERROR_LOG_BACKUP_COUNT": "count (default: 3)",
            "TOMBSTONE_PERIOD_DAYS": "days (default: 90)",
            "ENABLE_AUTO_CLEANUP": "boolean (default: true)",
            "GDPR_ANONYMIZE": "boolean (default: false, Phase 2)"
        }
    }


def get_artifact_retention_rules() -> Dict[str, Any]:
    """Get retention rules for all artifact types"""
    return {
        "rules": ARTIFACT_RETENTION_RULES,
        "summary": {
            "permanent": ["agent_specifications", "basket_configurations"],
            "1_year": ["execution_metadata", "agent_outputs", "logs_success", "logs_error"],
            "1_month": ["metrics"],
            "1_hour": ["agent_state"]
        }
    }


def get_data_lifecycle() -> Dict[str, Any]:
    """Get data lifecycle stages"""
    return {
        "lifecycle": DATA_LIFECYCLE,
        "visualization": """
Day 0: Execution happens
├─ Redis: Store (1-24hr TTL)
├─ MongoDB: Store (1yr TTL)
└─ Files: Append to log

Day 1-30: Available for analysis
├─ Redis: May still be available
├─ MongoDB: Available
└─ Files: Available

Day 30: Data older than 1 month
├─ Redis: Expired and cleaned
├─ MongoDB: Still available
└─ Files: Rotated but available

Day 365: Data older than 1 year
├─ Redis: Long since expired
├─ MongoDB: TTL index triggers deletion
└─ Files: Moved to archive, then deleted
        """
    }


def get_deletion_strategy() -> Dict[str, Any]:
    """Get deletion strategy details"""
    return {
        "strategy": "tombstoning_plus_ttl",
        "layers": {
            "layer_1_tombstoning": {
                "description": "Soft delete with audit trail",
                "process": [
                    "mark_with_deletion_timestamp",
                    "keep_for_audit_trail_1_3_months",
                    "then_hard_delete"
                ]
            },
            "layer_2_ttl": {
                "description": "Automatic cleanup",
                "redis": "1-24 hours (auto-expire)",
                "mongodb": "1 year (TTL index)",
                "files": "manual rotation, keep 5-10 backups"
            }
        }
    }


def get_gdpr_process() -> Dict[str, Any]:
    """Get GDPR right-to-be-forgotten process"""
    return {
        "gdpr_deletion": GDPR_DELETION_PROCESS,
        "timeline": "90 days (current), 30 days (Phase 2)",
        "compliance": "GDPR Article 17"
    }


def get_legal_hold_process() -> Dict[str, Any]:
    """Get legal hold process"""
    return {
        "process": LEGAL_HOLD_PROCESS,
        "example": {
            "legal_hold": True,
            "hold_date": "2026-01-15",
            "hold_reason": "Litigation case #123"
        },
        "implementation": "mongodb_flag_prevents_deletion"
    }


def get_storage_impact() -> Dict[str, Any]:
    """Get storage impact analysis"""
    return {
        "impact": STORAGE_IMPACT,
        "recommendation": "Monitor usage; archive if exceeding 100GB/year"
    }


def get_cleanup_procedures() -> Dict[str, Any]:
    """Get cleanup procedures"""
    return {
        "automated": {
            "redis_ttl": "automatic after 1-24 hours",
            "mongodb_ttl": "automatic after 1 year (configured)",
            "file_logs": "automatic rotation (daily)"
        },
        "manual": {
            "tombstone_cleanup": {
                "description": "Delete tombstoned data after 90 days",
                "command": "db.logs.deleteMany({deleted: true, deletion_timestamp: {$lt: ISODate('90 days ago')}})"
            },
            "old_logs_cleanup": {
                "description": "Delete logs older than 1 year",
                "command": "db.logs.deleteMany({timestamp: {$lt: ISODate('1 year ago')}})"
            }
        }
    }


def get_compliance_checklist() -> Dict[str, Any]:
    """Get compliance checklist"""
    return {
        "checklist": COMPLIANCE_CHECKLIST,
        "overall_status": "compliant",
        "phase_2_enhancements": "Q2 2026 (automated GDPR)"
    }


def calculate_retention_date(artifact_type: str, created_date: Optional[datetime] = None) -> Dict[str, Any]:
    """Calculate when data should be deleted based on artifact type"""
    if created_date is None:
        created_date = datetime.utcnow()
    
    rules = ARTIFACT_RETENTION_RULES.get(artifact_type, {})
    retention = rules.get("retention", "unknown")
    
    if retention == "permanent":
        return {
            "artifact_type": artifact_type,
            "created_date": created_date.isoformat(),
            "deletion_date": "never",
            "retention_period": "permanent"
        }
    elif retention == "1_year":
        deletion_date = created_date + timedelta(days=365)
        return {
            "artifact_type": artifact_type,
            "created_date": created_date.isoformat(),
            "deletion_date": deletion_date.isoformat(),
            "retention_period": "1 year",
            "days_remaining": (deletion_date - datetime.utcnow()).days
        }
    elif retention == "1_month":
        deletion_date = created_date + timedelta(days=30)
        return {
            "artifact_type": artifact_type,
            "created_date": created_date.isoformat(),
            "deletion_date": deletion_date.isoformat(),
            "retention_period": "1 month",
            "days_remaining": (deletion_date - datetime.utcnow()).days
        }
    elif retention == "1_hour":
        deletion_date = created_date + timedelta(hours=1)
        return {
            "artifact_type": artifact_type,
            "created_date": created_date.isoformat(),
            "deletion_date": deletion_date.isoformat(),
            "retention_period": "1 hour",
            "minutes_remaining": int((deletion_date - datetime.utcnow()).total_seconds() / 60)
        }
    else:
        return {
            "artifact_type": artifact_type,
            "created_date": created_date.isoformat(),
            "deletion_date": "unknown",
            "retention_period": "unknown",
            "error": "artifact type not found in retention rules"
        }


def get_dsar_process() -> Dict[str, Any]:
    """Get Data Subject Access Request process"""
    return {
        "dsar": {
            "description": "Data Subject Access Request (GDPR Article 15)",
            "timeline": "30 days (GDPR requirement)",
            "current_process": [
                "subject_requests_their_data",
                "find_all_logs_mentioning_them (limited, no user tracking yet)",
                "export_data_in_machine_readable_format",
                "verify_before_sending",
                "keep_record_of_export"
            ],
            "limitations": "No user tracking in v1.0.0 - limited data retrieval",
            "phase_2": "Q2 2026 - automated PII detection and export"
        }
    }
