"""
Grade Helper Utility
Fetches student grade from EMS or Profile cache
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.all_models import User, Profile
from app.services.ems_client import ems_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def get_student_grade(user: User, db: Session) -> Optional[str]:
    """
    Get student's grade from Profile cache or EMS database.
    
    Priority:
    1. Check Profile.data JSON cache
    2. Fetch from EMS API if available
    3. Cache result in Profile.data
    4. Return None if unavailable
    
    Args:
        user: User model instance
        db: Database session
        
    Returns:
        Grade string (e.g., "3", "9", "12") or None
    """
    # Only proceed if user is a student
    if user.role.upper() != "STUDENT":
        return None
    
    # Step 1: Check Profile.data cache
    try:
        if user.profile and user.profile.data:
            cached_grade = user.profile.data.get("grade")
            if cached_grade:
                logger.debug(f"Using cached grade for user {user.email}: {cached_grade}")
                return str(cached_grade)
    except Exception as e:
        logger.warning(f"Error reading profile cache: {e}")
    
    # Step 2: Try fetching from EMS (if admin credentials available)
    grade = None
    try:
        # Check if EMS is configured with admin credentials
        if settings.EMS_API_BASE_URL and settings.EMS_ADMIN_EMAIL and settings.EMS_ADMIN_PASSWORD:
            # Authenticate as admin to fetch student data
            admin_token_response = await ems_client.login(
                settings.EMS_ADMIN_EMAIL,
                settings.EMS_ADMIN_PASSWORD
            )
            admin_token = admin_token_response.get("access_token")
            
            if admin_token:
                # Fetch students list filtered by email to get this student's grade
                # Note: This requires EMS admin endpoint to support email search
                # For now, we'll skip this and rely on Profile cache
                # Grade will be synced when student uses EMS features
                logger.debug(f"EMS admin token obtained, but skipping direct fetch for {user.email}")
            else:
                logger.debug("Failed to get EMS admin token for grade fetch")
        else:
            logger.debug("EMS admin credentials not configured, skipping grade fetch")
        
    except Exception as e:
        logger.debug(f"Error fetching grade from EMS (non-critical): {e}")
        # Don't fail - just return None
    
    # Step 3: Cache grade in Profile.data if we got one
    if grade:
        try:
            # Get or create profile
            if not user.profile:
                profile = Profile(user_id=user.id, data={})
                db.add(profile)
                db.flush()
            else:
                profile = user.profile
            
            # Update cache
            if not profile.data:
                profile.data = {}
            profile.data["grade"] = grade
            db.commit()
            logger.info(f"Cached grade {grade} for user {user.email}")
        except Exception as e:
            logger.warning(f"Failed to cache grade: {e}")
            db.rollback()
    
    return grade


def get_grade_level_description(grade: Optional[str]) -> str:
    """
    Convert grade number to descriptive level for prompts.
    
    Args:
        grade: Grade string (e.g., "3", "9", "12") or None
        
    Returns:
        Descriptive string for prompt
    """
    if not grade:
        return "intermediate (Grades 6-8)"
    
    try:
        grade_num = int(grade)
        
        if grade_num <= 5:
            return f"elementary (Grade {grade})"
        elif grade_num <= 8:
            return f"middle school (Grade {grade})"
        elif grade_num <= 10:
            return f"high school (Grade {grade})"
        else:
            return f"advanced high school (Grade {grade})"
    except (ValueError, TypeError):
        return "intermediate (Grades 6-8)"


def get_grade_complexity_guidelines(grade: Optional[str]) -> str:
    """
    Get complexity guidelines for a specific grade level.
    
    Args:
        grade: Grade string or None
        
    Returns:
        Guidelines string for LLM prompts
    """
    if not grade:
        return """- Use intermediate vocabulary and concepts
- Explain ideas clearly with examples
- Balance simplicity with educational value"""
    
    try:
        grade_num = int(grade)
        
        if grade_num <= 5:
            return """- Use simple, age-appropriate vocabulary
- Focus on concrete examples and visual concepts
- Avoid abstract or complex terminology
- Break down concepts into small, digestible parts
- Use analogies and real-world examples children can relate to"""
        elif grade_num <= 8:
            return """- Use intermediate vocabulary with explanations for technical terms
- Introduce abstract concepts gradually
- Provide concrete examples alongside abstract ideas
- Use clear, structured explanations
- Include practical applications"""
        elif grade_num <= 10:
            return """- Use advanced vocabulary with context
- Introduce complex concepts with proper scaffolding
- Include technical terminology with definitions
- Focus on deeper understanding and analysis
- Connect concepts to real-world applications"""
        else:  # 11-12
            return """- Use advanced, college-prep level vocabulary
- Introduce complex, abstract concepts confidently
- Include specialized terminology appropriate for the subject
- Focus on critical thinking and analysis
- Prepare for advanced academic work"""
    except (ValueError, TypeError):
        return """- Use intermediate vocabulary and concepts
- Explain ideas clearly with examples
- Balance simplicity with educational value"""

