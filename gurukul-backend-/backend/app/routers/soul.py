from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.all_models import User, Reflection as DBReflection, LearningTrack, Milestone, StudentProgress
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# --- Schemas (Inline for now or move to schemas/soul.py later) ---

class MilestoneResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    order_index: int
    status: str # NOT_STARTED, IN_PROGRESS, COMPLETED
    
    class Config:
        from_attributes = True

class TrackResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    milestones: List[MilestoneResponse]
    
    class Config:
        from_attributes = True

class ReflectionCreate(BaseModel):
    content: str
    mood_score: int
    milestone_id: Optional[str] = None # Link reflection to a milestone

class ReflectionResponse(BaseModel):
    id: str
    content: str
    mood_score: int
    created_at: str

# --- Endpoints ---

@router.get("/journey", response_model=List[TrackResponse])
async def get_my_learning_journey(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the Student's Learning Journey.
    Shows tracks assigned (globally or via tenant) and progress on milestones.
    """
    # 1. Fetch Tracks (For now, fetch ALL global tracks or tenant specific)
    # Ideally tracks are assigned to Cohorts. For prototype, we show all visible tracks.
    tracks = db.query(LearningTrack).filter(
        (LearningTrack.tenant_id == current_user.tenant_id) | (LearningTrack.tenant_id == None)
    ).all()

    response = []
    for track in tracks:
        # Get Milestones sorted
        milestones = db.query(Milestone).filter(Milestone.track_id == track.id).order_by(Milestone.order_index).all()
        
        milestone_responses = []
        for m in milestones:
            # Check progress
            prog = db.query(StudentProgress).filter(
                StudentProgress.user_id == current_user.id,
                StudentProgress.milestone_id == m.id
            ).first()
            
            status = prog.status if prog else "NOT_STARTED"
            
            milestone_responses.append(MilestoneResponse(
                id=m.id,
                title=m.title,
                description=m.description,
                order_index=m.order_index,
                status=status
            ))
            
        response.append(TrackResponse(
            id=track.id,
            title=track.title,
            description=track.description,
            milestones=milestone_responses
        ))
        
    return response

@router.post("/reflections", response_model=ReflectionResponse)
async def create_reflection(
    reflection_in: ReflectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log a reflection and optionally complete a milestone"""
    
    # Create Reflection
    new_reflection = DBReflection(
        user_id=current_user.id,
        content=reflection_in.content,
        mood_score=reflection_in.mood_score
    )
    db.add(new_reflection)
    
    # If linked to a Milestone, update progress
    if reflection_in.milestone_id:
        # Check if milestone exists
        milestone = db.query(Milestone).filter(Milestone.id == reflection_in.milestone_id).first()
        if milestone:
            # Check if progress exists
            prog = db.query(StudentProgress).filter(
                StudentProgress.user_id == current_user.id,
                StudentProgress.milestone_id == reflection_in.milestone_id
            ).first()
            
            if not prog:
                prog = StudentProgress(
                    user_id=current_user.id,
                    milestone_id=milestone.id,
                    status="COMPLETED", # Auto-complete on reflection? Or IN_PROGRESS? Mandate says "Evidence".
                    completed_at=datetime.utcnow()
                )
                db.add(prog)
            else:
                prog.status = "COMPLETED"
                prog.completed_at = datetime.utcnow()
                # Update logic could be more complex later
            
            # Link reflection to progress? 
            # Our model has `reflection_notes` in StudentProgress, maybe copy content?
            prog.reflection_notes = reflection_in.content
            
    db.commit()
    db.refresh(new_reflection)
    
    return ReflectionResponse(
        id=new_reflection.id,
        content=new_reflection.content,
        mood_score=new_reflection.mood_score or 0,
        created_at=str(new_reflection.created_at)
    )

