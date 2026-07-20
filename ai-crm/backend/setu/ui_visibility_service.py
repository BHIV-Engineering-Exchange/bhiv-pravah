from datetime import datetime
from typing import Any, Dict, List, Optional

from .mongo_store import MongoSetuStore
from .niyantran_integration_adapter import NiyantranIntegrationAdapter


class SetuUIVisibilityService:
    """SETU UI Visibility Service - READ ONLY, NO EXECUTION"""
    
    def __init__(self, store: MongoSetuStore, niyantran_adapter: NiyantranIntegrationAdapter):
        self.store = store
        self.niyantran_adapter = niyantran_adapter

    async def get_candidate_state(self, trace_id: str) -> Dict[str, Any]:
        """Get candidate state for UI visibility"""
        
        # Get trace record
        trace_record = await self.store.get_trace_by_trace_id(trace_id)
        if not trace_record:
            return {"trace_id": trace_id, "state": "not_found"}
        
        # Get execution timeline
        timeline = await self.niyantran_adapter.get_execution_timeline(trace_id)
        
        # Determine current state based on timeline
        current_state = "unknown"
        if timeline["timeline"]:
            latest_event = timeline["timeline"][-1]
            
            if latest_event["type"] == "task_state":
                current_state = latest_event["data"]["state"]
            elif latest_event["type"] == "submission_state":
                current_state = f"submission_{latest_event['data']['state']}"
            elif latest_event["type"] == "execution_status":
                current_state = latest_event["data"]["status"]
        
        return {
            "trace_id": trace_id,
            "candidate_id": trace_record.get("execution_id"),
            "current_state": current_state,
            "tenant_id": trace_record.get("tenant_id"),
            "last_updated": timeline["timeline"][-1]["timestamp"] if timeline["timeline"] else None,
            "total_events": len(timeline["timeline"])
        }

    async def get_task_state_visibility(self, trace_id: str) -> Dict[str, Any]:
        """Get task state for UI visibility"""
        
        task_states = await self.niyantran_adapter.get_task_states(trace_id)
        
        # Organize by task_id
        tasks_by_id = {}
        for task_state in task_states:
            task_id = task_state["task_id"]
            if task_id not in tasks_by_id:
                tasks_by_id[task_id] = []
            tasks_by_id[task_id].append(task_state)
        
        # Get current state for each task
        task_summary = []
        for task_id, states in tasks_by_id.items():
            # Sort by timestamp to get latest state
            states.sort(key=lambda x: x["timestamp"], reverse=True)
            latest_state = states[0]
            
            task_summary.append({
                "task_id": task_id,
                "current_state": latest_state["state"],
                "last_updated": latest_state["timestamp"],
                "total_state_changes": len(states),
                "metadata": latest_state.get("metadata", {})
            })
        
        return {
            "trace_id": trace_id,
            "tasks": task_summary,
            "total_tasks": len(task_summary)
        }

    async def get_signal_visibility(self, trace_id: str) -> Dict[str, Any]:
        """Get signals for UI visibility"""
        
        signals = await self.store.list_signal_ingestion(trace_id)
        
        # Organize signals by severity
        signals_by_severity = {"low": [], "medium": [], "high": [], "critical": []}
        
        for signal in signals:
            severity = signal.get("severity", "unknown")
            if severity in signals_by_severity:
                signals_by_severity[severity].append({
                    "signal_id": signal.get("ingestion_id"),
                    "entity_id": signal.get("entity_id"),
                    "event_type": signal.get("event_type"),
                    "signal_type": signal.get("signal_type"),
                    "timestamp": signal.get("timestamp"),
                    "ingested_at": signal.get("ingested_at")
                })
        
        return {
            "trace_id": trace_id,
            "signals_by_severity": signals_by_severity,
            "total_signals": len(signals),
            "severity_counts": {
                severity: len(signal_list) 
                for severity, signal_list in signals_by_severity.items()
            }
        }

    async def get_severity_dashboard(self, trace_id: str) -> Dict[str, Any]:
        """Get severity dashboard for UI visibility"""
        
        signals = await self.store.list_signal_ingestion(trace_id)
        
        severity_analysis = {
            "critical_count": 0,
            "high_count": 0, 
            "medium_count": 0,
            "low_count": 0,
            "overall_severity": "low",
            "latest_critical": None,
            "trend": []
        }
        
        # Count severities and find latest critical
        for signal in signals:
            severity = signal.get("severity", "unknown")
            
            if severity == "critical":
                severity_analysis["critical_count"] += 1
                if not severity_analysis["latest_critical"] or signal["timestamp"] > severity_analysis["latest_critical"]["timestamp"]:
                    severity_analysis["latest_critical"] = signal
            elif severity == "high":
                severity_analysis["high_count"] += 1
            elif severity == "medium":
                severity_analysis["medium_count"] += 1
            elif severity == "low":
                severity_analysis["low_count"] += 1
        
        # Determine overall severity
        if severity_analysis["critical_count"] > 0:
            severity_analysis["overall_severity"] = "critical"
        elif severity_analysis["high_count"] > 0:
            severity_analysis["overall_severity"] = "high"
        elif severity_analysis["medium_count"] > 0:
            severity_analysis["overall_severity"] = "medium"
        
        return {
            "trace_id": trace_id,
            "severity_analysis": severity_analysis
        }

    async def get_execution_timeline_ui(self, trace_id: str) -> Dict[str, Any]:
        """Get execution timeline for UI display"""
        
        timeline = await self.niyantran_adapter.get_execution_timeline(trace_id)
        
        # Enhance timeline for UI display
        enhanced_timeline = []
        for event in timeline["timeline"]:
            ui_event = {
                "timestamp": event["timestamp"],
                "type": event["type"],
                "title": self._get_event_title(event),
                "description": self._get_event_description(event),
                "status": self._get_event_status(event),
                "icon": self._get_event_icon(event["type"]),
                "color": self._get_event_color(event),
                "data": event["data"]
            }
            enhanced_timeline.append(ui_event)
        
        return {
            "trace_id": trace_id,
            "timeline": enhanced_timeline,
            "summary": timeline["summary"]
        }

    def _get_event_title(self, event: Dict[str, Any]) -> str:
        """Get UI-friendly event title"""
        event_type = event["type"]
        data = event["data"]
        
        if event_type == "task_state":
            return f"Task {data.get('task_id', 'Unknown')} - {data.get('state', 'Unknown')}"
        elif event_type == "submission_state":
            return f"Submission {data.get('submission_id', 'Unknown')} - {data.get('state', 'Unknown')}"
        elif event_type == "execution_status":
            return f"Execution {data.get('execution_id', 'Unknown')} - {data.get('status', 'Unknown')}"
        
        return event_type

    def _get_event_description(self, event: Dict[str, Any]) -> str:
        """Get UI-friendly event description"""
        data = event["data"]
        metadata = data.get("metadata", {})
        
        if metadata:
            return f"Metadata: {str(metadata)[:100]}..."
        
        return "No additional details"

    def _get_event_status(self, event: Dict[str, Any]) -> str:
        """Get event status for UI styling"""
        data = event["data"]
        
        if event["type"] == "task_state":
            state = data.get("state", "").lower()
            if state in ["completed", "success"]:
                return "success"
            elif state in ["failed", "error"]:
                return "error"
            elif state in ["running", "in_progress"]:
                return "running"
            else:
                return "pending"
        
        return "info"

    def _get_event_icon(self, event_type: str) -> str:
        """Get icon for event type"""
        icons = {
            "task_state": "task",
            "submission_state": "submit", 
            "execution_status": "execute"
        }
        return icons.get(event_type, "event")

    def _get_event_color(self, event: Dict[str, Any]) -> str:
        """Get color for event based on status"""
        status = self._get_event_status(event)
        
        colors = {
            "success": "green",
            "error": "red",
            "running": "blue",
            "pending": "orange",
            "info": "gray"
        }
        
        return colors.get(status, "gray")

    async def get_visibility_dashboard(self, trace_id: str) -> Dict[str, Any]:
        """Get complete visibility dashboard - NO EXECUTION BUTTONS"""
        
        candidate_state = await self.get_candidate_state(trace_id)
        task_state = await self.get_task_state_visibility(trace_id)
        signal_visibility = await self.get_signal_visibility(trace_id)
        severity_dashboard = await self.get_severity_dashboard(trace_id)
        timeline = await self.get_execution_timeline_ui(trace_id)
        
        return {
            "trace_id": trace_id,
            "dashboard_type": "visibility_only",
            "no_execution_actions": True,
            "no_workflow_mutations": True,
            "candidate_state": candidate_state,
            "task_state": task_state,
            "signal_visibility": signal_visibility,
            "severity_dashboard": severity_dashboard,
            "timeline": timeline,
            "generated_at": datetime.utcnow().isoformat()
        }