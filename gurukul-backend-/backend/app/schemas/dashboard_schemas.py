from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Alert Schemas ---
class AlertCreate(BaseModel):
    type: str  # e.g. "PACING", "COMPREHENSION", "ATTENDANCE"
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    owner_id: Optional[str] = None

class AlertAssign(BaseModel):
    owner_id: str

class AlertStatusUpdate(BaseModel):
    status: str  # OPEN, RESOLVED, CLOSED

class AlertResponse(BaseModel):
    id: str
    type: str
    priority: str
    owner_id: Optional[str]
    status: str
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Action Schemas ---
class ActionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    owner_id: Optional[str] = None

class ActionAssign(BaseModel):
    owner_id: str

class ActionStatusUpdate(BaseModel):
    status: str  # Created, Assigned, In Progress, Completed, Closed, Cancelled

class ActionResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    owner_id: Optional[str]
    status: str
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Audit Log Schema ---
class AuditLogResponse(BaseModel):
    id: str
    created_by: str
    updated_by: Optional[str]
    timestamp: datetime
    entity: str
    entity_id: str
    operation: str
    status: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- Dashboard Aggregation Schema ---
class DashboardResponse(BaseModel):
    role: str
    kpis: Dict[str, Any]
    open_alerts: List[AlertResponse]
    pending_actions: List[ActionResponse]
    recent_activity: List[Dict[str, Any]]
    status_summary: Dict[str, Any]
