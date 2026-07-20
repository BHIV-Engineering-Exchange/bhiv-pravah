# HR Portal Service

Streamlit-based internal dashboard for HR teams to manage candidates, jobs, and AI-powered matching in the BHIV HR Platform.

---

## Overview
The HR Portal is a comprehensive Streamlit-based dashboard for HR teams to manage the entire recruitment lifecycle. The portal provides tools for candidate management, job posting, AI-powered matching, values assessment, and analytics. It integrates with backend services through the Gateway API, offering real-time data synchronization and automated workflows.

## Architecture
The service follows a client-server architecture where the Streamlit frontend communicates with backend microservices through the Gateway API:

```
portal/
├── app.py              # Main Streamlit application with UI components
├── auth_manager.py     # Authentication management and API request handling
├── batch_upload.py     # Batch processing and resume upload functionality
├── config.py           # Configuration management and environment loading
├── email_automation.py # Email and communication automation
├── file_security.py    # File validation and security measures
├── components/         # Reusable UI components
├── Dockerfile          # Containerization configuration
└── requirements.txt    # Python dependencies
```

## Key Features
- **Comprehensive Dashboard:** Real-time metrics, analytics, and recruitment pipeline visualization
- **Advanced Candidate Search:** Sophisticated filtering and AI-powered matching capabilities
- **Job Management:** Create, edit, and manage job postings with client integration
- **Values Assessment:** 5-point BHIV values evaluation system (Integrity, Honesty, Discipline, Hard Work, Gratitude)
- **Batch Operations:** Secure candidate data import with resume processing
- **Interview Management:** Schedule and track interviews with automated notifications
- **AI Shortlisting:** Advanced semantic matching using Talah AI
- **Automated Communications:** Multi-channel notifications via email, WhatsApp, and Telegram
- **Security Measures:** File validation, path traversal protection, and 2FA
- **Export Capabilities:** Comprehensive reports with assessment data

## API Endpoints
The portal communicates with the Gateway service using the following endpoints:

### Authentication Endpoints
- `POST /v1/hr/login` - Authenticate HR credentials
- `GET /health` - Verify API connectivity

### Candidate Management Endpoints
- `GET /v1/candidates/search` - Search candidates with filters
- `POST /v1/candidates/bulk` - Upload multiple candidates
- `GET /v1/candidate/profile/{candidate_id}` - Get candidate profile
- `GET /v1/candidate/applications/{candidate_id}` - Get candidate applications
- `GET /v1/candidate/stats/{candidate_id}` - Get candidate statistics

### Statistics Endpoints
- `GET /v1/recruiter/stats` - Get recruiter dashboard statistics

### Job Management Endpoints
- `GET /v1/jobs` - Retrieve job listings
- `POST /v1/jobs` - Create new job listing

### Interview Management Endpoints
- `GET /v1/interviews` - Retrieve scheduled interviews
- `POST /v1/interviews` - Schedule new interview

### AI Agent Endpoints
- `POST /match` - Get AI-matched candidates for a job

## Authentication & Security Implementation
- **JWT Token Authentication:** Secure session management using JWT tokens
- **API Key Authorization:** Service-to-service communication secured with API keys
- **Password Hashing:** Bcrypt implementation for secure password storage
- **File Security:** Path traversal prevention and file validation
- **Environment Variables:** Sensitive configuration stored in environment variables
- **2FA Integration:** Two-factor authentication with QR code generation
- **Input Validation:** Client-side and server-side validation

## Database Integration
- **Indirect Access:** Portal accesses database through Gateway API endpoints
- **MongoDB Atlas:** Backend uses MongoDB Atlas for data persistence
- **No Direct Connection:** Portal does not connect directly to database
- **Connection Pooling:** Configured HTTP client with connection pooling
- **Timeout Management:** Proper timeout configurations for API calls

## Configuration Requirements
The service requires the following environment variables:
- `GATEWAY_SERVICE_URL` - URL of the Gateway service
- `API_KEY_SECRET` - API key for service authentication
- `JWT_SECRET_KEY` - Secret key for JWT token generation
- `CANDIDATE_JWT_SECRET_KEY` - Candidate-specific JWT secret
- `LANGGRAPH_SERVICE_URL` - URL of the LangGraph automation service
- `AGENT_SERVICE_URL` - URL of the AI agent service

## Deployment Instructions
### Local Development
```bash
cd services/portal
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### Docker Deployment
```bash
# Build container
docker build -t hr-portal .

# Run container
docker run -d --name hr-portal \
  -p 8501:8501 \
  -e GATEWAY_SERVICE_URL=http://gateway:8000 \
  -e API_KEY_SECRET=your_api_key \
  -e JWT_SECRET_KEY=your_jwt_secret \
  -e CANDIDATE_JWT_SECRET_KEY=your_candidate_jwt_secret \
  -e LANGGRAPH_SERVICE_URL=http://langgraph:9001 \
  -e AGENT_SERVICE_URL=http://agent:9000 \
  hr-portal
```

## Dependencies
- `streamlit` - Web application framework
- `httpx` - HTTP client with connection pooling and timeout management
- `pandas` - Data manipulation and analysis
- `plotly` - Interactive data visualization
- `numpy` - Numerical computing
- `python-dotenv` - Environment variable management
- `requests` - HTTP client for API communication
- `pillow` - Image processing for 2FA QR codes
- `qrcode[pil]` - QR code generation for 2FA

## Integration Points
- **Gateway Service:** Primary integration point for all backend operations
- **LangGraph Service:** Automation for notifications and workflow management
- **AI Agent Service:** AI-powered candidate matching and semantic analysis
- **MongoDB Atlas:** Data persistence through Gateway service
- **Communication Services:** Multi-channel notifications via email, WhatsApp, and Telegram

## Error Handling & Monitoring
- **API Connection Handling:** Graceful degradation when backend services are unavailable
- **Connection Pooling:** Configured HTTP client with proper limits
- **Timeout Management:** Proper timeout configurations for API calls
- **Form Validation:** Client-side validation with user-friendly error messages
- **Session Management:** Robust session handling with proper cleanup
- **Logging:** Comprehensive logging for debugging and monitoring
- **Fallback Mechanisms:** Error handling with user notifications

## Monitoring Capabilities
- **Real-time Metrics:** Live candidate counts, job statistics, and interview schedules
- **Recruitment Pipeline:** Visualization of application stages and conversion rates
- **AI Performance:** Metrics on AI matching effectiveness
- **Values Assessment:** Analysis of values alignment and cultural fit
- **System Status:** Health checks for connected services
