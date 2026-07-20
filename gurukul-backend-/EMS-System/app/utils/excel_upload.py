"""
Excel upload utility for bulk user creation.
Supports uploading Teachers, Students, and Parents via Excel files.
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from io import BytesIO
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.models import User, UserRole, School, StudentParent
from app.utils.password_generator import generate_unique_password
from app.auth import get_password_hash
from app.email_service import send_login_credentials_email
from app.config import settings
from app.services.gurukul_sync import sync_student_to_gurukul
import asyncio


class ExcelUploadResult:
    """Result of Excel upload operation."""
    def __init__(self):
        self.success_count = 0
        self.failed_rows: List[Dict] = []
        self.created_users: List[User] = []
    
    def add_success(self, user: User):
        self.success_count += 1
        self.created_users.append(user)
    
    def add_failure(self, row_number: int, email: str, reason: str, data: Dict):
        self.failed_rows.append({
            "row": row_number,
            "email": email,
            "reason": reason,
            "data": data
        })


async def validate_email(email: str, db: Session) -> Tuple[bool, Optional[str]]:
    """
    Validate email format and check for duplicates.
    
    Returns:
        (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    # Basic email format validation
    if "@" not in email or "." not in email.split("@")[1]:
        return False, "Invalid email format"
    
    # Check for duplicate email (only for active users)
    existing_user = db.query(User).filter(
        User.email == email.lower().strip(),
        User.is_active == True
    ).first()
    if existing_user:
        return False, f"Email already exists: {email}"
    
    return True, None


async def upload_teachers_excel(
    file: UploadFile,
    school_id: int,
    db: Session
) -> ExcelUploadResult:
    """
    Upload teachers from Excel file.
    
    Expected columns:
    - name (required)
    - email (required, must be unique)
    - subject (optional)
    
    Returns:
        ExcelUploadResult with success/failure details
    """
    result = ExcelUploadResult()
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # Validate required columns
        required_columns = ["name", "email"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Verify school exists
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"School with id {school_id} not found"
            )
        
        # Process each row
        for index, row in df.iterrows():
            row_number = index + 2  # Excel rows start at 2 (1 is header)
            
            try:
                name = str(row.get("name", "")).strip()
                email = str(row.get("email", "")).strip().lower()
                subject = str(row.get("subject", "")).strip() if pd.notna(row.get("subject")) else None
                
                # Validate name
                if not name:
                    result.add_failure(row_number, email or "N/A", "Name is required", row.to_dict())
                    continue
                
                # Validate email
                is_valid, error_msg = await validate_email(email, db)
                if not is_valid:
                    result.add_failure(row_number, email, error_msg or "Invalid email", row.to_dict())
                    continue
                
                # Generate unique password
                password = generate_unique_password(db, email, name, UserRole.TEACHER.value, school_id)
                hashed_password = get_password_hash(password)
                
                # Create teacher user
                teacher = User(
                    name=name,
                    email=email,
                    password=hashed_password,
                    role=UserRole.TEACHER,
                    school_id=school_id,
                    is_active=True,
                    subject=subject if subject else None
                )
                
                db.add(teacher)
                db.flush()  # Get the ID
                
                # Send login credentials email
                try:
                    await send_login_credentials_email(db, teacher, password, UserRole.TEACHER.value)
                except Exception as e:
                    # Log error but don't fail the creation
                    print(f"Warning: Failed to send email to {email}: {str(e)}")
                
                result.add_success(teacher)
                
            except Exception as e:
                result.add_failure(row_number, email if 'email' in locals() else "N/A", str(e), row.to_dict())
        
        # Commit all successful creations
        db.commit()
        
        return result
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel file is empty"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing Excel file: {str(e)}"
        )


async def upload_students_excel(
    file: UploadFile,
    school_id: int,
    db: Session
) -> ExcelUploadResult:
    """
    Upload students from Excel file.
    
    Expected columns:
    - name (required)
    - email (required, must be unique)
    - grade (optional)
    - parent_email (optional, for linking to parent)
    
    Returns:
        ExcelUploadResult with success/failure details
    """
    result = ExcelUploadResult()
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # Validate required columns
        required_columns = ["name", "email"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Verify school exists
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"School with id {school_id} not found"
            )
        
        # Process each row
        for index, row in df.iterrows():
            row_number = index + 2  # Excel rows start at 2
            
            try:
                name = str(row.get("name", "")).strip()
                email = str(row.get("email", "")).strip().lower()
                grade = str(row.get("grade", "")).strip() if pd.notna(row.get("grade")) else None
                parent_email = str(row.get("parent_email", "")).strip().lower() if pd.notna(row.get("parent_email")) else None
                
                # Validate name
                if not name:
                    result.add_failure(row_number, email or "N/A", "Name is required", row.to_dict())
                    continue
                
                # Validate email
                is_valid, error_msg = await validate_email(email, db)
                if not is_valid:
                    result.add_failure(row_number, email, error_msg or "Invalid email", row.to_dict())
                    continue
                
                # Generate unique password
                password = generate_unique_password(db, email, name, UserRole.STUDENT.value, school_id)
                hashed_password = get_password_hash(password)
                
                # Create student user
                student = User(
                    name=name,
                    email=email,
                    password=hashed_password,
                    role=UserRole.STUDENT,
                    school_id=school_id,
                    is_active=True
                )
                
                db.add(student)
                db.flush()  # Get the ID
                
                # Link to parent if parent_email provided
                if parent_email:
                    parent = db.query(User).filter(
                        User.email == parent_email,
                        User.role == UserRole.PARENT,
                        User.school_id == school_id
                    ).first()
                    
                    if parent:
                        # Create StudentParent relationship
                        from app.models import StudentParent
                        student_parent = StudentParent(
                            student_id=student.id,
                            parent_id=parent.id,
                            relationship_type="Parent"
                        )
                        db.add(student_parent)
                
                # Send login credentials email
                try:
                    await send_login_credentials_email(db, student, password, UserRole.STUDENT.value)
                except Exception as e:
                    print(f"Warning: Failed to send email to {email}: {str(e)}")
                
                # Sync student to Gurukul (fire-and-forget)
                if settings.GURUKUL_API_BASE_URL:
                    asyncio.create_task(
                        asyncio.to_thread(
                            sync_student_to_gurukul,
                            settings.GURUKUL_API_BASE_URL,
                            email,
                            password,
                            name,
                        )
                    )
                
                result.add_success(student)
                
            except Exception as e:
                result.add_failure(row_number, email if 'email' in locals() else "N/A", str(e), row.to_dict())
        
        # Commit all successful creations
        db.commit()
        
        return result
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel file is empty"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing Excel file: {str(e)}"
        )


async def upload_parents_excel(
    file: UploadFile,
    school_id: int,
    db: Session
) -> ExcelUploadResult:
    """
    Upload parents from Excel file.
    
    Expected columns:
    - name (required)
    - email (required, must be unique)
    - student_email (optional, for linking to student)
    
    Returns:
        ExcelUploadResult with success/failure details
    """
    result = ExcelUploadResult()
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # Validate required columns
        required_columns = ["name", "email"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Verify school exists
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"School with id {school_id} not found"
            )
        
        # Process each row
        for index, row in df.iterrows():
            row_number = index + 2  # Excel rows start at 2
            
            try:
                name = str(row.get("name", "")).strip()
                email = str(row.get("email", "")).strip().lower()
                student_email = str(row.get("student_email", "")).strip().lower() if pd.notna(row.get("student_email")) else None
                
                # Validate name
                if not name:
                    result.add_failure(row_number, email or "N/A", "Name is required", row.to_dict())
                    continue
                
                # Validate email
                is_valid, error_msg = await validate_email(email, db)
                if not is_valid:
                    result.add_failure(row_number, email, error_msg or "Invalid email", row.to_dict())
                    continue
                
                # Generate unique password
                password = generate_unique_password(db, email, name, UserRole.PARENT.value, school_id)
                hashed_password = get_password_hash(password)
                
                # Create parent user
                parent = User(
                    name=name,
                    email=email,
                    password=hashed_password,
                    role=UserRole.PARENT,
                    school_id=school_id,
                    is_active=True
                )
                
                db.add(parent)
                db.flush()  # Get the ID
                
                # Link to student if student_email provided
                if student_email:
                    student = db.query(User).filter(
                        User.email == student_email,
                        User.role == UserRole.STUDENT,
                        User.school_id == school_id
                    ).first()
                    
                    if student:
                        # Create StudentParent relationship
                        from app.models import StudentParent
                        student_parent = StudentParent(
                            student_id=student.id,
                            parent_id=parent.id,
                            relationship_type="Parent"
                        )
                        db.add(student_parent)
                
                # Send login credentials email
                try:
                    await send_login_credentials_email(db, parent, password, UserRole.PARENT.value)
                except Exception as e:
                    print(f"Warning: Failed to send email to {email}: {str(e)}")
                
                result.add_success(parent)
                
            except Exception as e:
                result.add_failure(row_number, email if 'email' in locals() else "N/A", str(e), row.to_dict())
        
        # Commit all successful creations
        db.commit()
        
        return result
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel file is empty"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing Excel file: {str(e)}"
        )
