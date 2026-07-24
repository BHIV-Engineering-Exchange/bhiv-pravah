from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator, ValidationError
from typing import List, Optional
import os
import logging


def safe_int(value: str, default: int) -> int:
    """Safely parse integer from environment variable"""
    try:
        return int(value)
    except (ValueError, TypeError):
        logging.warning(f"Invalid integer value '{value}', using default {default}")
        return default


def safe_float(value: str, default: float) -> float:
    """Safely parse float from environment variable"""
    try:
        return float(value)
    except (ValueError, TypeError):
        logging.warning(f"Invalid float value '{value}', using default {default}")
        return default


def safe_bool(value: str, default: bool) -> bool:
    """Safely parse boolean from environment variable"""
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


class Settings(BaseSettings):
    """Application settings with Sovereign Core integration"""
    
    # ========================================================================
    # Sovereign Core Configuration (Phase 2.2)
    # ========================================================================
    
    # Sovereign Core Auth
    SOVEREIGN_AUTH_URL: str = os.getenv(
        "SOVEREIGN_AUTH_URL",
        "http://localhost:8003/auth"
    )
    SOVEREIGN_SERVICE_KEY: str = os.getenv(
        "SOVEREIGN_SERVICE_KEY",
        "sovereign-service-key-placeholder"
    )
    SOVEREIGN_JWT_SECRET: str = os.getenv(
        "SOVEREIGN_JWT_SECRET",
        "sovereign-jwt-secret-placeholder"
    )
    SOVEREIGN_JWT_ALGORITHM: str = os.getenv(
        "SOVEREIGN_JWT_ALGORITHM",
        "HS256"
    )
    
    # Sovereign Core Database
    SOVEREIGN_DB_HOST: str = os.getenv(
        "SOVEREIGN_DB_HOST",
        "localhost"
    )
    SOVEREIGN_DB_PORT: int = safe_int(os.getenv("SOVEREIGN_DB_PORT", "5432"), 5432)
    SOVEREIGN_DB_NAME: str = os.getenv(
        "SOVEREIGN_DB_NAME",
        "sovereign_core"
    )
    SOVEREIGN_DB_USER: str = os.getenv(
        "SOVEREIGN_DB_USER",
        "sovereign_user"
    )
    SOVEREIGN_DB_PASSWORD: str = os.getenv(
        "SOVEREIGN_DB_PASSWORD",
        "sovereign_password"
    )
    
    # Migration toggle
    USE_SOVEREIGN_CORE: bool = safe_bool(os.getenv("USE_SOVEREIGN_CORE", "false"), False)
    
    # Backward compatibility (Supabase)
    # These are kept for transition period
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    
    # Application Configuration
    APP_NAME: str = "InsightFlow"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Q-Learning Hyperparameters
    LEARNING_RATE: float = 0.1
    DISCOUNT_FACTOR: float = 0.95
    EPSILON: float = 0.1
    MIN_EPSILON: float = 0.01
    EPSILON_DECAY: float = 0.995
    
    # Core Feedback Service Configuration
    CORE_FEEDBACK_SERVICE_URL: str = os.getenv(
        "CORE_FEEDBACK_SERVICE_URL",
        "http://core-feedback:8000/api/scores"
    )
    CORE_FEEDBACK_CACHE_TTL: int = safe_int(os.getenv("CORE_FEEDBACK_CACHE_TTL", "30"), 30)
    CORE_FEEDBACK_TIMEOUT: int = safe_int(os.getenv("CORE_FEEDBACK_TIMEOUT", "5"), 5)
    CORE_FEEDBACK_MAX_RETRIES: int = safe_int(os.getenv("CORE_FEEDBACK_MAX_RETRIES", "3"), 3)
    
    # Routing Decision Logging
    ROUTING_LOG_DIR: str = os.getenv(
        "ROUTING_LOG_DIR",
        "logs"
    )
    ROUTING_LOG_RETENTION_DAYS: int = safe_int(os.getenv("ROUTING_LOG_RETENTION_DAYS", "30"), 30)
    
    # ========================================================================
    # STP-Layer Configuration (Phase 2.2)
    # ========================================================================
    
    # Enable/disable STP wrapping (for gradual rollout)
    STP_ENABLED: bool = safe_bool(os.getenv("STP_ENABLED", "true"), True)
    
    # STP destination system
    STP_DESTINATION: str = os.getenv("STP_DESTINATION", "sovereign_core")
    
    # Default STP priority
    STP_DEFAULT_PRIORITY: str = os.getenv("STP_DEFAULT_PRIORITY", "normal")
    
    # Require acknowledgment for critical packets
    STP_REQUIRE_ACK: bool = safe_bool(os.getenv("STP_REQUIRE_ACK", "false"), False)
    
    # ========================================================================
    # Karma Weighting Configuration (Phase 2.2)
    # ========================================================================
    
    # Karma Tracker endpoint URL
    KARMA_ENDPOINT: str = os.getenv(
        "KARMA_ENDPOINT",
        "http://localhost:8002/api/karma"
    )
    
    # Enable/disable Karma weighting
    KARMA_ENABLED: bool = safe_bool(os.getenv("KARMA_ENABLED", "true"), True)
    
    # Karma cache TTL (seconds)
    KARMA_CACHE_TTL: int = safe_int(os.getenv("KARMA_CACHE_TTL", "60"), 60)
    
    # Karma request timeout (seconds)
    KARMA_TIMEOUT: int = safe_int(os.getenv("KARMA_TIMEOUT", "5"), 5)
    
    # Karma weight in scoring (0-1)
    KARMA_WEIGHT: float = safe_float(os.getenv("KARMA_WEIGHT", "0.15"), 0.15)
    
    # ========================================================================
    # Telemetry Bus Configuration (V3)
    # ========================================================================
    
    # Enable telemetry streaming
    TELEMETRY_ENABLED: bool = safe_bool(os.getenv("TELEMETRY_ENABLED", "true"), True)
    
    # Maximum telemetry queue size
    TELEMETRY_MAX_QUEUE_SIZE: int = safe_int(os.getenv("TELEMETRY_MAX_QUEUE_SIZE", "1000"), 1000)
    
    # Maximum concurrent WebSocket connections
    TELEMETRY_MAX_CONNECTIONS: int = safe_int(os.getenv("TELEMETRY_MAX_CONNECTIONS", "100"), 100)
    
    # WebSocket rate limit (messages per second per connection)
    TELEMETRY_RATE_LIMIT: int = safe_int(os.getenv("TELEMETRY_RATE_LIMIT", "200"), 200)
    
    # Telemetry WebSocket endpoint
    TELEMETRY_ENDPOINT: str = os.getenv("TELEMETRY_ENDPOINT", "/telemetry/stream")
    
    # Telemetry buffer size (backward compatibility)
    TELEMETRY_BUFFER_SIZE: int = safe_int(os.getenv("TELEMETRY_BUFFER_SIZE", "1000"), 1000)
    
    # Telemetry authentication required
    TELEMETRY_AUTH_REQUIRED: bool = safe_bool(os.getenv("TELEMETRY_AUTH_REQUIRED", "false"), False)
    
    # ========================================================================
    # Telemetry Security Configuration (Phase 3.1)
    # ========================================================================
    
    # Enable telemetry packet signing
    ENABLE_TELEMETRY_SIGNING: bool = safe_bool(os.getenv("ENABLE_TELEMETRY_SIGNING", "true"), True)
    
    # Telemetry packet signing (alias for backward compatibility)
    TELEMETRY_PACKET_SIGNING: bool = safe_bool(os.getenv("TELEMETRY_PACKET_SIGNING", "false"), False)
    
    # Maximum timestamp drift for verification (seconds)
    TELEMETRY_MAX_TIMESTAMP_DRIFT: int = safe_int(os.getenv("TELEMETRY_MAX_TIMESTAMP_DRIFT", "5"), 5)
    
    # Telemetry signature verification timeout (alias)
    TELEMETRY_SIGNATURE_TIMEOUT: int = safe_int(os.getenv("TELEMETRY_SIGNATURE_TIMEOUT", "5"), 5)
    
    # ========================================================================
    # STP Feedback Configuration (V3 Phase C)
    # ========================================================================
    
    # Enable STP feedback enrichment
    ENABLE_FEEDBACK: bool = safe_bool(os.getenv("ENABLE_FEEDBACK", "false"), False)
    
    # STP version
    STP_VERSION: str = os.getenv("STP_VERSION", "stp-1")
    
    # Enable Q-learning updates
    ENABLE_Q_UPDATES: bool = safe_bool(os.getenv("ENABLE_Q_UPDATES", "false"), False)
    
    # Enable karma weighting in Q-learning
    ENABLE_KARMA_WEIGHTING: bool = safe_bool(os.getenv("ENABLE_KARMA_WEIGHTING", "false"), False)
    
    # ========================================================================
    # Q-Learning Configuration (V3 Phase D)
    # ========================================================================
    
    # Q-learning parameters
    Q_LEARNING_RATE: float = safe_float(os.getenv("Q_LEARNING_RATE", "0.1"), 0.1)
    
    Q_DISCOUNT_FACTOR: float = safe_float(os.getenv("Q_DISCOUNT_FACTOR", "0.95"), 0.95)
    
    # Validation methods
    @validator('LEARNING_RATE')
    def validate_learning_rate(cls, v):
        if not 0.001 <= v <= 1.0:
            raise ValueError('Learning rate must be between 0.001 and 1.0')
        return v
    
    @validator('DISCOUNT_FACTOR')
    def validate_discount_factor(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Discount factor must be between 0.0 and 1.0')
        return v
    
    @validator('EPSILON')
    def validate_epsilon(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Epsilon must be between 0.0 and 1.0')
        return v
    
    @validator('KARMA_CACHE_TTL')
    def validate_karma_cache_ttl(cls, v):
        if not 1 <= v <= 3600:
            raise ValueError('Karma cache TTL must be between 1 and 3600 seconds')
        return v
    
    @validator('KARMA_TIMEOUT')
    def validate_karma_timeout(cls, v):
        if not 1 <= v <= 30:
            raise ValueError('Karma timeout must be between 1 and 30 seconds')
        return v
    
    @validator('KARMA_WEIGHT')
    def validate_karma_weight(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Karma weight must be between 0.0 and 1.0')
        return v
    
    @validator('JWT_EXPIRATION_MINUTES')
    def validate_jwt_expiration(cls, v):
        if not 5 <= v <= 1440:  # 5 minutes to 24 hours
            raise ValueError('JWT expiration must be between 5 and 1440 minutes')
        return v
    
    @validator('SOVEREIGN_DB_PORT')
    def validate_db_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Database port must be between 1 and 65535')
        return v
    
    @validator('SOVEREIGN_SERVICE_KEY')
    def validate_sovereign_service_key(cls, v):
        if 'placeholder' in v.lower():
            raise ValueError('SOVEREIGN_SERVICE_KEY cannot use placeholder value in production')
        if len(v) < 16:
            raise ValueError('SOVEREIGN_SERVICE_KEY must be at least 16 characters long')
        return v
    
    @validator('SOVEREIGN_JWT_SECRET')
    def validate_sovereign_jwt_secret(cls, v):
        if 'placeholder' in v.lower():
            raise ValueError('SOVEREIGN_JWT_SECRET cannot use placeholder value in production')
        if len(v) < 32:
            raise ValueError('SOVEREIGN_JWT_SECRET must be at least 32 characters long for security')
        return v
    
    @validator('TELEMETRY_SIGNATURE_TIMEOUT')
    def validate_telemetry_signature_timeout(cls, v):
        if not 1 <= v <= 30:
            raise ValueError('Telemetry signature timeout must be between 1 and 30 seconds')
        return v
    
    @validator('TELEMETRY_MAX_TIMESTAMP_DRIFT')
    def validate_telemetry_max_timestamp_drift(cls, v):
        if not 1 <= v <= 60:
            raise ValueError('Telemetry max timestamp drift must be between 1 and 60 seconds')
        return v
    
    @validator('JWT_SECRET_KEY')
    def validate_jwt_secret_key(cls, v):
        if v == 'your-super-secret-key-change-in-production':
            raise ValueError('JWT_SECRET_KEY cannot use default placeholder value')
        if len(v) < 32:
            raise ValueError('JWT_SECRET_KEY must be at least 32 characters long for security')
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    def validate_config(self) -> bool:
        """Validate configuration after initialization"""
        try:
            # Additional cross-field validation
            if self.MIN_EPSILON >= self.EPSILON:
                raise ValueError('MIN_EPSILON must be less than EPSILON')
            
            if self.USE_SOVEREIGN_CORE and not all([
                self.SOVEREIGN_DB_HOST,
                self.SOVEREIGN_DB_NAME,
                self.SOVEREIGN_DB_USER,
                self.SOVEREIGN_DB_PASSWORD
            ]):
                raise ValueError('Sovereign Core enabled but database config incomplete')
            
            # Production security validation
            if self.ENVIRONMENT == 'production':
                self._validate_production_secrets()
            
            return True
        except Exception as e:
            logging.error(f"Configuration validation failed: {e}")
            return False
    
    def _validate_production_secrets(self):
        """Validate that all secrets are properly configured for production"""
        security_issues = []
        
        # Check for placeholder values
        if 'placeholder' in self.SOVEREIGN_SERVICE_KEY.lower():
            security_issues.append('SOVEREIGN_SERVICE_KEY uses placeholder value')
        
        if 'placeholder' in self.SOVEREIGN_JWT_SECRET.lower():
            security_issues.append('SOVEREIGN_JWT_SECRET uses placeholder value')
        
        if self.JWT_SECRET_KEY == 'your-super-secret-key-change-in-production':
            security_issues.append('JWT_SECRET_KEY uses default placeholder value')
        
        # Check for weak passwords
        if self.SOVEREIGN_DB_PASSWORD == 'sovereign_password':
            security_issues.append('SOVEREIGN_DB_PASSWORD uses default weak password')
        
        # Check secret lengths
        if len(self.JWT_SECRET_KEY) < 32:
            security_issues.append('JWT_SECRET_KEY is too short (minimum 32 characters)')
        
        if len(self.SOVEREIGN_SERVICE_KEY) < 16:
            security_issues.append('SOVEREIGN_SERVICE_KEY is too short (minimum 16 characters)')
        
        if len(self.SOVEREIGN_JWT_SECRET) < 32:
            security_issues.append('SOVEREIGN_JWT_SECRET is too short (minimum 32 characters)')
        
        if security_issues:
            raise ValueError(f"Production security validation failed: {'; '.join(security_issues)}")
    
    def validate_production_config(self) -> tuple[bool, list[str]]:
        """Validate configuration for production deployment"""
        warnings = []
        
        # Check for localhost defaults
        if 'localhost' in self.SOVEREIGN_DB_HOST:
            warnings.append('SOVEREIGN_DB_HOST uses localhost (not suitable for production)')
        
        if 'localhost' in self.SOVEREIGN_AUTH_URL:
            warnings.append('SOVEREIGN_AUTH_URL uses localhost (not suitable for production)')
        
        if 'localhost' in self.KARMA_ENDPOINT:
            warnings.append('KARMA_ENDPOINT uses localhost (not suitable for production)')
        
        # Check for placeholder values
        if 'placeholder' in self.SOVEREIGN_SERVICE_KEY:
            warnings.append('SOVEREIGN_SERVICE_KEY uses placeholder value (security risk)')
        
        if 'placeholder' in self.SOVEREIGN_JWT_SECRET:
            warnings.append('SOVEREIGN_JWT_SECRET uses placeholder value (security risk)')
        
        if self.JWT_SECRET_KEY == 'your-super-secret-key-change-in-production':
            warnings.append('JWT_SECRET_KEY uses default value (security risk)')
        
        # Check for weak secrets
        if len(self.JWT_SECRET_KEY) < 32:
            warnings.append('JWT_SECRET_KEY is too short (security risk)')
        
        if len(self.SOVEREIGN_SERVICE_KEY) < 16:
            warnings.append('SOVEREIGN_SERVICE_KEY is too short (security risk)')
        
        if self.SOVEREIGN_DB_PASSWORD == 'sovereign_password':
            warnings.append('SOVEREIGN_DB_PASSWORD uses default weak password (security risk)')
        
        # Check environment settings
        if self.ENVIRONMENT == 'production' and self.DEBUG:
            warnings.append('DEBUG=True in production environment (security risk)')
        
        # Check CORS for localhost
        localhost_cors = [origin for origin in self.CORS_ORIGINS if 'localhost' in origin]
        if localhost_cors and self.ENVIRONMENT == 'production':
            warnings.append(f'CORS_ORIGINS contains localhost entries: {localhost_cors}')
        
        is_production_ready = len(warnings) == 0
        return is_production_ready, warnings
    
    def validate_migration_config(self) -> tuple[str, list[str]]:
        """Validate Supabase to Sovereign Core migration configuration"""
        issues = []
        
        if self.USE_SOVEREIGN_CORE:
            # Sovereign Core mode - validate Sovereign config
            if not all([self.SOVEREIGN_DB_HOST, self.SOVEREIGN_DB_NAME, 
                       self.SOVEREIGN_DB_USER, self.SOVEREIGN_DB_PASSWORD]):
                issues.append('Sovereign Core enabled but database configuration incomplete')
            
            if 'placeholder' in self.SOVEREIGN_SERVICE_KEY:
                issues.append('Sovereign Core enabled but service key is placeholder')
            
            # Check if Supabase config still present (migration incomplete)
            if any([self.SUPABASE_URL, self.SUPABASE_ANON_KEY, self.SUPABASE_SERVICE_KEY]):
                issues.append('Migration incomplete: Both Supabase and Sovereign Core configs present')
            
            migration_status = 'sovereign_core'
        else:
            # Supabase mode - validate Supabase config
            if not all([self.SUPABASE_URL, self.SUPABASE_ANON_KEY, self.SUPABASE_SERVICE_KEY]):
                issues.append('Supabase mode but configuration incomplete')
            
            migration_status = 'supabase'
        
        return migration_status, issues
    
    def get_migration_guide(self) -> dict:
        """Get migration guide from Supabase to Sovereign Core"""
        return {
            'current_mode': 'sovereign_core' if self.USE_SOVEREIGN_CORE else 'supabase',
            'migration_steps': [
                '1. Set up Sovereign Core database with schema',
                '2. Configure SOVEREIGN_DB_* environment variables',
                '3. Generate and set SOVEREIGN_SERVICE_KEY and SOVEREIGN_JWT_SECRET',
                '4. Test connection with USE_SOVEREIGN_CORE=true',
                '5. Migrate data from Supabase to Sovereign Core',
                '6. Remove SUPABASE_* environment variables',
                '7. Validate configuration with validate_migration_config()'
            ],
            'required_env_vars': {
                'sovereign_core': [
                    'USE_SOVEREIGN_CORE=true',
                    'SOVEREIGN_DB_HOST=your-db-host',
                    'SOVEREIGN_DB_NAME=your-db-name',
                    'SOVEREIGN_DB_USER=your-db-user',
                    'SOVEREIGN_DB_PASSWORD=your-db-password',
                    'SOVEREIGN_SERVICE_KEY=your-service-key',
                    'SOVEREIGN_JWT_SECRET=your-jwt-secret'
                ],
                'supabase_removal': [
                    'Remove SUPABASE_URL',
                    'Remove SUPABASE_ANON_KEY',
                    'Remove SUPABASE_SERVICE_KEY'
                ]
            }
        }


# Create and validate global settings instance
try:
    settings = Settings()
    if not settings.validate_config():
        raise ValueError("Configuration validation failed")
    
    # Log migration status
    migration_status, migration_issues = settings.validate_migration_config()
    if migration_issues:
        for issue in migration_issues:
            logging.warning(f"Migration issue: {issue}")
    else:
        logging.info(f"Migration status: {migration_status} (validated)")
        
except ValidationError as e:
    logging.error(f"Configuration validation error: {e}")
    raise
except Exception as e:
    logging.error(f"Configuration initialization error: {e}")
    raise