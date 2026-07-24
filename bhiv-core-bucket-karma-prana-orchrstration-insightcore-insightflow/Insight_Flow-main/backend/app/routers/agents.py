from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict
from pydantic import BaseModel
from app.schemas.agent import AgentCreate, AgentResponse
from app.services.agent_service import AgentService
from app.core.security import get_current_user
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
agent_service = AgentService()


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    status_filter: str = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    List all agents with optional status filter
    
    Args:
        status_filter: Optional status filter (active, inactive, maintenance)
        current_user: Current authenticated user
        
    Returns:
        List of agents
    """
    try:
        db = get_db()
        query = db.table("agents").select("*")
        if status_filter:
            query = query.eq("status", status_filter)
        result = query.execute()
        return result.data
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving agents"
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get specific agent by ID
    
    Args:
        agent_id: Agent ID
        current_user: Current authenticated user
        
    Returns:
        Agent details
    """
    try:
        agent = await agent_service.get_agent_by_id(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting agent: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving agent"
        )


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new agent
    
    Args:
        agent: Agent creation data
        current_user: Current authenticated user
        
    Returns:
        Created agent
    """
    try:
        # Check if user has admin role
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create agents"
            )
        
        agent_data = agent.model_dump()
        created_agent = await agent_service.create_agent(agent_data)
        
        return created_agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating agent"
        )


class StatusUpdate(BaseModel):
    status: str

@router.patch("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: str,
    status_update: StatusUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update agent status
    
    Args:
        agent_id: Agent ID
        status_update: Status update data
        current_user: Current authenticated user
        
    Returns:
        Updated agent
    """
    try:
        # Check if user has admin role
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update agent status"
            )
        
        db = get_db()
        result = db.table("agents").update({
            "status": status_update.status
        }).eq("id", agent_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating agent status"
        )