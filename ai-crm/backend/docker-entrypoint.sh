#!/bin/bash

# AI Agent CRM System - Docker Entrypoint Script
# Handles initialization, security, and service startup

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to check required environment variables
check_environment() {
    log "Checking environment configuration..."
    
    # Required environment variables
    REQUIRED_VARS=(
        "DATABASE_URL"
        "SECRET_KEY"
    )
    
    # Optional but recommended variables
    OPTIONAL_VARS=(
        "OFFICE365_CLIENT_ID"
        "OFFICE365_CLIENT_SECRET" 
        "OFFICE365_TENANT_ID"
        "GOOGLE_MAPS_API_KEY"
        "OPENAI_API_KEY"
        "REDIS_URL"
        "LOG_LEVEL"
    )
    
    missing_required=0
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "Required environment variable $var is not set"
            missing_required=1
        fi
    done
    
    for var in "${OPTIONAL_VARS[@]}"; do
        if [[ -z "${!var}" ]]; then
            warn "Optional environment variable $var is not set - some features may be disabled"
        fi
    done
    
    if [[ $missing_required -eq 1 ]]; then
        error "Missing required environment variables. Cannot start."
        exit 1
    fi
    
    success "Environment configuration validated"
}

# Function to initialize database
init_database() {
    log "Initializing database..."
    
    # Create data directory if it doesn't exist
    mkdir -p /app/data
    
    # Run database initialization
    python -c "
from database.models import create_tables, init_database
try:
    create_tables()
    init_database()
    print('Database initialized successfully')
except Exception as e:
    print(f'Database initialization failed: {e}')
    exit(1)
"
    
    if [[ $? -eq 0 ]]; then
        success "Database initialized successfully"
    else
        error "Database initialization failed"
        exit 1
    fi
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Add migration logic here if needed
    python -c "
from database.models import create_tables
try:
    create_tables()
    print('Migrations completed successfully')
except Exception as e:
    print(f'Migrations failed: {e}')
    exit(1)
"
    
    success "Database migrations completed"
}

# Function to validate integrations
validate_integrations() {
    log "Validating external integrations..."
    
    # Test Office 365 integration
    if [[ -n "$OFFICE365_CLIENT_ID" && -n "$OFFICE365_CLIENT_SECRET" ]]; then
        python -c "
from integrations.office365_integration import Office365Integration
try:
    office365 = Office365Integration()
    print('Office 365 integration: Ready')
except Exception as e:
    print(f'Office 365 integration: Error - {e}')
"
    else
        warn "Office 365 integration: Not configured"
    fi
    
    # Test Google Maps integration
    if [[ -n "$GOOGLE_MAPS_API_KEY" ]]; then
        python -c "
from integrations.google_maps_integration import GoogleMapsIntegration
try:
    maps = GoogleMapsIntegration()
    print('Google Maps integration: Ready')
except Exception as e:
    print(f'Google Maps integration: Error - {e}')
"
    else
        warn "Google Maps integration: Not configured"
    fi
    
    # Test OpenAI integration
    if [[ -n "$OPENAI_API_KEY" ]]; then
        python -c "
from integrations.llm_query_system import LLMQuerySystem
try:
    llm = LLMQuerySystem()
    print('OpenAI LLM integration: Ready')
except Exception as e:
    print(f'OpenAI LLM integration: Error - {e}')
"
    else
        warn "OpenAI LLM integration: Not configured"
    fi
    
    success "Integration validation completed"
}

# Function to start services in development mode
start_development() {
    log "Starting services in development mode..."
    
    # Start all services with hot reload
    python -m uvicorn api_app:app --host 0.0.0.0 --port 8000 --reload &
    python -m uvicorn crm_api:crm_app --host 0.0.0.0 --port 8001 --reload &
    
    # Wait a bit for APIs to start
    sleep 5
    
    # Start dashboards
    streamlit run dashboard_with_supplier.py --server.port=8502 --server.address=0.0.0.0 &
    streamlit run crm_dashboard.py --server.port=8501 --server.address=0.0.0.0 &
    
    success "All services started in development mode"
    
    # Keep container running
    wait
}

# Function to start services in production mode
start_production() {
    log "Starting services in production mode..."
    
    # Start main API
    python -m uvicorn api_app:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --access-log \
        --log-config logging.conf &
    
    # Start CRM API
    python -m uvicorn crm_api:crm_app \
        --host 0.0.0.0 \
        --port 8001 \
        --workers 2 \
        --worker-class uvicorn.workers.UvicornWorker \
        --access-log \
        --log-config logging.conf &
    
    # Wait for APIs to be ready
    sleep 10
    
    # Start dashboards
    streamlit run dashboard_with_supplier.py \
        --server.port=8502 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --server.enableCORS=false &
    
    streamlit run crm_dashboard.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --server.enableCORS=false &
    
    success "All services started in production mode"
    
    # Health check loop
    while true; do
        # Check if services are running
        if ! curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            error "Main API health check failed"
        fi
        
        if ! curl -sf http://localhost:8001/health > /dev/null 2>&1; then
            error "CRM API health check failed"
        fi
        
        sleep 30
    done
}

# Function to run tests
run_tests() {
    log "Running comprehensive test suite..."
    
    python test_crm_comprehensive.py
    
    if [[ $? -eq 0 ]]; then
        success "All tests passed"
    else
        error "Some tests failed"
        exit 1
    fi
}

# Function to backup data
backup_data() {
    log "Creating data backup..."
    
    BACKUP_DIR="/app/backups"
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    mkdir -p "$BACKUP_DIR"
    
    tar -czf "$BACKUP_DIR/$BACKUP_FILE" /app/data/ /app/logs/
    
    success "Backup created: $BACKUP_FILE"
}

# Main execution logic
main() {
    log "AI Agent CRM System - Starting up..."
    log "Version: ${VERSION:-unknown}"
    log "Environment: ${ENVIRONMENT:-development}"
    
    # Parse command line arguments
    case "${1:-development}" in
        "development"|"dev")
            log "Running in development mode"
            check_environment
            init_database
            validate_integrations
            start_development
            ;;
        "production"|"prod")
            log "Running in production mode"
            check_environment
            run_migrations
            validate_integrations
            start_production
            ;;
        "test")
            log "Running test suite"
            check_environment
            init_database
            run_tests
            ;;
        "backup")
            log "Creating backup"
            backup_data
            ;;
        "shell")
            log "Starting interactive shell"
            exec /bin/bash
            ;;
        *)
            error "Unknown command: $1"
            echo "Usage: $0 {development|production|test|backup|shell}"
            exit 1
            ;;
    esac
}

# Handle shutdown signals gracefully
shutdown() {
    log "Received shutdown signal, stopping services..."
    pkill -f uvicorn
    pkill -f streamlit
    success "Services stopped gracefully"
    exit 0
}

trap shutdown SIGTERM SIGINT

# Run main function
main "$@"