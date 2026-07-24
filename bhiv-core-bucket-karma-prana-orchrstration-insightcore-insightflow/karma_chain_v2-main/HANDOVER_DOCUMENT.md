# Karma Tracker System - Final Handover Document

## System Overview

The Karma Tracker is a comprehensive karma tracking system called "KarmaChain v2 (Dual-Ledger)" built with FastAPI and MongoDB. It implements a dual-ledger approach tracking both positive (Punya) and negative (Paap) karmic actions based on Vedic principles. The system provides a complete karma lifecycle management system with progressive atonement mechanisms.

### Core Architecture
- **Framework**: FastAPI (Python 3.11)
- **Database**: MongoDB (with collections for users, transactions, karma events, etc.)
- **Architecture**: Modular, portable system with versioned APIs
- **Deployment**: Docker containerized with MongoDB and mongo-express

## Previous Owner & New Owner
- **Previous Owner**: Siddhesh (Developer)
- **New Owner**: Task Bank / Master Chat (BHIV)

---

## Implemented Features and Modules

### 1. Core Karma Engine
- **Dual-Ledger System**: Tracks both positive (Punya) and negative (Paap) karmic actions
- **Token System**: DharmaPoints, SevaPoints, PunyaTokens, and PaapTokens (minor, medium, maha)
- **Vedic Classification**: Four-tier karma classification (Minor, Medium, Major, Maha)
- **Progressive Punishment**: For cheating with escalating penalties
- **Karma Decay**: Configurable decay rates for different token types

### 2. Atonement System
- **Atonement Plans**: Personalized plans based on action severity
- **Atonement Types**: Jap (mantra repetition), Tap (fasting), Bhakti (devotion), Daan (charity)
- **File Upload Support**: Proof submission with validation and storage
- **Atonement Validation**: Verification of atonement completion

### 3. Karma Lifecycle Engine
- **Complete Lifecycle**: Birth → Life → Death → Rebirth simulation
- **Prarabdha Counter**: Tracks current life karma experience
- **Death Threshold**: Automatic death event when Prarabdha drops below -100
- **Loka Assignment**: Based on net karma (Swarga, Mrityuloka, Antarloka, Naraka)
- **Karma Inheritance**: Sanchita karma carries over to next life (20% positive, 50% negative)

### 4. Rnanubandhan (Karmic Debt) System
- **Debt Relationships**: Tracks karmic debts between users
- **Severity Levels**: Minor, medium, major debt classifications
- **Repayment System**: Methods to repay karmic debts
- **Debt Transfer**: Ability to transfer debts to other users

### 5. Agami Karma Prediction
- **Predictive Analysis**: Predicts future karma based on current patterns
- **Behavioral Modeling**: Models Sanchita (accumulated) → Prarabdha (experienced) → Agami (future) flow

### 6. Dridha/Adridha Analysis
- **Stability Assessment**: Analyzes stable (Dridha) vs. volatile (Adridha) karma patterns
- **Guidance Effectiveness**: Determines guidance effectiveness based on karma stability
- **Personalized Recommendations**: Based on karma patterns

### 7. Behavioral State Normalization
- **Multi-Module Integration**: Unifies behavioral inputs from different modules
- **Standardized Signals**: Converts multi-module inputs to standardized karmic signals

### 8. Karmic Feedback Engine
- **Net Influence Calculation**: Computes net karmic influence and publishes telemetry
- **Real-time Feedback**: Provides immediate feedback on karmic impact

### 9. Karmic Analytics
- **Interpretable Analytics**: Provides analytics for InsightFlow dashboards
- **Trend Analysis**: Tracks engagement metrics and behavioral trends

### 10. STP Bridge Integration
- **Secure Telemetry**: Forwarding to external systems like Unreal Engine
- **External System Integration**: Secure API endpoints for cross-module integration

### 11. Event Bus System
- **Real-time Broadcasting**: Broadcasting of karmic events to connected clients
- **Event Messaging**: Real-time event broadcasting and messaging

### 12. Q-Learning Integration
- **Adaptive Learning**: Adaptive karma prediction and atonement recommendations
- **Optimization**: Optimizes karma calculations using reinforcement learning

### 13. Unified Event Gateway
- **Single Endpoint**: All karma operations accessible through `/v1/karma/event`
- **File Upload Support**: File uploads with validation and storage
- **Event Audit Trail**: Complete event logging and lifecycle tracking

### 14. API Endpoints
- **Versioned APIs**: `/v1/karma/` endpoints for all operations
- **Traditional Endpoints**: Separate endpoints for specific operations
- **Unified Gateway**: Single endpoint for all operations with file support

---

## Non-Implemented Features

### 1. Planned but Not Implemented
- **User and Admin Routes**: The system has commented imports for user and admin modules that don't exist yet
- **Advanced Game Integration**: While game module scoring exists, full gaming integration features are not fully developed
- **Advanced Finance Integration**: Finance module hooks exist but may not be fully connected to external financial systems
- **InsightFlow Advanced Features**: Some advanced analytics features may not be fully implemented
- **Gurukul Advanced Features**: Some educational module features may not be fully implemented

### 2. Future Enhancements
- **Enhanced Security Features**: Additional security measures beyond current implementation
- **Advanced Multi-tenant Support**: More sophisticated user isolation features
- **Advanced Reporting**: More comprehensive reporting features beyond current analytics
- **Mobile API Extensions**: Additional endpoints optimized for mobile clients
- **Advanced ML Integration**: More sophisticated machine learning features beyond current Q-learning

---

## Key Files, Folders and Scripts

### Root Directory Files
- **main.py**: FastAPI application entry point with all route inclusions
- **models.py**: Pydantic models for request/response validation
- **database.py**: MongoDB connection and collection definitions
- **config.py**: Application configuration and karma factors
- **requirements.txt**: Python dependencies
- **Dockerfile**: Container build instructions
- **docker-compose.yml**: Multi-container deployment configuration
- **.env**: Environment variables (not committed to version control)
- **.env.example**: Example environment variables file

### Routes Directory
- **routes/karma.py**: Main karma API routes (log-action, submit-atonement, get-karma-profile)
- **routes/agami.py**: Agami karma prediction routes
- **routes/analytics.py**: Karmic analytics routes
- **routes/balance.py**: Wallet operations routes
- **routes/feedback.py**: Karmic feedback engine routes
- **routes/normalization.py**: Behavioral state normalization routes
- **routes/policy.py**: Policy-related routes
- **routes/redeem.py**: Token redemption routes
- **routes/rnanubandhan.py**: Rnanubandhan debt relationship routes
- **routes/v1/karma/**: Versioned karma routes
  - **event.py**: Unified event gateway
  - **lifecycle.py**: Karma lifecycle engine routes
  - **log_action.py**: Action logging routes
  - **appeal.py**: Appeal submission routes
  - **atonement.py**: Atonement submission routes
  - **death.py**: Death event routes
  - **stats.py**: User statistics routes
  - **__init__.py**: Route initialization

### Utils Directory
- **utils/karma_engine.py**: Core karma evaluation and guidance logic
- **utils/karma_lifecycle.py**: Karma lifecycle engine implementation
- **utils/karmic_predictor.py**: Agami karma prediction and Dridha/Adridha analysis
- **utils/karmic_analytics.py**: Analytics processing utilities
- **utils/karma_schema.py**: Karma schema and calculation utilities
- **utils/atonement.py**: Atonement validation and processing
- **utils/loka.py**: Loka assignment and karma calculation
- **utils/merit.py**: Merit score calculation and role determination
- **utils/paap.py**: Paap token generation and management
- **utils/qlearning.py**: Q-learning implementation for karma optimization
- **utils/tokens.py**: Token management and decay logic
- **utils/transactions.py**: Transaction processing utilities
- **utils/utils_user.py**: User utility functions
- **utils/rnanubandhan.py**: Rnanubandhan relationship management
- **utils/rnanubandhan_net.py**: Rnanubandhan network utilities
- **utils/stp_bridge.py**: STP bridge implementation
- **utils/event_bus.py**: Event bus system implementation
- **utils/unreal_broadcast.py**: Unreal Engine broadcast utilities
- **utils/audit_enhancer.py**: Audit enhancement utilities
- **utils/agami_predictor.py**: Agami prediction utilities
- **utils/audit_scheduler.py**: Audit scheduling utilities
- **utils/analytics_scheduler.py**: Analytics scheduling utilities

### Handover Directory
- **handover/data_module/api_notes.md**: API usage notes for analytics team
- **handover/data_module/data_schema.json**: Data schema definitions
- **handover/data_module/sample_responses/**: Sample API responses
- **handover/interface_module/api_map.md**: API mapping documentation
- **handover/interface_module/event_payloads.md**: Event payload specifications
- **handover/interface_module/response_codes.md**: Response code definitions
- **handover/system_module/Dockerfile**: Docker configuration for system team
- **handover/system_module/deployment_notes.md**: Deployment notes
- **handover/system_module/docker-compose.yml**: Docker Compose configuration
- **handover/system_module/env.example**: Environment variable examples

### Docs Directory
- **docs/agami_karma_predictor.md**: Agami karma predictor documentation
- **docs/behavioral_normalization.md**: Behavioral normalization documentation
- **docs/event_bus_implementation.md**: Event bus implementation guide
- **docs/feedback_engine_guide.md**: Feedback engine guide
- **docs/karma_api_endpoints.md**: Karma API endpoints documentation
- **docs/karma_engine.md**: Karma engine documentation
- **docs/karma_lifecycle_implementation.md**: Karma lifecycle implementation guide
- **docs/karmachain_v2.md**: KarmaChain v2 overview
- **docs/karmic_analytics_api.md**: Karmic analytics API documentation
- **docs/rnanubandhan_api.md**: Rnanubandhan API documentation
- **docs/rnanubandhan_implementation.md**: Rnanubandhan implementation guide
- **docs/stp_bridge_security_upgrade.md**: STP bridge security documentation
- **docs/unified_event_api.md**: Unified event API documentation
- **docs/HANDOVER_GUIDE.md**: Comprehensive handover guide
- **docs/API_REFERENCE.md**: API reference documentation

### Scripts Directory
- **scripts/api_structure_test.py**: API structure testing script
- **scripts/demo_agami_predictor.py**: Agami predictor demonstration
- **scripts/demo_audit_scheduler.py**: Audit scheduler demonstration
- **scripts/demo_cli.py**: CLI demonstration script
- **scripts/demo_complete_system.py**: Complete system demonstration
- **scripts/demo_event_bus.py**: Event bus demonstration
- **scripts/demo_karmic_analytics.py**: Karmic analytics demonstration
- **scripts/demo_normalization.py**: Normalization demonstration
- **scripts/demo_rnanubandhan.py**: Rnanubandhan demonstration
- **scripts/demo_ui.html**: Demo UI HTML file
- **scripts/export_to_core.bat**: Windows export script
- **scripts/export_to_core.sh**: Linux/Mac export script
- **scripts/final_verification.py**: Final verification script
- **scripts/finance_gurukul_stubs.py**: Finance and Gurukul stubs
- **scripts/generate_sample_logs.py**: Sample log generation
- **scripts/init_karma_events.py**: Karma events initialization
- **scripts/insightflow_stub.py**: InsightFlow stub
- **scripts/lifecycle_simulation.py**: Lifecycle simulation script
- **scripts/run_local.sh**: Local run script
- **scripts/simple_stp_test.py**: Simple STP test
- **scripts/simple_verify.py**: Simple verification script
- **scripts/test_audit_integration.py**: Audit integration test
- **scripts/test_feedback_api.py**: Feedback API test
- **scripts/test_flow.py**: Flow test
- **scripts/test_nonce_detection.py**: Nonce detection test
- **scripts/test_stp_bridge_logging.py**: STP bridge logging test
- **scripts/test_stp_fixes.py**: STP fixes test
- **scripts/unreal_client_stub.py**: Unreal client stub
- **scripts/unreal_simulation.py**: Unreal simulation
- **scripts/validate_handover.py**: Handover validation script
- **scripts/verify_endpoints.py**: Endpoint verification script

### Tests Directory
- **tests/test_advanced_karmic_features.py**: Advanced karmic features tests
- **tests/test_agami_predictor.py**: Agami predictor tests
- **tests/test_audit_enhancer.py**: Audit enhancer tests
- **tests/test_event_bus.py**: Event bus tests
- **tests/test_feedback_engine.py**: Feedback engine tests
- **tests/test_karma_api.py**: Karma API tests
- **tests/test_karma_cycle_simulation.py**: Karma cycle simulation tests
- **tests/test_karma_engine.py**: Karma engine tests
- **tests/test_karma_lifecycle.py**: Karma lifecycle tests
- **tests/test_karma_schema.py**: Karma schema tests
- **tests/test_karmic_analytics.py**: Karmic analytics tests
- **tests/test_karmic_predictor.py**: Karmic predictor tests
- **tests/test_lifecycle_api.py**: Lifecycle API tests
- **tests/test_normalization.py**: Normalization tests
- **tests/test_rnanubandhan.py**: Rnanubandhan tests
- **tests/test_rnanubandhan_net.py**: Rnanubandhan network tests
- **tests/test_stp_bridge.py**: STP bridge tests
- **tests/integration_demo.py**: Integration demo tests
- **tests/stress_test.py**: Stress tests
- **tests/context_weights.json**: Context weights for testing

### Data Directory
- **data/karma_actions_dataset.json**: Sample karma actions dataset

### Schemas Directory
- **schemas/event_bus.json**: Event bus schema
- **schemas/state_schema.json**: State schema
- **schemas/token_schema.json**: Token schema

### Other Important Files
- **collection_test.py**: Database collection test file
- **context_weights.json**: Context weights configuration
- **observability.py**: Observability configuration
- **system_manifest.json**: System manifest
- **validation.py**: Input validation utilities
- **validation_middleware.py**: Validation middleware
- **UNREAL_ENGINE_INTEGRATION_PLAN.md**: Unreal Engine integration plan
- **DAY4_SUMMARY.md**: Day 4 development summary
- **DELIVERABLES_SUMMARY.md**: Deliverables summary
- **DOCKER_SETUP.md**: Docker setup documentation

---

## How to Run and Test the System

### Prerequisites
- Python 3.8+
- MongoDB 6.0+
- Docker and Docker Compose (recommended)
- Git

### Local Development Setup

#### Option 1: Using Docker (Recommended)
1. Clone the repository:
```bash
git clone <repository-url>
cd karma-tracker
```

2. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
Edit the `.env` file with your MongoDB connection details and other configurations.

3. Run the application using Docker Compose:
```bash
docker-compose up --build
```

4. The application will be available at `http://localhost:8000`
5. MongoDB will be available at `http://localhost:27017`
6. MongoDB Express UI will be available at `http://localhost:8081`

#### Option 2: Local Installation
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up MongoDB:
   - Install MongoDB locally or use MongoDB Atlas
   - Update your `.env` file with the correct MongoDB URI

3. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Documentation
- Interactive API documentation available at `http://localhost:8000/docs`
- Alternative documentation at `http://localhost:8000/redoc`

### Testing the System

#### Unit Tests
Run all unit tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=.
```

Run specific test files:
```bash
pytest tests/test_karma_engine.py
```

#### Integration Tests
Run integration tests:
```bash
pytest tests/integration_demo.py
```

#### Stress Tests
Run stress tests for performance evaluation:
```bash
pytest tests/stress_test.py
```

#### API Tests
Test specific API endpoints:
```bash
pytest tests/test_karma_api.py
```

### Key Endpoints to Test

#### Traditional Endpoints
1. **Log Action**: `POST /api/v1/log-action/`
   ```json
   {
     "user_id": "test_user_123",
     "action": "helping_peers",
     "role": "learner",
     "note": "Helped a colleague debug code"
   }
   ```

2. **Get Karma Profile**: `GET /api/v1/karma/{user_id}`
   ```bash
   curl http://localhost:8000/api/v1/karma/test_user_123
   ```

3. **Submit Atonement**: `POST /api/v1/submit-atonement/`
   ```json
   {
     "user_id": "test_user_123",
     "plan_id": "atonement_plan_1",
     "atonement_type": "Daan",
     "amount": 100.0,
     "proof_text": "Donated to charity"
   }
   ```

#### Unified Event Gateway (Recommended)
1. **Life Event**: `POST /v1/karma/event/`
   ```json
   {
     "type": "life_event",
     "data": {
       "user_id": "test_user_123",
       "action": "helping_peers",
       "role": "learner",
       "note": "Helped a colleague"
     }
   }
   ```

2. **Atonement Event**: `POST /v1/karma/event/`
   ```json
   {
     "type": "atonement",
     "data": {
       "user_id": "test_user_123",
       "plan_id": "atonement_plan_1",
       "atonement_type": "Daan",
       "amount": 100.0,
       "proof_text": "Donated to charity"
     }
   }
   ```

3. **File Upload Atonement**: `POST /v1/karma/event/with-file`
   - Form data with fields: `event_type`, `user_id`, `plan_id`, `atonement_type`, `amount`, `proof_text`, `proof_file`

#### Rnanubandhan Endpoints
1. **Create Debt**: `POST /api/v1/rnanubandhan/create-debt`
   ```json
   {
     "debtor_id": "user123",
     "receiver_id": "user456",
     "action_type": "harm_others",
     "severity": "medium",
     "amount": 50.0,
     "description": "Caused emotional harm"
   }
   ```

2. **Repay Debt**: `POST /api/v1/rnanubandhan/repay-debt`
   ```json
   {
     "relationship_id": "507f1f77bcf86cd799439011",
     "amount": 25.0,
     "repayment_method": "atonement"
   }
   ```

#### Karma Lifecycle Endpoints
1. **Check Prarabdha**: `GET /api/v1/karma/lifecycle/prarabdha/{user_id}`
2. **Update Prarabdha**: `POST /api/v1/karma/lifecycle/prarabdha/update`
3. **Check Death Threshold**: `POST /api/v1/karma/lifecycle/death/check`
4. **Process Death**: `POST /api/v1/karma/lifecycle/death/process`
5. **Process Rebirth**: `POST /api/v1/karma/lifecycle/rebirth/process`
6. **Run Simulation**: `POST /api/v1/karma/lifecycle/simulate`

### Health Check
Check the system health:
```bash
curl http://localhost:8000/health
```

### Sample Test Scenarios
1. Create a user by logging an action
2. Verify the user's karma profile
3. Test atonement submission
4. Test file upload for atonement
5. Test Rnanubandhan debt creation and repayment
6. Test karma lifecycle events
7. Test unified event gateway for all operations

---

## Known Risks and Edge Cases

### 1. Security Risks
- **MongoDB Authentication**: Default credentials in docker-compose.yml may be insecure for production
- **File Upload Validation**: File size and type validation may have bypasses if not properly configured
- **Input Sanitization**: User inputs should be thoroughly validated to prevent injection attacks
- **API Rate Limiting**: No built-in rate limiting may expose the system to DoS attacks
- **Environment Variables**: Sensitive configuration data should be properly secured

### 2. Data Integrity Risks
- **Concurrent Updates**: Multiple simultaneous updates to user karma could cause race conditions
- **MongoDB Consistency**: Lack of explicit transaction handling for complex multi-document operations
- **Data Loss**: Improper backup strategies could lead to data loss during system failures
- **Event Audit Trail**: Incomplete logging of events could affect traceability and debugging

### 3. Performance Risks
- **Database Queries**: Complex aggregation queries may cause performance bottlenecks with large datasets
- **Memory Usage**: Large file uploads and processing may cause memory issues
- **API Response Times**: Complex karma calculations may result in slow API responses
- **Database Indexing**: Missing indexes could cause slow query performance

### 4. Business Logic Edge Cases
- **Negative Karma Handling**: Very large negative karma values could cause unexpected behavior
- **Decimal Precision**: Floating-point arithmetic in karma calculations may cause precision issues
- **Zero Values**: Division by zero or operations with zero values may cause errors
- **Large User IDs**: Very long user IDs could exceed database field limits
- **Time Zone Issues**: Timestamp handling across different time zones may cause inconsistencies

### 5. System Integration Risks
- **Unreal Engine Integration**: WebSocket connection failures could affect real-time updates
- **External API Dependencies**: Dependencies on external services could cause failures
- **STP Bridge Failures**: Secure telemetry forwarding failures could impact external systems
- **Event Bus Disconnections**: Disconnected event buses could cause missed events

### 6. Lifecycle Edge Cases
- **Death Threshold**: Edge cases when Prarabdha karma is exactly at the death threshold
- **Rebirth Counters**: Integer overflow in rebirth counters with very high values
- **Inheritance Calculations**: Edge cases when calculating karma inheritance with extreme values
- **Loka Assignments**: Edge cases when karma values are exactly at loka boundaries

### 7. Atonement Edge Cases
- **Atonement Validation**: Edge cases in validating atonement proofs with unusual formats
- **File Upload Failures**: Network issues during file uploads could cause incomplete submissions
- **Atonement Multipliers**: Invalid multipliers in atonement calculations could cause errors
- **Proof Verification**: Automated proof verification may have false positives/negatives

### 8. Rnanubandhan Edge Cases
- **Circular Debt**: Multiple users creating debt relationships that form circular dependencies
- **Negative Amounts**: Negative debt amounts could cause calculation errors
- **Self-Debt**: Users creating debt relationships with themselves should be prevented
- **Transfer Validation**: Transferring debts to users who don't exist could cause issues

### 9. Configuration Risks
- **Environment Variables**: Missing or incorrect environment variables could cause system failures
- **Database Connection**: Connection timeouts or failures could cause service unavailability
- **Q-Learning Parameters**: Improper hyperparameter settings could affect learning effectiveness
- **Token Attributes**: Invalid token attribute configurations could cause calculation errors

### 10. Operational Risks
- **Event Retention**: Long-term event retention without cleanup could cause storage issues
- **Backup Strategies**: Lack of proper backup strategies could cause permanent data loss
- **Monitoring**: Insufficient monitoring could lead to undetected system issues
- **Maintenance Windows**: Lack of scheduled maintenance could cause system degradation

---

## FAQ for Future Maintainers

### Q1: What is the difference between the dual-ledger system and traditional karma tracking?
**A**: The dual-ledger system tracks both positive (PunyaTokens, SevaPoints, DharmaPoints) and negative (PaapTokens) karmic actions separately. This allows for more nuanced karma calculations and progressive atonement mechanisms, as opposed to simple positive-only tracking.

### Q2: How do I add new karma actions to the system?
**A**: 
1. Add the action to the `ACTIONS` list in `config.py`
2. Define the reward mapping in `REWARD_MAP` in `config.py`
3. Add to the appropriate categories in `PURUSHARTHA` in `utils/karma_engine.py`
4. If it's a negative action, add it to `PAAP_CLASSES` in `config.py`

### Q3: How does the progressive punishment system work for cheating?
**A**: The system tracks cheating incidents and applies escalating penalties based on the number of offenses:
- 1st offense: -2 DharmaPoints
- 2nd offense: -5 DharmaPoints
- 3rd offense: -10 DharmaPoints
- 4th offense: -20 DharmaPoints
- 5th offense: -40 DharmaPoints
- Repeat offenders: -100 DharmaPoints
The cheat count resets after 30 days of no cheating incidents.

### Q4: What are the different karma types and their purposes?
**A**:
- **DharmaPoints**: Represent righteous actions and moral virtue
- **SevaPoints**: Represent selfless service to others
- **PunyaTokens**: Represent significant spiritual merit
- **PaapTokens**: Negative karma tokens (minor, medium, maha)
- **DridhaKarma**: Stable karma that's harder to change
- **AdridhaKarma**: Volatile karma that's easier to change
- **SanchitaKarma**: Accumulated karma from all lifetimes
- **PrarabdhaKarma**: Karma currently being experienced in this life
- **Rnanubandhan**: Karmic debts owed to other users

### Q5: How do I modify the atonement requirements?
**A**: Modify the `PRAYASCHITTA_MAP` in `config.py` to change the required amounts for each atonement type (Jap, Tap, Bhakti, Daan) based on Paap severity (minor, medium, maha).

### Q6: What happens when a user reaches the death threshold?
**A**: When a user's Prarabdha karma drops below -100:
1. Their loka (realm) is determined based on net karma
2. A death event is recorded with inheritance calculations
3. Karma inheritance is calculated (20% positive, 50% negative carries over)
4. The user is reborn with a new ID and inherited karma

### Q7: How do I update loka assignment thresholds?
**A**: Modify the `LOKA_THRESHOLDS` in `config.py` to adjust the karma ranges for each loka (Swarga, Mrityuloka, Antarloka, Naraka).

### Q8: What is the unified event gateway and why should I use it?
**A**: The unified event gateway (`/v1/karma/event/`) is a single endpoint that routes different event types to appropriate internal endpoints. It provides:
- Centralized event logging and audit trail
- Consistent error handling
- Simplified integration for external systems
- Single point of monitoring and debugging

### Q9: How do I handle file uploads for atonement proofs?
**A**: File uploads are handled through the unified event gateway with the `/v1/karma/event/with-file` endpoint. The system validates:
- File type (text, PDF, images, documents)
- File size (max 1MB)
- Content type
- Proper cleanup of temporary files

### Q10: What are Rnanubandhan relationships and how do they work?
**A**: Rnanubandhan represents karmic debt relationships between users:
- Debtor owes karma debt to receiver
- Can be repaid through atonement or service
- Can be transferred to other users
- Severity levels: minor, medium, major
- Tracked in the `rnanubandhan_relationships` MongoDB collection

### Q11: How do I troubleshoot common API issues?
**A**:
- Check the `karma_events` collection for event logs and error messages
- Verify MongoDB connectivity and authentication
- Review application logs for error details
- Use the health check endpoint (`/health`) to verify system status
- Check the unified event gateway logs for routing issues

### Q12: What are the Purushartha categories and how do they affect karma?
**A**: The four Purushartha categories are:
- **Dharma**: Righteousness, duty, and moral virtue
- **Artha**: Wealth, prosperity, and economic values
- **Kama**: Desire, pleasure, and emotional fulfillment
- **Moksha**: Liberation, spiritual freedom, and enlightenment
These categories influence karma scoring and guidance recommendations based on their modifiers in the configuration.

### Q13: How do I scale the system for more users?
**A**:
- Increase MongoDB connection pool size in `database.py`
- Add more workers in the Dockerfile CMD
- Implement proper indexing in MongoDB
- Consider sharding for very large datasets
- Use Redis for caching frequently accessed data
- Implement load balancing for multiple instances

### Q14: How does the Q-learning integration work?
**A**: The system implements Q-learning to optimize karma calculations and recommendations:
- Learns from user actions and outcomes
- Adjusts karma rewards based on effectiveness
- Improves atonement recommendations over time
- Configurable hyperparameters (alpha, gamma, epsilon) in `config.py`

### Q15: What are Dridha and Adridha karma, and why do they matter?
**A**: 
- **Dridha Karma**: Stable karma that represents consistent behavior patterns; changes slowly and has long-lasting effects
- **Adridha Karma**: Volatile karma that represents inconsistent behavior patterns; changes quickly and has temporary effects
These concepts help determine how effective corrective guidance will be for different users.

### Q16: How do I add new modules to the system?
**A**: To add new modules:
1. Create a new route file in the `routes` directory
2. Define the API endpoints with proper request/response models
3. Implement the business logic in a new utility file in `utils`
4. Register the routes in `main.py`
5. Add proper error handling and logging
6. Create tests for the new functionality

### Q17: What is the Agami karma prediction system?
**A**: Agami karma refers to future karma based on current patterns. The prediction system:
- Analyzes current karma trends
- Predicts future karma states based on current patterns
- Models the flow from Sanchita (accumulated) → Prarabdha (experienced) → Agami (future)
- Provides guidance to improve future karma outcomes

### Q18: How do I backup and restore the system?
**A**:
- Use MongoDB's built-in backup tools: `mongodump` and `mongorestore`
- Backup the `karmachain` database regularly
- Store backups in the `/backups` directory as configured in docker-compose.yml
- Test restore procedures regularly
- Consider automated backup scheduling

---

## Ownership Transfer and Closure

### Project Ownership
- **Previous Owner**: Siddhesh (Developer)
- **New Owner**: Task Bank / Master Chat (BHIV)
- **Transfer Date**: January 5, 2026
- **Transfer Status**: Complete

### System Responsibility Transfer
- **Codebase**: All code, documentation, and configurations are transferred
- **Knowledge**: All development knowledge and system insights are documented
- **Access**: All system access credentials and deployment information provided
- **Maintenance**: Future maintenance responsibility transferred to new owner

### Closure Confirmation
- **Code Completeness**: All implemented features are functional
- **Documentation**: Comprehensive documentation provided
- **Testing**: All tests pass and system is verified as operational
- **Security**: No known security vulnerabilities (though review is recommended)
- **Backup**: Database and configuration backup procedures documented

### Security and Confidentiality
- All concepts, logic, schemas, and system designs remain confidential and proprietary
- No reuse, replication, derivative work, or external application of this knowledge is permitted
- All concepts remain under BHIV control and ownership
- Previous developer (Siddhesh) has no retention of system knowledge for external use

### Final Verification
- All handover requirements have been met
- System is fully operational and documented
- No private copies remain outside BHIV-controlled systems
- All deliverables completed as per assignment requirements

### Next Steps for New Owner
1. Review all documentation thoroughly
2. Set up proper monitoring and alerting
3. Implement additional security measures as needed
4. Plan for ongoing maintenance and feature development
5. Establish backup and disaster recovery procedures
6. Consider performance optimization for production use

---

**Handover Complete**: This marks the formal completion of the Karma Tracker system handover. All responsibilities, code, and knowledge have been transferred from Siddhesh to Task Bank / Master Chat (BHIV). No follow-up support is expected from the previous owner.