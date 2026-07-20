"""
BHIV Bucket Integration
======================
Handles artifact storage and retrieval for the full pipeline.

STRICT RULES:
- Bucket does NOT reconstruct
- Bucket does NOT interpret  
- Append-only storage
- artifact_id and trace_id based retrieval
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# All first-class artifact types in the live pipeline (A1 → A4 including authority stages)
ARTIFACT_TYPES = [
    "telemetry",
    "instruction",
    "blueprint",
    "contract",
    "authority",
    "gate",
    "execution",
    "result",
    "alert",
]


class BHIVBucket:
    """Artifact storage system for BHIV pipeline"""
    
    def __init__(self, base_path: str = "bhiv_bucket"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Create subdirectories for all artifact types
        for artifact_type in ARTIFACT_TYPES:
            (self.base_path / f"{artifact_type}s").mkdir(exist_ok=True)
        (self.base_path / "traces").mkdir(exist_ok=True)
    
    def store_artifact(self, artifact_id: str, artifact_type: str, data: Dict[str, Any], 
                      trace_id: str) -> Dict[str, Any]:
        """Store artifact with metadata (append-only)"""
        
        artifact_record = {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "metadata": {
                "size_bytes": len(json.dumps(data)),
                "schema_version": "1.0.0"
            }
        }
        
        # Store in type-specific directory
        type_dir = self.base_path / f"{artifact_type}s"
        artifact_file = type_dir / f"{artifact_id}.json"
        
        with open(artifact_file, 'w', encoding='utf-8') as f:
            json.dump(artifact_record, f, indent=2, ensure_ascii=False)
        
        # Update trace index
        self._update_trace_index(trace_id, artifact_id, artifact_type)
        
        return {
            "status": "stored",
            "artifact_id": artifact_id,
            "path": str(artifact_file),
            "timestamp": artifact_record["timestamp"]
        }
    
    def retrieve_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve artifact by ID (no transformation)"""
        
        # Search across all artifact type directories
        for artifact_type in ARTIFACT_TYPES:
            type_dir = self.base_path / f"{artifact_type}s"
            artifact_file = type_dir / f"{artifact_id}.json"
            
            if artifact_file.exists():
                with open(artifact_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        return None
    
    def retrieve_by_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Retrieve all artifacts for a trace ID"""
        
        trace_file = self.base_path / "traces" / f"{trace_id}.json"
        if not trace_file.exists():
            return []
        
        with open(trace_file, 'r', encoding='utf-8') as f:
            trace_data = json.load(f)
        
        artifacts = []
        for artifact_id in trace_data.get("artifact_ids", []):
            artifact = self.retrieve_artifact(artifact_id)
            if artifact:
                artifacts.append(artifact)
        
        return artifacts
    
    def _update_trace_index(self, trace_id: str, artifact_id: str, artifact_type: str):
        """Update trace index with new artifact"""
        
        trace_file = self.base_path / "traces" / f"{trace_id}.json"
        
        if trace_file.exists():
            with open(trace_file, 'r', encoding='utf-8') as f:
                trace_data = json.load(f)
        else:
            trace_data = {
                "trace_id": trace_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "artifact_ids": [],
                "artifact_types": {}
            }
        
        trace_data["artifact_ids"].append(artifact_id)
        trace_data["artifact_types"][artifact_type] = artifact_id
        trace_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        with open(trace_file, 'w', encoding='utf-8') as f:
            json.dump(trace_data, f, indent=2, ensure_ascii=False)
    
    def list_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent traces"""
        
        traces_dir = self.base_path / "traces"
        trace_files = sorted(traces_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        
        traces = []
        for trace_file in trace_files[:limit]:
            with open(trace_file, 'r', encoding='utf-8') as f:
                trace_data = json.load(f)
                traces.append({
                    "trace_id": trace_data["trace_id"],
                    "created_at": trace_data["created_at"],
                    "artifact_count": len(trace_data["artifact_ids"])
                })
        
        return traces
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bucket statistics"""
        
        stats = {
            "total_artifacts": 0,
            "by_type": {},
            "total_traces": 0,
            "storage_size_mb": 0
        }
        
        for artifact_type in ARTIFACT_TYPES:
            type_dir = self.base_path / f"{artifact_type}s"
            count = len(list(type_dir.glob("*.json")))
            stats["by_type"][artifact_type] = count
            stats["total_artifacts"] += count
        
        traces_dir = self.base_path / "traces"
        stats["total_traces"] = len(list(traces_dir.glob("*.json")))
        
        # Calculate storage size
        total_size = sum(f.stat().st_size for f in self.base_path.rglob("*.json"))
        stats["storage_size_mb"] = round(total_size / (1024 * 1024), 2)
        
        return stats

    def get_insightflow_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Read recent InsightFlow events from the shared telemetry log."""
        events_path = self.base_path / "insightflow_events.jsonl"
        if not events_path.exists():
            return []
        lines = events_path.read_text(encoding="utf-8").strip().splitlines()
        events = []
        for line in lines[-limit:]:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Minimal observability snapshot: bucket stats + recent traces + telemetry counts."""
        stats = self.get_stats()
        traces = self.list_traces(limit=10)
        events = self.get_insightflow_events(limit=500)
        by_component: Dict[str, int] = {}
        for event in events:
            component = event.get("component", "unknown")
            by_component[component] = by_component.get(component, 0) + 1
        return {
            "bucket": stats,
            "recent_traces": traces,
            "insightflow_event_count": len(events),
            "insightflow_by_component": by_component,
        }


# Bucket API
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional

bucket_app = FastAPI(
    title="BHIV Bucket API",
    description="Artifact storage and retrieval for BHIV pipeline",
    version="1.0.0"
)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    expected_api_key = os.getenv("AUTH_API_KEY", "")
    auth_enabled = os.getenv("AUTH_ENABLED", "true").lower() in ("1", "true", "yes")
    if auth_enabled and expected_api_key:
        if not api_key or api_key != expected_api_key:
            raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

bucket = BHIVBucket()

class StoreArtifactRequest(BaseModel):
    artifact_id: str
    artifact_type: str
    data: Dict[str, Any]
    trace_id: str

@bucket_app.post("/bucket/store", dependencies=[Depends(verify_api_key)])
async def store_artifact(request: StoreArtifactRequest):
    """Store artifact in bucket"""
    result = bucket.store_artifact(
        request.artifact_id,
        request.artifact_type, 
        request.data,
        request.trace_id
    )
    return result

@bucket_app.get("/bucket/artifact/{artifact_id}", dependencies=[Depends(verify_api_key)])
async def get_artifact(artifact_id: str):
    """Retrieve artifact by ID"""
    artifact = bucket.retrieve_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact

@bucket_app.get("/bucket/trace/{trace_id}", dependencies=[Depends(verify_api_key)])
async def get_trace_artifacts(trace_id: str):
    """Retrieve all artifacts for a trace"""
    artifacts = bucket.retrieve_by_trace(trace_id)
    if not artifacts:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {"trace_id": trace_id, "artifacts": artifacts}

@bucket_app.get("/bucket/traces", dependencies=[Depends(verify_api_key)])
async def list_traces(limit: int = 100):
    """List recent traces"""
    return {"traces": bucket.list_traces(limit)}

@bucket_app.get("/bucket/stats")
async def get_bucket_stats():
    """Get bucket statistics"""
    return bucket.get_stats()

@bucket_app.get("/bucket/insightflow")
async def get_insightflow_events(limit: int = 100):
    """Query recent InsightFlow telemetry events"""
    return {"events": bucket.get_insightflow_events(limit)}

@bucket_app.get("/bucket/dashboard")
async def get_dashboard():
    """Minimal observability dashboard data"""
    return bucket.get_dashboard_summary()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(bucket_app, host="0.0.0.0", port=8005)