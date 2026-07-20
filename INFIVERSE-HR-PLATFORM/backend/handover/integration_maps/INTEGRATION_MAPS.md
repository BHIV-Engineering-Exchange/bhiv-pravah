# Integration Maps — BHIV HR Platform

**Version**: 4.3.0  
**Architecture**: Microservices (6 services)  
**Integration Type**: REST APIs, Event-driven workflows  
**Last Updated**: December 9, 2025

---

## Table of Contents

1. [Map 1: HR Platform → AI Agent Integration](#map-1-hr-platform--ai-agent-integration)
2. [Map 2: LangGraph Workflow Automation](#map-2-langgraph-workflow-automation)
3. [Map 3: Triple Portal Authentication Flow](#map-3-triple-portal-authentication-flow)
4. [Map 4: RL Feedback Loop Integration](#map-4-rl-feedback-loop-integration)
5. [Map 5: End-to-End Candidate Journey](#map-5-end-to-end-candidate-journey)
6. [Integration Summary](#integration-summary)

---

## Map 1: HR Platform → AI Agent Integration

**Purpose**: Show how Gateway service integrates with AI Agent for semantic candidate matching

### Architecture Diagram

```mermaid
sequenceDiagram
    participant Client as Client/HR Portal
    participant Gateway as API Gateway<br/>(Port 8000)
    participant DB as MongoDB Atlas<br/>Database
    participant Agent as AI Agent Service<br/>(Port 8001)
    participant Cache as Matching Cache

    Client->>Gateway: POST /v1/match/{job_id}/top
    Note over Client,Gateway: Bearer Token Authentication
    
    Gateway->>Gateway: Validate API Key/JWT
    Gateway->>DB: SELECT job requirements<br/>WHERE id = job_id
    DB-->>Gateway: Job data (title, requirements, location)
    
    Gateway->>DB: SELECT candidates<br/>WHERE status = 'active'
    DB-->>Gateway: Candidate list (skills, experience)
    
    Gateway->>Agent: POST /match<br/>{"job_id": 1, "candidate_ids": []}
    Note over Gateway,Agent: Internal API call with API key
    
    Agent->>Agent: Phase 3 Semantic Engine<br/>- Load sentence transformer<br/>- Encode job requirements<br/>- Encode candidate profiles
    
    Agent->>Agent: Calculate Match Scores<br/>- Skills similarity (40%)<br/>- Experience match (30%)<br/>- Location match (20%)<br/>- Values alignment (10%)
    
    Agent->>Agent: Rank candidates by score<br/>Sort descending
    
    Agent-->>Gateway: {"top_candidates": [<br/>  {"candidate_id": 1, "score": 87.5},<br/>  {"candidate_id": 2, "score": 82.3}<br/>], "algorithm_version": "v3.0.0"}
    
    Gateway->>Cache: INSERT INTO matching_cache<br/>(job_id, candidate_id, match_score)
    Cache-->>Gateway: Cache updated
    
    Gateway-->>Client: {"matches": [...],<br/>"algorithm_version": "v3.0.0",<br/>"processing_time": "0.45s"}
```

### Integration Details

**Endpoint**: `POST /v1/match/{job_id}/top`  
**Gateway Service**: `services/gateway/app/main.py` (lines 1150-1220)  
**Agent Service**: `services/agent/app.py` (lines 200-350)  
**Algorithm**: Phase 3 Semantic Engine (`services/agent/semantic_engine/phase3_engine.py`)

**Request Flow**:
1. Client sends match request to Gateway with job_id
2. Gateway validates authentication (API key or JWT)
3. Gateway fetches job and candidate data from MongoDB Atlas
4. Gateway calls Agent service `/match` endpoint
5. Agent loads sentence transformer model (all-MiniLM-L6-v2)
6. Agent encodes job requirements and candidate profiles
7. Agent calculates cosine similarity scores
8. Agent applies weighted scoring (skills 40%, experience 30%, location 20%, values 10%)
9. Agent returns top candidates sorted by score
10. Gateway caches results in `matching_cache` table
11. Gateway returns formatted response to client

**Fallback Mechanism**:
- If Agent service unavailable → Gateway uses database fallback matching
- Fallback algorithm: Basic keyword matching with lower accuracy
- Response includes `"agent_status": "disconnected"` flag

**Performance**:
- Agent processing time: 0.02-0.5s per job
- Batch processing: 50 candidates per chunk
- Cache TTL: Results cached indefinitely (invalidate on profile update)

**Error Handling**:
- Agent timeout (60s) → Fallback to database matching
- Agent 500 error → Log error, return fallback results
- Database error → Return 500 with error message

---

## Map 2: LangGraph Workflow Automation

**Purpose**: Show automated workflow execution for candidate lifecycle events

### Architecture Diagram

```mermaid
graph TB
    subgraph "Trigger Events"
        E1[Candidate Applied]
        E2[Candidate Shortlisted]
        E3[Interview Scheduled]
    end
    
    subgraph "API Gateway (Port 8000)"
        GW[Gateway Service]
        WF[Workflow Trigger<br/>/v1/langgraph/trigger]
    end
    
    subgraph "LangGraph Service (Port 8003)"
        LG[LangGraph Orchestrator]
        WFE[Workflow Engine]
        
        subgraph "Workflow Steps"
            S1[Step 1: Validate Input]
            S2[Step 2: AI Analysis]
            S3[Step 3: Send Notifications]
            S4[Step 4: Update Status]
            S5[Step 5: Log Completion]
        end
        
        subgraph "Communication Channels"
            EMAIL[Email Service<br/>Gmail SMTP]
            WA[WhatsApp<br/>Twilio API]
            TG[Telegram<br/>Bot API]
        end
    end
    
    subgraph "Database"
        DB[(MongoDB Atlas)]
        WFT[workflows table]
        AUDIT[audit_logs table]
    end
    
    E1 --> GW
    E2 --> GW
    E3 --> GW
    
    GW --> WF
    WF --> LG
    
    LG --> WFE
    WFE --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    
    S3 --> EMAIL
    S3 --> WA
    S3 --> TG
    
    WFE --> DB
    S1 --> WFT
    S4 --> WFT
    S5 --> WFT
    S5 --> AUDIT
    
    EMAIL -.->|Delivery Status| WFE
    WA -.->|Delivery Status| WFE
    TG -.->|Delivery Status| WFE

    style E1 fill:#e1f5ff
    style E2 fill:#e1f5ff
    style E3 fill:#e1f5ff
    style LG fill:#fff4e1
    style WFE fill:#fff4e1
    style EMAIL fill:#e8f5e9
    style WA fill:#e8f5e9
    style TG fill:#e8f5e9
```

### Integration Details

**Workflow Trigger Endpoint**: `POST /v1/langgraph/trigger`  
**Gateway Integration**: `services/gateway/langgraph_integration.py` (lines 50-120)  
**LangGraph Service**: `services/langgraph/app/main.py` (lines 100-250)  
**Communication Module**: `services/langgraph/app/communication.py` (lines 1-200)

**Workflow Types**:
1. **candidate_application** - Triggered when candidate applies
2. **candidate_shortlisted** - Triggered when candidate shortlisted
3. **interview_scheduled** - Triggered when interview scheduled
4. **custom** - Custom workflow defined by client

**Workflow Execution Flow**:

```json
{
  "workflow_id": "wf_abc123",
  "workflow_type": "candidate_application",
  "input_data": {
    "candidate_id": 1,
    "job_id": 1,
    "candidate_email": "alice@example.com",
    "job_title": "Senior Python Developer"
  }
}
```

**Step-by-Step Execution**:

1. **Step 1: Validate Input** (0.1s)
   - Verify candidate_id exists in database
   - Verify job_id exists in database
   - Check email format validity
   - Create workflow record in `workflows` table

2. **Step 2: AI Analysis** (0.5s)
   - Call AI Agent for candidate-job matching
   - Get match score and reasoning
   - Store in `matching_cache` table

3. **Step 3: Send Notifications** (2-5s)
   - **Email**: Send confirmation to candidate via Gmail SMTP
   - **WhatsApp**: Send notification via Twilio API (if phone provided)
   - **Telegram**: Send notification via Telegram Bot API (if configured)
   - Parallel execution for all channels

4. **Step 4: Update Status** (0.2s)
   - Update candidate status in database
   - Update workflow progress to 80%
   - Log status change in audit_logs

5. **Step 5: Log Completion** (0.1s)
   - Mark workflow as completed
   - Set progress to 100%
   - Record completion timestamp
   - Log to audit_logs

**Total Execution Time**: 3-6 seconds (depending on notification delivery)

**Notification Endpoints**:
- **Direct Send**: `POST /tools/send-notification` (confirmed working)
- **Email**: Uses Gmail SMTP with app password
- **WhatsApp**: Uses Twilio API with account SID and auth token
- **Telegram**: Uses Telegram Bot API with bot token

**Error Handling**:
- Notification failure → Log error, continue workflow
- Database error → Rollback transaction, mark workflow as failed
- Timeout (120s) → Mark workflow as failed, log error

**Monitoring**:
- Workflow status tracked in `workflows` table
- Real-time progress updates via `progress_percentage` field
- Audit trail in `audit_logs` table

---

## Map 3: Triple Portal Authentication Flow

**Purpose**: Show authentication flow for HR Portal, Client Portal, and Candidate Portal

### Architecture Diagram

```mermaid
sequenceDiagram
    participant User as User/Client/Candidate
    participant Portal as Portal UI<br/>(Streamlit)
    participant Gateway as API Gateway<br/>(Port 8000)
    participant DB as MongoDB Atlas<br/>Database
    participant Auth as Auth Manager<br/>(auth_manager.py)

    Note over User,Auth: Three Authentication Flows

    rect rgb(230, 240, 255)
        Note over User,Auth: Flow 1: HR Portal (Internal Users)
        User->>Portal: Login (username, password)
        Portal->>Auth: validate_credentials(username, password)
        Auth->>DB: SELECT * FROM users<br/>WHERE username = ?
        DB-->>Auth: User record + password_hash
        Auth->>Auth: bcrypt.checkpw(password, hash)
        
        alt 2FA Enabled
            Auth-->>Portal: Require 2FA
            Portal-->>User: Show 2FA prompt
            User->>Portal: Enter TOTP code
            Portal->>Gateway: POST /v1/auth/2fa/verify
            Gateway->>Gateway: pyotp.verify(code, secret)
            Gateway-->>Portal: 2FA verified
        end
        
        Auth->>Auth: Generate session token
        Auth-->>Portal: {"authenticated": true, "role": "hr_manager"}
        Portal-->>User: Redirect to dashboard
    end

    rect rgb(255, 240, 230)
        Note over User,Auth: Flow 2: Client Portal (External Clients)
        User->>Portal: Login (client_id, password)
        Portal->>Gateway: POST /v1/client/login
        Gateway->>DB: SELECT * FROM clients<br/>WHERE client_id = ?
        DB-->>Gateway: Client record + password_hash
        Gateway->>Gateway: bcrypt.checkpw(password, hash)
        Gateway->>Gateway: Check failed_login_attempts<br/>Check locked_until
        
        alt Account Locked
            Gateway-->>Portal: {"success": false, "error": "Account locked"}
            Portal-->>User: Show error message
        else Valid Credentials
            Gateway->>Gateway: Generate JWT token<br/>jwt.encode(payload, JWT_SECRET_KEY)
            Gateway->>DB: UPDATE clients SET<br/>failed_login_attempts = 0
            Gateway-->>Portal: {"success": true, "access_token": "eyJ..."}
            Portal->>Portal: Store token in session
            Portal-->>User: Redirect to client dashboard
        end
    end

    rect rgb(240, 255, 240)
        Note over User,Auth: Flow 3: Candidate Portal (Job Seekers)
        User->>Portal: Login (email, password)
        Portal->>Gateway: POST /v1/candidate/login
        Gateway->>DB: SELECT * FROM candidates<br/>WHERE email = ?
        DB-->>Gateway: Candidate record + password_hash
        Gateway->>Gateway: bcrypt.checkpw(password, hash)
        
        alt Valid Credentials
            Gateway->>Gateway: Generate JWT token<br/>jwt.encode(payload, CANDIDATE_JWT_SECRET_KEY)
            Gateway-->>Portal: {"success": true, "token": "eyJ...", "candidate": {...}}
            Portal->>Portal: Store token in session
            Portal-->>User: Redirect to candidate dashboard
        else Invalid Credentials
            Gateway-->>Portal: {"success": false, "error": "Invalid credentials"}
            Portal-->>User: Show error message
        end
    end
```

### Integration Details

**Authentication Methods**:

1. **API Key Authentication** (Primary for API access)
   - Header: `Authorization: Bearer <API_KEY_SECRET>`
   - Validated in Gateway: `validate_api_key()` function
   - Used by: External API clients, service-to-service calls

2. **Client JWT Authentication** (Client Portal)
   - Algorithm: HS256
   - Secret: `JWT_SECRET_KEY` environment variable
   - Expiry: 24 hours
   - Payload: `{"client_id": "TECH001", "company_name": "...", "exp": ...}`

3. **Candidate JWT Authentication** (Candidate Portal)
   - Algorithm: HS256
   - Secret: `CANDIDATE_JWT_SECRET_KEY` environment variable
   - Expiry: 24 hours
   - Payload: `{"candidate_id": 1, "email": "...", "exp": ...}`

**Auth Manager Files**:
- HR Portal: `services/portal/auth_manager.py`
- Client Portal: `services/client_portal/auth_manager.py`
- Candidate Portal: `services/candidate_portal/auth_manager.py`

**Security Features**:
- Password hashing: bcrypt with salt rounds = 12
- 2FA support: TOTP with QR code generation
- Account lockout: 5 failed attempts → 30 minute lock
- Session management: Token-based with expiry
- Password history: Last 5 passwords stored (clients only)
- Backup codes: 10 codes for 2FA recovery

**Endpoints**:
- HR Portal: Uses internal session management (no JWT)
- Client Portal: `POST /v1/client/login`, `POST /v1/client/register`
- Candidate Portal: `POST /v1/candidate/login`, `POST /v1/candidate/register`
- 2FA Setup: `POST /v1/auth/2fa/setup`
- 2FA Verify: `POST /v1/auth/2fa/verify`

---

## Map 4: RL Feedback Loop Integration

**Purpose**: Show reinforcement learning feedback loop for continuous model improvement

### Architecture Diagram

```mermaid
graph LR
    subgraph "1. Prediction Phase"
        A[AI Agent<br/>Semantic Matching] -->|match_score| B[RL Agent<br/>Prediction Model]
        B -->|rl_score, confidence| C[Gateway API]
        C -->|Store prediction| D[(rl_predictions<br/>table)]
    end
    
    subgraph "2. Decision Phase"
        C -->|Return to user| E[HR/Client Portal]
        E -->|Review candidates| F[Human Decision]
    end
    
    subgraph "3. Feedback Phase"
        F -->|Actual outcome| G[Feedback Collection]
        G -->|hired/rejected| H[Gateway API]
        H -->|POST /v1/rl/feedback| I[LangGraph Service]
    end
    
    subgraph "4. Reward Calculation"
        I -->|Calculate reward| J[Reward Function]
        J -->|reward_signal| K[(rl_feedback<br/>table)]
        K -->|Link to prediction| D
    end
    
    subgraph "5. Training Phase"
        K -->|Aggregate feedback| L[Training Data<br/>Preparation]
        L -->|features + rewards| M[(rl_training_data<br/>table)]
        M -->|Batch training| N[Model Retraining]
        N -->|Updated weights| B
    end
    
    subgraph "6. Evaluation Phase"
        N -->|Evaluate performance| O[Model Evaluation]
        O -->|accuracy, precision,<br/>recall, f1_score| P[(rl_model_performance<br/>table)]
        P -->|Monitor metrics| Q[Performance Dashboard]
    end

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style G fill:#ffe1e1
    style J fill:#ffe1e1
    style N fill:#e8f5e9
    style O fill:#e8f5e9
```

### Integration Details

**RL Prediction Flow**:

1. **Initial Matching** (AI Agent)
   - Semantic matching produces base score (0-100)
   - Features extracted: skills_match, experience_match, location_match, values_score

2. **RL Enhancement** (RL Agent)
   - Takes AI match score + features as input
   - Applies learned weights from previous feedback
   - Produces RL score (0-100) and confidence level (0-100)
   - Recommends action: recommend (score > 80), review (50-80), reject (< 50)

3. **Prediction Storage**
   ```sql
   INSERT INTO rl_predictions (
     candidate_id, job_id, rl_score, confidence_level,
     decision_type, features, model_version
   ) VALUES (1, 1, 87.5, 92.0, 'recommend', {...}, 'v1.0.0')
   ```

**Feedback Collection Flow**:

1. **Human Decision**
   - HR/Client reviews candidates
   - Makes hiring decision: hired, rejected, withdrawn, interviewed, shortlisted

2. **Feedback Submission**
   ```json
   POST /v1/rl/feedback
   {
     "prediction_id": 1,
     "feedback_source": "hr",
     "actual_outcome": "hired",
     "feedback_score": 5.0,
     "feedback_notes": "Excellent candidate, perfect match"
   }
   ```

3. **Reward Calculation**
   - Hired + high score → reward = +1.0
   - Hired + low score → reward = +0.5 (lucky match)
   - Rejected + high score → reward = -0.5 (false positive)
   - Rejected + low score → reward = +0.5 (correct rejection)

4. **Feedback Storage**
   ```sql
   INSERT INTO rl_feedback (
     prediction_id, feedback_source, actual_outcome,
     feedback_score, reward_signal
   ) VALUES (1, 'hr', 'hired', 5.0, 1.0)
   ```

**Training Data Preparation**:

1. **Feature Extraction**
   ```json
   {
     "candidate_features": {
       "experience_years": 5,
       "skills_count": 8,
       "values_score": 4.6,
       "education_level": "bachelor"
     },
     "job_features": {
       "experience_required": 5,
       "skills_required": 6,
       "seniority": "senior",
       "department": "engineering"
     },
     "match_score": 87.5,
     "actual_outcome": "hired",
     "reward_value": 1.0
   }
   ```

2. **Batch Creation**
   - Collect 100+ feedback records
   - Group by training_batch identifier
   - Store in `rl_training_data` table

**Model Retraining**:

1. **Trigger Conditions**
   - 100+ new feedback records collected
   - Weekly scheduled retraining
   - Manual trigger by admin

2. **Training Process**
   - Load training data from `rl_training_data`
   - Split: 80% train, 20% validation
   - Train scikit-learn model (RandomForest or GradientBoosting)
   - Validate on holdout set
   - Save new model version

3. **Model Deployment**
   - Update model_version in predictions
   - A/B test: 10% traffic to new model, 90% to old
   - Monitor performance metrics
   - Full rollout if metrics improve

**Performance Evaluation**:

1. **Metrics Calculation**
   ```python
   accuracy = correct_predictions / total_predictions
   precision = true_positives / (true_positives + false_positives)
   recall = true_positives / (true_positives + false_negatives)
   f1_score = 2 * (precision * recall) / (precision + recall)
   average_reward = sum(rewards) / len(rewards)
   ```

2. **Storage**
   ```sql
   INSERT INTO rl_model_performance (
     model_version, accuracy, precision_score, recall_score,
     f1_score, average_reward, total_predictions, evaluation_date
   ) VALUES ('v1.0.0', 0.875, 0.90, 0.85, 0.874, 0.75, 150, NOW())
   ```

**Endpoints**:
- Submit Feedback: `POST /v1/rl/feedback`
- Get Predictions: `GET /v1/rl/predictions/{candidate_id}/{job_id}`
- Model Performance: `GET /v1/rl/model-performance`
- Trigger Training: `POST /v1/rl/train` (admin only)

**Files**:
- RL Routes: `services/gateway/routes/rl_routes.py`
- RL Integration: `services/langgraph/app/rl_integration/`
- Feedback Agent: `services/langgraph/app/rl_integration/feedback_agent.py`

---

## Map 5: End-to-End Candidate Journey

**Purpose**: Show complete candidate lifecycle from application to hiring

### Architecture Diagram

```mermaid
graph TD
    Start([Candidate Visits<br/>Job Portal]) --> Apply[Candidate Applies<br/>POST /v1/candidate/apply]
    
    Apply --> DB1[(Database:<br/>job_applications)]
    Apply --> WF1[Trigger Workflow:<br/>candidate_application]
    
    WF1 --> Email1[Send Email:<br/>Application Received]
    WF1 --> WA1[Send WhatsApp:<br/>Application Confirmation]
    WF1 --> AI1[AI Matching:<br/>Calculate Score]
    
    AI1 --> Cache1[(matching_cache:<br/>Store Score)]
    
    Email1 --> Status1[Update Status:<br/>applied → screened]
    WA1 --> Status1
    
    Status1 --> HR[HR Reviews<br/>Candidates]
    
    HR --> Decision1{Match Score<br/>> 80?}
    
    Decision1 -->|Yes| Shortlist[Shortlist Candidate<br/>POST /v1/candidates/{id}]
    Decision1 -->|No| Review[Manual Review]
    
    Review --> Decision2{HR Decision}
    Decision2 -->|Approve| Shortlist
    Decision2 -->|Reject| Reject1[Reject Candidate]
    
    Shortlist --> DB2[(Database:<br/>Update status)]
    Shortlist --> WF2[Trigger Workflow:<br/>candidate_shortlisted]
    
    WF2 --> Email2[Send Email:<br/>Shortlist Notification]
    WF2 --> WA2[Send WhatsApp:<br/>Next Steps]
    
    Email2 --> Schedule[Schedule Interview<br/>POST /v1/interviews]
    WA2 --> Schedule
    
    Schedule --> DB3[(Database:<br/>interviews table)]
    Schedule --> WF3[Trigger Workflow:<br/>interview_scheduled]
    
    WF3 --> Email3[Send Email:<br/>Interview Details]
    WF3 --> Cal[Calendar Invite]
    
    Email3 --> Interview[Conduct Interview]
    Cal --> Interview
    
    Interview --> Feedback[Submit Feedback<br/>POST /v1/feedback]
    
    Feedback --> DB4[(Database:<br/>feedback table)]
    Feedback --> Values[Calculate Values Score:<br/>BHIV Assessment]
    
    Values --> Decision3{Values Score<br/>> 4.0?}
    
    Decision3 -->|Yes| Offer[Create Offer<br/>POST /v1/offers]
    Decision3 -->|No| Reject2[Reject Candidate]
    
    Offer --> DB5[(Database:<br/>offers table)]
    Offer --> Email4[Send Email:<br/>Offer Letter]
    
    Email4 --> Decision4{Candidate<br/>Accepts?}
    
    Decision4 -->|Yes| Hire[Mark as Hired<br/>Update status]
    Decision4 -->|No| Decline[Mark as Declined]
    
    Hire --> DB6[(Database:<br/>Update status: hired)]
    Hire --> RLFeedback[Submit RL Feedback:<br/>POST /v1/rl/feedback]
    
    RLFeedback --> DB7[(rl_feedback:<br/>reward_signal = +1.0)]
    
    DB7 --> Training[Model Retraining:<br/>Improve Predictions]
    
    Training --> End([Journey Complete])
    
    Reject1 --> RLFeedback2[Submit RL Feedback:<br/>reward_signal = +0.5]
    Reject2 --> RLFeedback2
    Decline --> RLFeedback2
    
    RLFeedback2 --> DB8[(rl_feedback:<br/>Store feedback)]
    DB8 --> Training
    
    style Start fill:#e1f5ff
    style Apply fill:#fff4e1
    style AI1 fill:#ffe1e1
    style Shortlist fill:#e8f5e9
    style Interview fill:#f3e5f5
    style Offer fill:#fff9c4
    style Hire fill:#c8e6c9
    style End fill:#e1f5ff
```

### Journey Steps Breakdown

**Step 1: Application Submission** (2-5 seconds)
- Candidate fills application form on Candidate Portal
- Endpoint: `POST /v1/candidate/apply`
- Creates record in `job_applications` table
- Triggers `candidate_application` workflow
- Sends confirmation email + WhatsApp notification
- AI matching calculates initial score
- Status: `applied`

**Step 2: AI Screening** (0.5-1 second)
- AI Agent performs semantic matching
- Calculates match score (0-100)
- Stores in `matching_cache` table
- RL Agent enhances prediction
- Stores in `rl_predictions` table
- Status: `applied` → `screened`

**Step 3: HR Review** (1-3 days)
- HR views candidates on HR Portal dashboard
- Filters by match score, skills, experience
- Reviews top candidates (score > 80)
- Manual review for borderline candidates (50-80)
- Decision: Shortlist or Reject

**Step 4: Shortlisting** (1-2 seconds)
- HR shortlists candidate
- Endpoint: `PUT /v1/candidates/{id}` (update status)
- Triggers `candidate_shortlisted` workflow
- Sends shortlist notification email + WhatsApp
- Status: `screened` → `shortlisted`

**Step 5: Interview Scheduling** (2-5 seconds)
- HR schedules interview
- Endpoint: `POST /v1/interviews`
- Creates record in `interviews` table
- Triggers `interview_scheduled` workflow
- Sends interview details email + calendar invite
- Status: `shortlisted` → `interviewed`

**Step 6: Interview Conduct** (30-60 minutes)
- Interview conducted (Technical, HR, Behavioral rounds)
- Interviewer takes notes
- Assesses technical skills and cultural fit

**Step 7: Feedback Submission** (2-5 minutes)
- Interviewer submits BHIV values feedback
- Endpoint: `POST /v1/feedback`
- Scores: Integrity, Honesty, Discipline, Hard Work, Gratitude (1-5 each)
- Auto-calculates average_score
- Stores in `feedback` table
- Updates candidate `average_score`

**Step 8: Offer Decision** (1-2 days)
- HR reviews feedback and values scores
- Decision based on: Technical skills + Values alignment
- Threshold: average_score > 4.0 for offer
- If approved → Create offer
- If rejected → Send rejection email

**Step 9: Offer Creation** (2-5 seconds)
- HR creates job offer
- Endpoint: `POST /v1/offers`
- Includes: Salary, start date, terms
- Sends offer letter email
- Status: `interviewed` → `offered`

**Step 10: Offer Response** (3-7 days)
- Candidate reviews offer
- Decision: Accept or Decline
- If accepted → Mark as hired
- If declined → Mark as declined

**Step 11: Hiring Completion** (1-2 seconds)
- Update candidate status to `hired`
- Endpoint: `PUT /v1/candidates/{id}`
- Submit positive RL feedback (reward = +1.0)
- Endpoint: `POST /v1/rl/feedback`
- Stores in `rl_feedback` table
- Status: `offered` → `hired`

**Step 12: RL Model Improvement** (Background process)
- Aggregate feedback from all candidates
- Prepare training data
- Retrain RL model weekly
- Improve future predictions
- Track performance in `rl_model_performance` table

**Total Journey Time**: 7-14 days (typical)

**Database Tables Involved**:
1. `candidates` - Candidate profile
2. `jobs` - Job posting
3. `job_applications` - Application record
4. `matching_cache` - AI match scores
5. `rl_predictions` - RL predictions
6. `interviews` - Interview records
7. `feedback` - BHIV values feedback
8. `offers` - Job offers
9. `rl_feedback` - RL feedback for training
10. `workflows` - Workflow execution tracking
11. `audit_logs` - Complete audit trail

**Notifications Sent**:
1. Application received (Email + WhatsApp)
2. Shortlist notification (Email + WhatsApp)
3. Interview scheduled (Email + Calendar)
4. Offer letter (Email)
5. Rejection notification (Email) - if applicable

**Key Endpoints Used**:
- `POST /v1/candidate/apply` - Submit application
- `POST /v1/match/{job_id}/top` - AI matching
- `PUT /v1/candidates/{id}` - Update status
- `POST /v1/interviews` - Schedule interview
- `POST /v1/feedback` - Submit feedback
- `POST /v1/offers` - Create offer
- `POST /v1/rl/feedback` - Submit RL feedback
- `POST /v1/langgraph/trigger` - Trigger workflows

**Failure Scenarios**:

1. **Application Submission Fails**
   - Cause: Database connection error
   - Impact: Candidate not registered
   - Recovery: Retry submission, check database health

2. **AI Matching Timeout**
   - Cause: Agent service unavailable
   - Impact: Fallback to basic matching (lower accuracy)
   - Recovery: Gateway uses database fallback, logs warning

3. **Notification Delivery Fails**
   - Cause: External service (Gmail, Twilio) error
   - Impact: Candidate misses communication
   - Recovery: Manual follow-up by HR, retry notification

4. **Interview Scheduling Conflict**
   - Cause: Calendar integration error
   - Impact: Double-booked interview slot
   - Recovery: Manual rescheduling, calendar sync

5. **Offer Acceptance Timeout**
   - Cause: Candidate doesn't respond within deadline
   - Impact: Offer expires
   - Recovery: HR extends deadline or moves to next candidate

**Performance Expectations**:
- Application processing: < 5 seconds
- AI matching: < 2 seconds
- Workflow execution: < 10 seconds
- Notification delivery: < 5 seconds
- End-to-end journey: 7-14 days

---

## Integration Summary

### Service Communication Matrix

| From Service | To Service | Protocol | Authentication | Purpose |
|--------------|------------|----------|----------------|---------|
| Gateway | AI Agent | HTTP REST | API Key | Semantic matching |
| Gateway | LangGraph | HTTP REST | API Key | Workflow automation |
| Gateway | MongoDB Atlas | TCP/MongoDB | Password | Data persistence |
| LangGraph | Gmail SMTP | SMTP | App Password | Email notifications |
| LangGraph | Twilio API | HTTPS | Auth Token | WhatsApp notifications |
| LangGraph | Telegram API | HTTPS | Bot Token | Telegram notifications |
| HR Portal | Gateway | HTTP REST | Session | HR operations |
| Client Portal | Gateway | HTTP REST | JWT | Client operations |
| Candidate Portal | Gateway | HTTP REST | JWT | Candidate operations |
| AI Agent | MongoDB Atlas | TCP/MongoDB | Password | Fetch candidates/jobs |
| LangGraph | MongoDB Atlas | TCP/MongoDB | Password | Workflow tracking |

### Service Endpoints Summary

**Gateway Service** (80 endpoints)
- Core API: 5 endpoints
- Job Management: 2 endpoints
- Candidate Management: 5 endpoints
- AI Matching: 2 endpoints
- Assessment & Workflow: 6 endpoints
- Analytics: 3 endpoints
- Client Portal: 2 endpoints
- Security Testing: 12 endpoints
- CSP Management: 4 endpoints
- 2FA: 8 endpoints
- Password Management: 6 endpoints
- Candidate Portal: 5 endpoints
- Authentication: 4 endpoints
- AI Integration: 2 endpoints
- LangGraph Integration: 7 endpoints
- RL + Feedback: 4 endpoints
- Monitoring: 3 endpoints

**AI Agent Service** (6 endpoints)
- `/health` - Health check
- `/match` - Single job matching
- `/batch-match` - Batch job matching
- `/candidate/{id}` - Get candidate details
- `/job/{id}` - Get job details
- `/cache-stats` - Cache statistics

**LangGraph Service** (25 endpoints)
- `/health` - Health check
- `/trigger` - Trigger workflow
- `/status/{workflow_id}` - Get workflow status
- `/workflows` - List workflows
- `/tools/send-notification` - Send notification
- `/rl/*` - RL integration endpoints (8 endpoints)

### Data Flow Patterns

**Pattern 1: Request-Response** (Synchronous)
- Client → Gateway → Database → Gateway → Client
- Used for: CRUD operations, queries, authentication
- Response time: 50-200ms

**Pattern 2: Service-to-Service** (Synchronous)
- Gateway → AI Agent → Gateway
- Used for: AI matching, predictions
- Response time: 500ms-2s

**Pattern 3: Workflow Automation** (Asynchronous)
- Gateway → LangGraph → External Services
- Used for: Notifications, multi-step processes
- Response time: 3-10s

**Pattern 4: Feedback Loop** (Asynchronous)
- User Action → Feedback Collection → Model Training → Improved Predictions
- Used for: RL model improvement
- Cycle time: 1 week

### Integration Best Practices

1. **Authentication**
   - Always use Bearer token authentication
   - Rotate API keys every 90 days
   - Use separate JWT secrets for different portals

2. **Error Handling**
   - Implement fallback mechanisms for service failures
   - Log all errors to audit_logs table
   - Return user-friendly error messages

3. **Performance**
   - Cache AI matching results
   - Use database indexes for fast queries
   - Implement rate limiting to prevent abuse

4. **Monitoring**
   - Track workflow execution in workflows table
   - Monitor service health with /health endpoints
   - Use Prometheus metrics for observability

5. **Security**
   - Validate all inputs
   - Sanitize data before database insertion
   - Use parameterized queries to prevent SQL injection
   - Implement CSP headers for XSS protection

### Environment Variables Required

**Gateway Service**:
```
DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/db
API_KEY_SECRET=<secret>
JWT_SECRET_KEY=<secret>
CANDIDATE_JWT_SECRET_KEY=<secret>
AGENT_SERVICE_URL=http://localhost:8001
LANGGRAPH_SERVICE_URL=http://localhost:8003
```

**AI Agent Service**:
```
DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/db
API_KEY_SECRET=<secret>
MODEL_PATH=/models/sentence-transformer
```

**LangGraph Service**:
```
DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/db
API_KEY_SECRET=<secret>
GMAIL_USER=<email>
GMAIL_APP_PASSWORD=<password>
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TELEGRAM_BOT_TOKEN=<token>
```

**Portal Services**:
```
GATEWAY_SERVICE_URL=http://localhost:8000
API_KEY_SECRET=<secret>
```

### Deployment Architecture

```
Production Environment (Render Platform)
├── Gateway Service (bhiv-hr-gateway-ltg0.onrender.com)
├── AI Agent Service (bhiv-hr-agent-nhgg.onrender.com)
├── LangGraph Service (bhiv-hr-langgraph.onrender.com)
├── HR Portal (bhiv-hr-portal-u670.onrender.com)
├── Client Portal (bhiv-hr-client-portal-3iod.onrender.com)
├── Candidate Portal (bhiv-hr-candidate-portal-abe6.onrender.com)
└── MongoDB Atlas Database (MongoDB Atlas instance)
```

**Network Configuration**:
- All services deployed in Oregon, US West region
- Internal service communication via Render private network
- External access via HTTPS with SSL/TLS
- Database accessible only from Render services

**Scaling Strategy**:
- Gateway: Auto-scale based on CPU (50-80% threshold)
- AI Agent: Manual scale for model inference
- LangGraph: Auto-scale based on workflow queue
- Portals: Static deployment (low traffic)
- Database: Vertical scaling (increase resources)

---

## Integration Testing Checklist

### Gateway ↔ AI Agent
- [ ] `/match` endpoint returns valid scores
- [ ] Fallback mechanism works when Agent unavailable
- [ ] Batch matching processes multiple jobs
- [ ] Cache stores results correctly
- [ ] Timeout handling (60s limit)

### Gateway ↔ LangGraph
- [ ] Workflow trigger creates workflow record
- [ ] Status updates tracked in workflows table
- [ ] Notifications sent successfully (Email, WhatsApp, Telegram)
- [ ] Error handling for failed notifications
- [ ] Workflow completion logged to audit_logs

### Gateway ↔ Database
- [ ] All CRUD operations work correctly
- [ ] Foreign key constraints enforced
- [ ] Triggers update timestamps automatically
- [ ] Audit logs capture all changes
- [ ] Indexes improve query performance

### Portal ↔ Gateway
- [ ] Authentication works for all three portals
- [ ] JWT tokens validated correctly
- [ ] Session management prevents unauthorized access
- [ ] 2FA flow works end-to-end
- [ ] API responses formatted correctly for UI

### RL Feedback Loop
- [ ] Predictions stored with correct features
- [ ] Feedback submission calculates reward correctly
- [ ] Training data prepared in correct format
- [ ] Model retraining improves performance
- [ ] Performance metrics tracked over time

---

**End of Integration Maps Documentation**

