"""
Combined Excel upload utility for students and parents together.
"""

import asyncio
import pandas as pd
from typing import List, Dict, Tuple, Optional
from io import BytesIO
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.models import User, UserRole, School, StudentParent
from app.utils.password_generator import generate_unique_password
from app.auth import get_password_hash
from app.email_service import send_login_credentials_email
from app.utils.excel_upload import ExcelUploadResult, validate_email
from app.config import settings
from app.services.gurukul_sync import sync_student_to_gurukul


async def upload_students_parents_combined_excel(
    file: UploadFile,
    school_id: int,
    db: Session
) -> ExcelUploadResult:
    """
    Upload students and parents from a combined Excel file.
    Expected columns:
    - Student Name
    - Student Email
    - Grade / Class
    - Parent Name
    - Parent Email
    """
    result = ExcelUploadResult()
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # Normalize column names (case-insensitive, strip whitespace)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Required columns
        required_columns = ['student_name', 'student_email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Process each row
        for row_number, row in df.iterrows():
            row_number += 2  # Excel rows start at 2 (1 is header)
            
            try:
                # Get student data
                student_name = str(row.get('student_name', '')).strip()
                student_email = str(row.get('student_email', '')).strip().lower()
                grade = str(row.get('grade', '') or row.get('class', '')).strip()
                
                # Get parent data (optional)
                parent_name = str(row.get('parent_name', '')).strip() if pd.notna(row.get('parent_name')) else None
                parent_email = str(row.get('parent_email', '')).strip().lower() if pd.notna(row.get('parent_email')) else None
                
                # Validate student email
                is_valid, error_msg = await validate_email(student_email, db)
                if not is_valid:
                    result.add_failure(row_number, student_email, f"Student: {error_msg}", row.to_dict())
                    continue
                
                # Check if student already exists (only active users)
                existing_student = db.query(User).filter(
                    User.email == student_email,
                    User.is_active == True
                ).first()
                
                if existing_student:
                    student = existing_student
                    if student.school_id != school_id or student.role != UserRole.STUDENT:
                        result.add_failure(row_number, student_email, "Student exists but belongs to different school or has different role", row.to_dict())
                        continue
                else:
                    # Create new student
                    password = generate_unique_password(db, student_email, student_name, UserRole.STUDENT.value, school_id)
                    hashed_password = get_password_hash(password)
                    
                    student = User(
                        name=student_name,
                        email=student_email,
                        password=hashed_password,
                        role=UserRole.STUDENT,
                        school_id=school_id,
                        is_active=True
                    )
                    db.add(student)
                    db.flush()
                    
                    # Send login credentials email
                    try:
                        await send_login_credentials_email(db, student, password, UserRole.STUDENT.value)
                    except Exception as e:
                        print(f"Warning: Failed to send email to {student_email}: {str(e)}")
                    
                    # Sync student to Gurukul (fire-and-forget)
                    if settings.GURUKUL_API_BASE_URL:
                        asyncio.create_task(
                            asyncio.to_thread(
                                sync_student_to_gurukul,
                                settings.GURUKUL_API_BASE_URL,
                                student_email,
                                password,
                                student_name,
                            )
                        )
                
                # Process parent if provided
                if parent_email and parent_name:
                    # Validate parent email
                    is_valid, error_msg = await validate_email(parent_email, db)
                    if not is_valid:
                        result.add_failure(row_number, parent_email, f"Parent: {error_msg}", row.to_dict())
                        continue
                    
                    # Check if parent already exists (only active users)
                    existing_parent = db.query(User).filter(
                        User.email == parent_email,
                        User.is_active == True
                    ).first()
                    
                    if existing_parent:
                        parent = existing_parent
                        if parent.school_id != school_id or parent.role != UserRole.PARENT:
                            result.add_failure(row_number, parent_email, "Parent exists but belongs to different school or has different role", row.to_dict())
                            continue
                    else:
                        # Create new parent
                        password = generate_unique_password(db, parent_email, parent_name, UserRole.PARENT.value, school_id)
                        hashed_password = get_password_hash(password)
                        
                        parent = User(
                            name=parent_name,
                            email=parent_email,
                            password=hashed_password,
                            role=UserRole.PARENT,
                            school_id=school_id,
                            is_active=True
                        )
                        db.add(parent)
                        db.flush()
                        
                        # Send login credentials email
                        try:
                            await send_login_credentials_email(db, parent, password, UserRole.PARENT.value)
                        except Exception as e:
                            print(f"Warning: Failed to send email to {parent_email}: {str(e)}")
                    
                    # Create parent-student link if it doesn't exist
                    existing_link = db.query(StudentParent).filter(
                        StudentParent.student_id == student.id,
                        StudentParent.parent_id == parent.id
                    ).first()
                    
                    if not existing_link:
                        link = StudentParent(
                            student_id=student.id,
                            parent_id=parent.id,
                            relationship_type="Parent"
                        )
                        db.add(link)
                
                result.add_success(student)
                
            except Exception as e:
                email = row.get('student_email', 'N/A') if 'student_email' in row else 'N/A'
                result.add_failure(row_number, email, str(e), row.to_dict())
        
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
