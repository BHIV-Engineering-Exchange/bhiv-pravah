
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_TITLE: str = "Gurukul Backend API"
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "3000"))  # Read PORT from environment (Render provides this)
    RELOAD: bool = False  # Disable reload in production
    
    # API Keys
    GROQ_API_KEY: Optional[str] = None
    GROQ_API_ENDPOINT: str = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"
    
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_PRIMARY: str = "llama2"
    LOCAL_LLAMA_API_URL: str = "http://localhost:8080/v1/chat/completions"
    
    YOUTUBE_API_KEY: Optional[str] = None
    YOUTUBE_API_BASE_URL: str = "https://www.googleapis.com/youtube/v3/search"
    
    # Vaani Sovereign TTS
    VAANI_API_URL: str = os.getenv("VAANI_API_URL", "http://localhost:8008")

    # TANTRA Integration
    PRAVAH_URL: Optional[str] = os.getenv("PRAVAH_URL", None)          # e.g. https://pravah.tantra.io/ingest
    BUCKET_URL: Optional[str] = os.getenv("BUCKET_URL", None)          # e.g. https://bucket.tantra.io/write
    TANTRA_API_KEY: Optional[str] = os.getenv("TANTRA_API_KEY", None)  # Shared secret for TANTRA auth
    TANTRA_DEBUG_LOG: bool = os.getenv("TANTRA_DEBUG_LOG", "false").lower() == "true"  # Write to runtime_events.json for debug

    # Database
    DATABASE_URL: Optional[str] = None # postgresql://user:password@host:port/db or sqlite:///./gurukul.db

    # Multi-tenant (DB-per-tenant)
    MULTI_TENANT_ENABLED: bool = False
    CENTRAL_DATABASE_URL: Optional[str] = None  # Tenant registry DB; if None and MULTI_TENANT_ENABLED, uses DATABASE_URL
    TENANT_BASE_DOMAIN: str = "gurukul.blackholeinfiverse.com"  # For subdomain resolution
    
    # EMS System Integration
    EMS_API_BASE_URL: str = "http://localhost:8000"
    EMS_API_KEY: Optional[str] = None  # Optional API key for EMS authentication
    
    # EMS Admin Credentials (for auto-creating student accounts)
    EMS_ADMIN_EMAIL: Optional[str] = None  # EMS admin email for student creation
    EMS_ADMIN_PASSWORD: Optional[str] = None  # EMS admin password for student creation
    EMS_DEFAULT_SCHOOL_ID: Optional[int] = None  # Default school ID if not using admin auth
    EMS_AUTO_CREATE_STUDENTS: bool = False  # Enable/disable auto-creation of EMS accounts (disabled by default to prevent signup delays)
    
    # JWT Authentication (for SQLite-only auth)
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"  # Change this in production!
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Feature Flags
    PDF_SUPPORT: bool = True
    DOC_SUMMARIZER_SUPPORT: bool = False
    PDF_SUMMARIZER_SUPPORT: bool = False
    
    # Vector Store Configuration
    VECTOR_STORE_BACKEND: str = "chromadb"  # Options: "chromadb", "faiss", "qdrant"
    VECTOR_STORE_PATH: str = "./knowledge_store"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_STORE_COLLECTION: str = "knowledge_base"
    
    # Vector Store Categories (for future use)
    # VECTOR_STORE_CATEGORIES: List[str] = ["vedas", "educational", "wellness", "unified"]
    
    # Pinecone Configuration (if using cloud)
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    # Qdrant Configuration (if using cloud/server)
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    
    # Weaviate Configuration (if using)
    WEAVIATE_URL: Optional[str] = None
    WEAVIATE_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
