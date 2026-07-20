from pydantic import BaseModel, EmailStr
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "STUDENT"  # STUDENT, TEACHER, PARENT, ADMIN

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    assessment_completed: bool
    
    class Config:
        from_attributes = True

class UpdateProfile(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None  # For future use if you add bio to User model

