from datetime import datetime
from typing import Any, Dict, List, Optional

from .mongo_store import MongoSetuStore


class NiyantranIntegrationAdapter:
    """Niyantran execution visibility integration - READ ONLY"""
    
    def __init__(self, store: MongoSetuStore):
        self.store = store

    async def consume_task_state(self, task_state: Dict[str, Any]) -> Dict[str, Any]:
        """Consume task state from Niyantran for visibility"""
        
        required_fields = ["task_id", "trace_id", "tenant_id", "state", "timestamp"]
        missing = [field for field in required_fields if field not in task_state]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        visibility_record = {
            "record_type": "task_state",
            "task_id": task_state["task_id"],
            "trace_id": task_state["trace_id"],
            "tenant_id": task_state["tenant_id"],
            "state": task_state["state"],
            "timestamp": task_state["timestamp"],
            "metadata": task_state.get("metadata", {}),
            "consumed_at": datetime.utcnow().isoformat(),
            "source": "niyantran"
        }
        
        await self.store.append_visibility_record(visibility_record)
        
        return {
            "success": True,
            "record_type": "task_state",
            "task_id": task_state["task_id"],
            "trace_id": task_state["trace_id"]
        }

    async def consume_submission_state(self, submission_state: Dict[str, Any]) -> Dict[str, Any]:
        """Consume submission state from Niyantran for visibility"""
        
        required_fields = ["submission_id", "task_id", "trace_id", "tenant_id", "state", "timestamp"]
        missing = [field for field in required_fields if field not in submission_state]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        visibility_record = {
            "record_type": "submission_state",
            "submission_id": submission_state["submission_id"],
            "task_id": submission_state["task_id"],
            "trace_id": submission_state["trace_id"],
            "tenant_id": submission_state["tenant_id"],
            "state": submission_state["state"],
            "timestamp": submission_state["timestamp"],
            "result": submission_state.get("result"),
            "metadata": submission_state.get("metadata", {}),
            "consumed_at": datetime.utcnow().isoformat(),
            "source": "niyantran"
        }
        
        await self.store.append_visibility_record(visibility_record)
        
        return {
            "success": True,
            "record_type": "submission_state", 
            "submission_id": submission_state["submission_id"],
            "trace_id": submission_state["trace_id"]
        }

    async def consume_execution_status(self, execution_status: Dict[str, Any]) -> Dict[str, Any]:
        """Consume execution status from Niyantran for visibility"""
        
        required_fields = ["execution_id", "trace_id", "tenant_id", "status", "timestamp"]
        missing = [field for field in required_fields if field not in execution_status]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        visibility_record = {
            "record_type": "execution_status",
            "execution_id": execution_status["execution_id"],
            "trace_id": execution_status["trace_id"], 
            "tenant_id": execution_status["tenant_id"],
            "status": execution_status["status"],
            "timestamp": execution_status["timestamp"],
            "progress": execution_status.get("progress"),
            "errors": execution_status.get("errors", []),
            "metadata": execution_status.get("metadata", {}),
            "consumed_at": datetime.utcnow().isoformat(),
            "source": "niyantran"
        }
        
        await self.store.append_visibility_record(visibility_record)
        
        return {
            "success": True,
            "record_type": "execution_status",
            "execution_id": execution_status["execution_id"],
            "trace_id": execution_status["trace_id"]
        }

    async def get_task_states(self, trace_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task states for visibility display"""
        return await self.store.list_visibility_records(
            trace_id, record_type="task_state", limit=limit
        )

    async def get_submission_states(self, trace_id: str, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get submission states for visibility display"""
        filters = {"record_type": "submission_state"}
        if task_id:
            filters["task_id"] = task_id
            
        return await self.store.list_visibility_records(
            trace_id, filters=filters, limit=limit
        )

    async def get_execution_statuses(self, trace_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution statuses for visibility display"""
        return await self.store.list_visibility_records(
            trace_id, record_type="execution_status", limit=limit
        )

    async def get_execution_timeline(self, trace_id: str) -> Dict[str, Any]:
        """Get complete execution timeline for visibility"""
        
        task_states = await self.get_task_states(trace_id)
        submission_states = await self.get_submission_states(trace_id)
        execution_statuses = await self.get_execution_statuses(trace_id)
        
        # Combine and sort by timestamp
        all_events = []
        
        for task in task_states:
            all_events.append({
                "type": "task_state",
                "timestamp": task["timestamp"],
                "data": task
            })
        
        for submission in submission_states:
            all_events.append({
                "type": "submission_state", 
                "timestamp": submission["timestamp"],
                "data": submission
            })
        
        for execution in execution_statuses:
            all_events.append({
                "type": "execution_status",
                "timestamp": execution["timestamp"],
                "data": execution
            })
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x["timestamp"])
        
        return {
            "trace_id": trace_id,
            "timeline": all_events,
            "summary": {
                "task_states_count": len(task_states),
                "submission_states_count": len(submission_states),
                "execution_statuses_count": len(execution_statuses),
                "total_events": len(all_events)
            }
        }