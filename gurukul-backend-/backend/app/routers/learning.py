
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.summary import (
    SubjectExplorerRequest, SubjectExplorerResponse, SaveSummaryRequest
)
from app.models.all_models import Summary as DBSummary, User, SubjectData
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.services.ems_sync import ems_sync
from sqlalchemy.orm import Session
from app.services.llm import call_groq_api, call_ollama_api, create_teaching_prompt, generate_text
from app.services.youtube import get_youtube_recommendations
from app.services.knowledge_base_helper import get_knowledge_base_context, enhance_prompt_with_context
from app.services.prana_runtime import prana_runtime
from app.utils.grade_helper import get_student_grade, get_grade_complexity_guidelines, get_grade_level_description
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/explore", response_model=SubjectExplorerResponse)
async def subject_explorer(
    request: SubjectExplorerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Explore a subject/topic to get comprehensive notes and resources.
    Uses Knowledge Base + Groq with automatic fallback to Groq-only if KB fails.
    Saves to DB and syncs to EMS.
    """
    logger.info(f"Received /subject-explorer request: {request.subject} - {request.topic}")
    
    # Get student's grade for grade-level appropriate content
    grade = await get_student_grade(current_user, db)
    grade_description = get_grade_level_description(grade)
    complexity_guidelines = get_grade_complexity_guidelines(grade)
    
    if grade:
        logger.info(f"Generating content for Grade {grade} student ({current_user.email})")
    else:
        logger.info(f"Grade not available for {current_user.email}, using default intermediate level")
    
    # Step 1: Try to get relevant knowledge from knowledge base
    kb_result = get_knowledge_base_context(
        query=f"{request.subject} {request.topic}",
        top_k=5,
        filter_metadata={"subject": request.subject} if request.subject else None,
        use_knowledge_base=True
    )
    
    # Step 2: Generate Notes using LLM (with or without KB context)
    notes = ""
    kb_used = False
    groq_used = False
    
    try:
        # Create base teaching prompt with grade level
        base_prompt = create_teaching_prompt(request.subject, request.topic, grade=grade)
        
        if kb_result["knowledge_base_used"] and kb_result["context"]:
            # Best case: Use Knowledge Base context + Groq
            enhanced_prompt = enhance_prompt_with_context(
                base_prompt=base_prompt,
                query=f"Generate comprehensive notes about {request.topic}",
                context=kb_result["context"],
                include_context_instruction=True
            )
            
            # Use enhanced prompt with Groq
            system_prompt = "You are an expert teacher who explains concepts clearly and simply."
            notes = await generate_text(system_prompt, enhanced_prompt, temperature=0.7)
            kb_used = True
            groq_used = True
            logger.info(f"Generated notes using Knowledge Base + Groq: {len(kb_result['context'])} chars context")
        else:
            # Fallback: Use Groq only (KB failed or empty)
            if request.provider == "groq":
                notes = await call_groq_api(request.subject, request.topic)
            elif request.provider == "ollama":
                notes = await call_ollama_api(request.subject, request.topic)
            else:
                # Default to Groq
                notes = await call_groq_api(request.subject, request.topic)
            groq_used = True
            if kb_result["error"]:
                logger.warning(f"Knowledge Base unavailable, using Groq only: {kb_result['error']}")
            else:
                logger.info("No relevant knowledge base content, using Groq only")
    
    except Exception as e:
        logger.error(f"LLM Error: {str(e)}")
        # Fallback notes
        notes = f"# Error Generating Notes\n\nCould not generate notes for {request.topic}. Please try again."

    # 2. Get YouTube Recommendations
    youtube_videos = []
    youtube_videos_dict = []  # For database storage (JSON serializable)
    try:
        youtube_videos = await get_youtube_recommendations(request.subject, request.topic)
        # Convert Pydantic models to dictionaries for database storage
        youtube_videos_dict = [video.dict() if hasattr(video, 'dict') else video.model_dump() for video in youtube_videos]
    except Exception as e:
        logger.error(f"[API] YouTube Error: {str(e)}")
    
    # 3. Save to database
    subject_data = SubjectData(
        user_id=current_user.id,
        subject=request.subject,
        topic=request.topic,
        notes=notes,
        provider=request.provider,
        youtube_recommendations=youtube_videos_dict  # Use dict version for DB
    )
    db.add(subject_data)
    db.commit()
    db.refresh(subject_data)
    
    # Cryptographically chain the next-task recommendations (Phase 1)
    try:
        from app.services.deterministic_repo import deterministic_repo
        next_task_data = {
            "subject_data_id": subject_data.id,
            "youtube_recommendations": youtube_videos_dict
        }
        deterministic_repo.add_next_task_version(db, submission_id=str(subject_data.id), next_task_json=next_task_data)
        logger.info(f"Next-task recommendation version 1 saved and chained for topic {request.topic}")
    except Exception as e:
        logger.error(f"Failed to save chained next-task version for topic {request.topic}: {e}")
    
    # 4. Sync to EMS asynchronously (don't block response)
    try:
        # Get school_id from user if available
        school_id = getattr(current_user, 'school_id', None)

        ems_sync_result = await ems_sync.sync_subject_data(
            gurukul_id=subject_data.id,
            student_email=current_user.email,
            school_id=school_id,
            subject=request.subject,
            topic=request.topic,
            notes=notes,
            provider=request.provider,
            youtube_recommendations=youtube_videos_dict  # Use dict version for EMS sync
        )
        
        if ems_sync_result:
            subject_data.ems_sync_id = ems_sync_result.get("id")
            subject_data.synced_to_ems = True
            db.commit()
            logger.info(f"Synced subject data {subject_data.id} to EMS")
    except Exception as e:
        logger.error(f"Failed to sync subject data {subject_data.id} to EMS: {str(e)}")
        # Don't fail the request if sync fails
        
    # Log KB usage for debugging
    logger.info(f"Subject Explorer: KB={kb_used}, Groq={groq_used}, Fallback={not kb_used}")
    
    return SubjectExplorerResponse(
        subject=request.subject,
        topic=request.topic,
        notes=notes,
        provider=request.provider,
        youtube_recommendations=youtube_videos,
        success=True
    )

@router.post("/summaries/save")
async def save_learning_summary(
    summary_in: SaveSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save a summary for flashcard generation or review - syncs to EMS"""
    # Create DB entry
    new_summary = DBSummary(
        user_id=current_user.id,
        title=summary_in.title,
        content=summary_in.content,
        source=summary_in.source or "manual",
        source_type=summary_in.source_type or "text"
    )
    db.add(new_summary)
    db.commit()
    db.refresh(new_summary)

    try:
        prana_runtime.ingest_event(
            db,
            submission_id=new_summary.id,
            event_type="task_submit",
            timestamp=(new_summary.created_at.isoformat() if new_summary.created_at else datetime.now(timezone.utc).isoformat()),
            payload={
                "sequence": 1,
                "route": "/api/v1/learning/summaries/save",
                "user_id": current_user.id,
                "title": summary_in.title,
                "source": summary_in.source or "manual",
                "source_type": summary_in.source_type or "text",
                "content_length": len(summary_in.content),
            },
            source_system="gurukul",
        )
    except Exception as e:
        logger.error(f"Failed to emit PRANA task_submit event for summary {new_summary.id}: {e}")
    
    # Sync to EMS asynchronously (don't block response)
    try:
        # Get school_id from user if available
        school_id = getattr(current_user, 'school_id', None)

        ems_sync_result = await ems_sync.sync_summary(
            gurukul_id=new_summary.id,
            student_email=current_user.email,
            school_id=school_id,
            title=summary_in.title,
            content=summary_in.content,
            source=summary_in.source or "manual",
            source_type=summary_in.source_type or "text"
        )
        
        if ems_sync_result:
            # Store EMS sync ID in metadata if needed
            new_summary.metadata_ = new_summary.metadata_ or {}
            new_summary.metadata_["ems_sync_id"] = ems_sync_result.get("id")
            db.commit()
            logger.info(f"Synced summary {new_summary.id} to EMS")
    except Exception as e:
        logger.error(f"Failed to sync summary {new_summary.id} to EMS: {str(e)}")
        # Don't fail the request if sync fails
    
    return {"message": "Summary saved successfully", "id": new_summary.id}


@router.get("/summaries")
async def get_user_summaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all summaries for the current user"""
    summaries = db.query(DBSummary).filter(
        DBSummary.user_id == current_user.id
    ).order_by(DBSummary.created_at.desc()).all()
    
    return [{
        "id": s.id,
        "title": s.title,
        "content": s.content,
        "source": s.source,
        "source_type": s.source_type,
        "created_at": s.created_at.isoformat() if s.created_at else None
    } for s in summaries]


@router.get("/subject-data")
async def get_user_subject_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all subject explorer data for the current user"""
    subject_data = db.query(SubjectData).filter(
        SubjectData.user_id == current_user.id
    ).order_by(SubjectData.created_at.desc()).all()
    
    return [{
        "id": s.id,
        "subject": s.subject,
        "topic": s.topic,
        "notes": s.notes,
        "provider": s.provider,
        "youtube_recommendations": s.youtube_recommendations or [],
        "created_at": s.created_at.isoformat() if s.created_at else None
    } for s in subject_data]
