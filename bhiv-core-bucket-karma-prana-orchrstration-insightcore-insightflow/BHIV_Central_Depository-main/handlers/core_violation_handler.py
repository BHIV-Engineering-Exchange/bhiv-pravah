"""
BHIV Core Violation Handler
Detects, logs, and escalates constitutional boundary violations
Implements escalation protocols and automated responses
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from utils.logger import get_logger

logger = get_logger(__name__)

class ViolationSeverity(Enum):
    """Severity levels for violations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EscalationLevel(Enum):
    """Escalation levels"""
    NONE = "none"
    OPS_TEAM = "ops_team"
    EXECUTOR = "executor"
    ADVISOR = "advisor"
    OWNER = "owner"
    CEO = "ceo"

class AutomatedResponse(Enum):
    """Automated responses to violations"""
    LOG_ONLY = "log_only"
    WARN = "warn"
    THROTTLE = "throttle"
    BLOCK = "block"
    HALT = "halt"

class CoreViolationHandler:
    """Handles detection and escalation of Core boundary violations"""
    
    def __init__(self, audit_middleware=None):
        self.audit_middleware = audit_middleware
        self.violation_history = []
        self.escalation_contacts = self._define_escalation_contacts()
        self.response_rules = self._define_response_rules()
        logger.info("Core Violation Handler initialized")
    
    def handle_violation(
        self,
        violation_type: str,
        severity: str,
        details: Dict[str, Any],
        requester_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a boundary violation
        
        Args:
            violation_type: Type of violation
            severity: Severity level
            details: Violation details
            requester_id: ID of violating system
            context: Additional context
            
        Returns:
            Response action taken
        """
        context = context or {}
        
        # Create violation record
        violation = {
            "violation_id": self._generate_violation_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "violation_type": violation_type,
            "severity": severity,
            "requester_id": requester_id,
            "details": details,
            "context": context
        }
        
        # Log violation
        self._log_violation(violation)
        
        # Determine automated response
        response = self._determine_response(violation)
        violation["response"] = response
        
        # Execute automated response
        self._execute_response(response, violation)
        
        # Determine escalation
        escalation = self._determine_escalation(violation)
        violation["escalation"] = escalation
        
        # Execute escalation if needed
        if escalation["level"] != EscalationLevel.NONE.value:
            self._execute_escalation(escalation, violation)
        
        # Store in history
        self.violation_history.append(violation)
        
        # Log to audit trail if available
        if self.audit_middleware:
            self._log_to_audit(violation)
        
        logger.info(f"Violation handled: {violation['violation_id']}")
        
        return {
            "violation_id": violation["violation_id"],
            "response_action": response["action"],
            "escalation_level": escalation["level"],
            "blocked": response["action"] in [AutomatedResponse.BLOCK.value, AutomatedResponse.HALT.value]
        }
    
    def _generate_violation_id(self) -> str:
        """Generate unique violation ID"""
        import uuid
        timestamp = int(datetime.utcnow().timestamp())
        return f"VIO_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    def _log_violation(self, violation: Dict[str, Any]):
        """Log violation to system logs"""
        severity = violation["severity"]
        vtype = violation["violation_type"]
        requester = violation["requester_id"]
        
        log_message = f"BOUNDARY VIOLATION: {vtype} by {requester} (Severity: {severity})"
        
        if severity == ViolationSeverity.CRITICAL.value:
            logger.critical(log_message)
        elif severity == ViolationSeverity.HIGH.value:
            logger.error(log_message)
        elif severity == ViolationSeverity.MEDIUM.value:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _determine_response(self, violation: Dict[str, Any]) -> Dict[str, Any]:
        """Determine automated response based on violation"""
        severity = violation["severity"]
        vtype = violation["violation_type"]
        
        # Get response rule
        rule = self.response_rules.get(vtype, self.response_rules.get("default"))
        
        # Adjust based on severity
        if severity == ViolationSeverity.CRITICAL.value:
            action = AutomatedResponse.HALT.value
        elif severity == ViolationSeverity.HIGH.value:
            action = AutomatedResponse.BLOCK.value
        elif severity == ViolationSeverity.MEDIUM.value:
            action = rule.get("medium_action", AutomatedResponse.THROTTLE.value)
        else:
            action = rule.get("low_action", AutomatedResponse.WARN.value)
        
        return {
            "action": action,
            "reason": rule.get("reason", "Boundary violation detected"),
            "duration": rule.get("duration", None)
        }
    
    def _execute_response(self, response: Dict[str, Any], violation: Dict[str, Any]):
        """Execute automated response"""
        action = response["action"]
        
        if action == AutomatedResponse.HALT.value:
            logger.critical(f"HALTING OPERATIONS due to violation: {violation['violation_id']}")
            # In production, this would trigger system-wide halt
            
        elif action == AutomatedResponse.BLOCK.value:
            logger.error(f"BLOCKING request due to violation: {violation['violation_id']}")
            # Request is blocked, logged, and escalated
            
        elif action == AutomatedResponse.THROTTLE.value:
            logger.warning(f"THROTTLING requester due to violation: {violation['violation_id']}")
            # Implement rate limiting for requester
            
        elif action == AutomatedResponse.WARN.value:
            logger.info(f"WARNING issued for violation: {violation['violation_id']}")
            # Warning logged, no blocking
    
    def _determine_escalation(self, violation: Dict[str, Any]) -> Dict[str, Any]:
        """Determine escalation level and contacts"""
        severity = violation["severity"]
        vtype = violation["violation_type"]
        
        # Escalation matrix
        escalation_matrix = {
            ViolationSeverity.CRITICAL.value: {
                "level": EscalationLevel.OWNER.value,
                "timeline": "IMMEDIATE",
                "contacts": ["ashmit_pandey", "vijay_dhawan"]
            },
            ViolationSeverity.HIGH.value: {
                "level": EscalationLevel.ADVISOR.value,
                "timeline": "1_HOUR",
                "contacts": ["vijay_dhawan"]
            },
            ViolationSeverity.MEDIUM.value: {
                "level": EscalationLevel.EXECUTOR.value,
                "timeline": "6_HOURS",
                "contacts": ["akanksha_parab"]
            },
            ViolationSeverity.LOW.value: {
                "level": EscalationLevel.OPS_TEAM.value,
                "timeline": "24_HOURS",
                "contacts": ["ops_team"]
            }
        }
        
        escalation = escalation_matrix.get(
            severity,
            {"level": EscalationLevel.NONE.value, "timeline": "N/A", "contacts": []}
        )
        
        # Special escalations for specific violation types
        if vtype in ["schema_mutation", "audit_tampering", "governance_bypass"]:
            escalation["level"] = EscalationLevel.CEO.value
            escalation["timeline"] = "IMMEDIATE"
            escalation["contacts"] = ["ceo", "ashmit_pandey", "vijay_dhawan"]
        
        return escalation
    
    def _execute_escalation(self, escalation: Dict[str, Any], violation: Dict[str, Any]):
        """Execute escalation protocol"""
        level = escalation["level"]
        contacts = escalation["contacts"]
        timeline = escalation["timeline"]
        
        logger.warning(f"ESCALATING to {level}: {violation['violation_id']}")
        logger.warning(f"Timeline: {timeline}, Contacts: {contacts}")
        
        # In production, this would:
        # 1. Send notifications to contacts
        # 2. Create escalation tickets
        # 3. Trigger alerts
        # 4. Update dashboards
        
        # For now, log the escalation
        escalation_log = {
            "violation_id": violation["violation_id"],
            "escalation_level": level,
            "contacts_notified": contacts,
            "timeline": timeline,
            "escalated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Escalation executed: {escalation_log}")
    
    def _log_to_audit(self, violation: Dict[str, Any]):
        """Log violation to audit trail"""
        try:
            import asyncio
            
            # Create audit entry
            asyncio.create_task(
                self.audit_middleware.log_operation(
                    operation_type="BOUNDARY_VIOLATION",
                    artifact_id="system",
                    requester_id=violation["requester_id"],
                    integration_id="core_boundary_enforcer",
                    data_after=violation,
                    status="violation_detected",
                    error_message=f"{violation['violation_type']}: {violation['severity']}"
                )
            )
        except Exception as e:
            logger.error(f"Failed to log violation to audit: {e}")
    
    def _define_escalation_contacts(self) -> Dict[str, List[str]]:
        """Define escalation contact lists"""
        return {
            EscalationLevel.OPS_TEAM.value: ["ops@bhiv.com"],
            EscalationLevel.EXECUTOR.value: ["akanksha_parab@bhiv.com"],
            EscalationLevel.ADVISOR.value: ["vijay_dhawan@bhiv.com"],
            EscalationLevel.OWNER.value: ["ashmit_pandey@bhiv.com"],
            EscalationLevel.CEO.value: ["ceo@bhiv.com", "ashmit_pandey@bhiv.com"]
        }
    
    def _define_response_rules(self) -> Dict[str, Dict]:
        """Define automated response rules"""
        return {
            "schema_mutation": {
                "medium_action": AutomatedResponse.BLOCK.value,
                "low_action": AutomatedResponse.BLOCK.value,
                "reason": "Schema mutations are never allowed"
            },
            "deletion_attempt": {
                "medium_action": AutomatedResponse.BLOCK.value,
                "low_action": AutomatedResponse.BLOCK.value,
                "reason": "Deletions require governance approval"
            },
            "audit_hiding": {
                "medium_action": AutomatedResponse.HALT.value,
                "low_action": AutomatedResponse.BLOCK.value,
                "reason": "Audit trail must be complete"
            },
            "governance_bypass": {
                "medium_action": AutomatedResponse.HALT.value,
                "low_action": AutomatedResponse.BLOCK.value,
                "reason": "Governance cannot be bypassed"
            },
            "default": {
                "medium_action": AutomatedResponse.THROTTLE.value,
                "low_action": AutomatedResponse.WARN.value,
                "reason": "Boundary violation detected"
            }
        }
    
    def get_violation_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate violation report for last N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent_violations = [
            v for v in self.violation_history
            if datetime.fromisoformat(v["timestamp"]) > cutoff
        ]
        
        return {
            "report_generated": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "total_violations": len(recent_violations),
            "by_severity": self._group_by_severity(recent_violations),
            "by_type": self._group_by_type(recent_violations),
            "by_requester": self._group_by_requester(recent_violations),
            "escalations": self._count_escalations(recent_violations),
            "violations": recent_violations
        }
    
    def _group_by_severity(self, violations: List[Dict]) -> Dict[str, int]:
        """Group violations by severity"""
        grouped = {}
        for v in violations:
            severity = v.get("severity", "unknown")
            grouped[severity] = grouped.get(severity, 0) + 1
        return grouped
    
    def _group_by_type(self, violations: List[Dict]) -> Dict[str, int]:
        """Group violations by type"""
        grouped = {}
        for v in violations:
            vtype = v.get("violation_type", "unknown")
            grouped[vtype] = grouped.get(vtype, 0) + 1
        return grouped
    
    def _group_by_requester(self, violations: List[Dict]) -> Dict[str, int]:
        """Group violations by requester"""
        grouped = {}
        for v in violations:
            requester = v.get("requester_id", "unknown")
            grouped[requester] = grouped.get(requester, 0) + 1
        return grouped
    
    def _count_escalations(self, violations: List[Dict]) -> Dict[str, int]:
        """Count escalations by level"""
        escalations = {}
        for v in violations:
            level = v.get("escalation", {}).get("level", "none")
            escalations[level] = escalations.get(level, 0) + 1
        return escalations

# Global violation handler instance
core_violation_handler = CoreViolationHandler()
