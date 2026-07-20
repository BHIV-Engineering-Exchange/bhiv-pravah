from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/school_management_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Email Configuration
    # Option 1: Brevo API (works on Render - recommended for production)
    BREVO_API_KEY: Optional[str] = None  # If set, uses Brevo HTTP API instead of SMTP
    
    # Option 2: SendGrid API (works on Render - alternative)
    SENDGRID_API_KEY: Optional[str] = None  # If set, uses SendGrid API instead of SMTP
    
    # Option 2: SMTP (for local development or services that allow SMTP)
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@schoolmanagement.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "School Management System"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    
    # Gurukul API (optional): when set, students created in EMS are also registered in Gurukul
    GURUKUL_API_BASE_URL: Optional[str] = None  # e.g. http://localhost:3000
    GURUKUL_API_KEY: Optional[str] = None  # Optional; if set, sent as X-API-Key when calling Gurukul (e.g. provision-tenant)

    # Frontend URL (for password setup links)
    # This should point to the EMS frontend, not the Gurukul app.
    # Default to the EMS Vite dev server port (3001).
    FRONTEND_URL: str = "http://localhost:3001"
    
    # Password token expiration (minutes)
    PASSWORD_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = [".env", "app/.env"]  # Check both root and app directory
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
