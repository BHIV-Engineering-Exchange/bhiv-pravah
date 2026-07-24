from pydantic import BaseModel
from typing import Dict, Any

class InboundRequest(BaseModel):
    token: str
    nonce: str
    payload: Dict[str, Any]

class DecisionResponse(BaseModel):
    decision: str
    reason: str
    version: str
