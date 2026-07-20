# Client Portal Service

Streamlit-based portal for external clients to post jobs, review candidates, and manage interviews in the BHIV HR Platform.

---

## Overview
The Client Portal is a Streamlit-based application designed for enterprise clients to securely post job listings, review AI-matched candidates, and coordinate interviews. The portal integrates with backend services through the Gateway API, providing a comprehensive interface for clients to manage their recruitment needs with real-time synchronization to HR and candidate portals.

## Architecture
The service follows a client-server architecture where the Streamlit frontend communicates with backend microservices through the Gateway API:

```
client_portal/
├── app.py              # Main Streamlit application with UI components
├── auth_manager.py     # Authentication management and API request handling
├── config.py           # Configuration management and environment loading
├── Dockerfile          # Containerization configuration
└── requirements.txt    # Python dependencies
```

## Key Features
- **Enterprise Authentication:** JWT-secured login and session management with optional 2FA
- **Job Posting Interface:** Intuitive form for creating, editing, and managing job listings
- **AI Candidate Review:** Advanced interface to view and shortlist AI-matched candidates
- **Interview Coordination:** Schedule and manage interviews with automated notifications
- **Real-Time Sync:** Instant updates with HR and candidate portals
- **Analytics Dashboard:** Real-time metrics and recruitment pipeline visualization
- **Multi-channel Communication:** Automated notifications via email, WhatsApp, and Telegram

## API Endpoints
The portal communicates with the Gateway service using the following endpoints:

### Authentication Endpoints
- `POST /v1/client/login` - Authenticate client credentials
- `POST /v1/client/register` - Register new client account

### Job Management Endpoints
- `GET /v1/jobs` - Retrieve job listings
- `POST /v1/jobs` - Create new job listing

### Candidate Management Endpoints
- `GET /v1/match/{job_id}/top` - Get AI-matched candidates for a job
- `GET /v1/candidates/search` - Search candidates with filters

### Health Check Endpoints
- `GET /health` - Verify API connectivity

### Statistics Endpoints
- `GET /v1/recruiter/stats` - Get recruiter dashboard statistics

## Authentication & Security Implementation
- **JWT Token Authentication:** Secure session management using JWT tokens
- **API Key Authorization:** Service-to-service communication secured with API keys
- **Password Hashing:** Bcrypt implementation for secure password storage
- **Environment Variables:** Sensitive configuration stored in environment variables
- **Session Management:** Robust session handling with proper cleanup
- **Input Validation:** Client-side and server-side validation

## Database Integration
- **Indirect Access:** Portal accesses database through Gateway API endpoints
- **MongoDB Atlas:** Backend uses MongoDB Atlas for data persistence
- **No Direct Connection:** Portal does not connect directly to database
- **Retry Strategy:** Configured HTTP session with retry strategy for resilience

## Configuration Requirements
The service requires the following environment variables:
- `GATEWAY_SERVICE_URL` - URL of the Gateway service
- `API_KEY_SECRET` - API key for service authentication
- `JWT_SECRET_KEY` - Secret key for JWT token generation
- `LANGGRAPH_SERVICE_URL` - URL of the LangGraph automation service

## Deployment Instructions
### Local Development
```bash
cd services/client_portal
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

### Docker Deployment
```bash
# Build container
docker build -t client-portal .

# Run container
docker run -d --name client-portal \
  -p 8502:8502 \
  -e GATEWAY_SERVICE_URL=http://gateway:8000 \
  -e API_KEY_SECRET=your_api_key \
  -e JWT_SECRET_KEY=your_jwt_secret \
  -e LANGGRAPH_SERVICE_URL=http://langgraph:9001 \
  client-portal
```

## Dependencies
- `streamlit` - Web application framework
- `requests` - HTTP client for API communication
- `httpx` - Alternative HTTP client with connection pooling
- `pandas` - Data manipulation and analysis
- `python-dotenv` - Environment variable management
- `bcrypt` - Password hashing
- `PyJWT` - JWT token handling
- `pillow` - Image processing for 2FA QR codes
- `qrcode[pil]` - QR code generation for 2FA

## Integration Points
- **Gateway Service:** Primary integration point for all backend operations
- **LangGraph Service:** Automation for notifications and workflow management
- **MongoDB Atlas:** Data persistence through Gateway service
- **AI Agent Service:** AI-powered candidate matching

## Error Handling & Monitoring
- **API Connection Handling:** Graceful degradation when backend services are unavailable
- **Retry Strategy:** Configured with 3 retries and exponential backoff
- **Form Validation:** Client-side validation with user-friendly error messages
- **Session Management:** Robust session handling with proper cleanup
- **Logging:** Comprehensive logging for debugging and monitoring

## Monitoring Capabilities
- **Real-time Metrics:** Live job counts and candidate statistics
- **Recruitment Pipeline:** Visualization of application stages
- **System Status:** Health checks for connected services
- **Activity Tracking:** Recent activity and trend analysis
