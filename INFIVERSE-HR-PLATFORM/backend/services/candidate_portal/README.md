# Candidate Portal Service

Streamlit-based portal for job seekers to register, search jobs, and manage applications in the BHIV HR Platform.

---

## Overview
The Candidate Portal is a Streamlit-based application that enables job seekers to register, manage their profiles, search and apply for jobs, and track application status. The portal integrates with backend services through secure API calls to the Gateway service, providing a seamless user experience for candidates seeking employment opportunities.

## Architecture
The service follows a client-server architecture where the Streamlit frontend communicates with backend microservices through the Gateway API:

```
candidate_portal/
├── app.py              # Main Streamlit application with UI components
├── auth_manager.py     # Authentication management and API request handling
├── config.py           # Configuration management and environment loading
├── Dockerfile          # Containerization configuration
└── requirements.txt    # Python dependencies
```

## Key Features
- **Secure Authentication:** JWT-based login and registration with password hashing
- **User Dashboard:** Personalized dashboard with application metrics and activity
- **Job Search & Filter:** Advanced filtering capabilities for job positions
- **Application Management:** Track and manage job applications with status updates
- **Profile Management:** Comprehensive profile editing with resume upload capability
- **Real-time Updates:** Live synchronization with job postings and application statuses
- **Multi-format Resume Support:** Accepts PDF, DOCX, and TXT resume formats

## API Endpoints
The portal communicates with the Gateway service using the following endpoints:

### Authentication Endpoints
- `POST /v1/candidate/login` - Authenticate candidate credentials
- `POST /v1/candidate/register` - Register new candidate account

### Job Management Endpoints
- `GET /v1/jobs` - Retrieve available job listings
- `POST /v1/candidate/apply` - Submit job application

### Profile Management Endpoints
- `GET /v1/candidate/profile/{candidate_id}` - Get candidate profile
- `PUT /v1/candidate/profile/{candidate_id}` - Update candidate profile
- `GET /v1/candidate/stats/{candidate_id}` - Get candidate statistics
- `GET /v1/candidate/applications/{candidate_id}` - Get candidate applications

## Authentication & Security Implementation
- **JWT Token Authentication:** Secure session management using JWT tokens
- **API Key Authorization:** Service-to-service communication secured with API keys
- **Password Hashing:** Bcrypt implementation for secure password storage
- **Environment Variables:** Sensitive configuration stored in environment variables
- **Input Validation:** Form validation and secure data handling

## Database Integration
- **Indirect Access:** Portal accesses database through Gateway API endpoints
- **MongoDB Atlas:** Backend uses MongoDB Atlas for data persistence
- **No Direct Connection:** Portal does not connect directly to database

## Configuration Requirements
The service requires the following environment variables:
- `GATEWAY_SERVICE_URL` - URL of the Gateway service
- `API_KEY_SECRET` - API key for service authentication
- `JWT_SECRET_KEY` - Secret key for JWT token generation
- `CANDIDATE_JWT_SECRET_KEY` - Candidate-specific JWT secret
- `LANGGRAPH_SERVICE_URL` - URL of the LangGraph automation service

## Deployment Instructions
### Local Development
```bash
cd services/candidate_portal
pip install -r requirements.txt
streamlit run app.py --server.port 8503
```

### Docker Deployment
```bash
# Build container
docker build -t candidate-portal .

# Run container
docker run -d --name candidate-portal \
  -p 8503:8503 \
  -e GATEWAY_SERVICE_URL=http://gateway:8000 \
  -e API_KEY_SECRET=your_api_key \
  -e JWT_SECRET_KEY=your_jwt_secret \
  candidate-portal
```

## Dependencies
- `streamlit` - Web application framework
- `requests` - HTTP client for API communication
- `pandas` - Data manipulation and analysis
- `python-dotenv` - Environment variable management
- `bcrypt` - Password hashing
- `PyJWT` - JWT token handling

## Integration Points
- **Gateway Service:** Primary integration point for all backend operations
- **LangGraph Service:** Automation for application notifications
- **MongoDB Atlas:** Data persistence through Gateway service

## Error Handling & Monitoring
- **API Connection Handling:** Graceful degradation when backend services are unavailable
- **Form Validation:** Client-side validation with user-friendly error messages
- **Session Management:** Robust session handling with proper cleanup
- **Logging:** Comprehensive logging for debugging and monitoring

## Monitoring Capabilities
- **Application Status Tracking:** Real-time monitoring of application progress
- **Job Search Analytics:** Tracking of candidate job searches and applications
- **User Engagement Metrics:** Dashboard views and profile updates
