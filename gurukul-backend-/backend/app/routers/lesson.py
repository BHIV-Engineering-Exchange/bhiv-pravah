from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.all_models import User, Summary, Lesson
from pydantic import BaseModel
import uuid

router = APIRouter()

class LessonContextResponse(BaseModel):
    lesson_id: str
    title: str
    subject: str
    topic: str
    content: str
    created_at: str
    success: bool

@router.get("/{lesson_id}/context", response_model=LessonContextResponse)
async def get_lesson_context(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the context for a specific lesson.
    This endpoint is designed to provide lesson context to the frontend
    so it can track which lesson the user is currently working on.
    """
    try:
        # First try to get actual lesson data
        lesson = db.query(Lesson).filter(
            Lesson.id == lesson_id,
            Lesson.user_id == current_user.id
        ).first()
        
        if lesson:
            return LessonContextResponse(
                lesson_id=lesson.id,
                title=lesson.title,
                subject=lesson.subject,
                topic=lesson.topic,
                content=lesson.description[:200] + "..." if lesson.description and len(lesson.description) > 200 else (lesson.description or ""),
                created_at=lesson.created_at.isoformat() if lesson.created_at else "",
                success=True
            )
        
        # If no specific lesson found, return a default context
        return LessonContextResponse(
            lesson_id=lesson_id,
            title="General Learning Session",
            subject="General",
            topic="Learning",
            content="Current learning session context",
            created_at="",
            success=True
        )
    except Exception as e:
        print(f"[Lesson Context Error] {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving lesson context")

# Include a simple lesson creation endpoint for testing purposes
class LessonCreateRequest(BaseModel):
    title: str
    subject: str
    topic: str
    content: str

@router.post("/", response_model=LessonContextResponse)
async def create_lesson(
    lesson_data: LessonCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new lesson/summary for tracking purposes.
    This allows the frontend to have a proper lesson_id to work with.
    """
    try:
        # Create a lesson record to serve as our lesson context
        lesson_id = str(uuid.uuid4())
        
        new_lesson = Lesson(
            id=lesson_id,
            user_id=current_user.id,
            title=lesson_data.title,
            subject=lesson_data.subject,
            topic=lesson_data.topic,
            description=lesson_data.content,
            content=lesson_data.content
        )
        
        db.add(new_lesson)
        db.commit()
        db.refresh(new_lesson)
        
        return LessonContextResponse(
            lesson_id=new_lesson.id,
            title=new_lesson.title,
            subject=new_lesson.subject,
            topic=new_lesson.topic,
            content=new_lesson.description[:200] + "..." if new_lesson.description and len(new_lesson.description) > 200 else (new_lesson.description or ""),
            created_at=new_lesson.created_at.isoformat() if new_lesson.created_at else "",
            success=True
        )
    except Exception as e:
        print(f"[Create Lesson Error] {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creating lesson")