# 🧪 BHIV HR Platform - Testing Suite

**Comprehensive testing for all services with multiple test levels**

## 🚀 Quick Start

### Run Main Comprehensive Tests
```bash
# From project root directory
python tests/comprehensive_endpoint_tests.py
```

### Install Dependencies
```bash
pip install -r tests/requirements.txt
```

### Test Options
- **Comprehensive Test**: `python tests/comprehensive_endpoint_tests.py` - Full endpoint coverage with detailed validation
- **Quick Smoke Test**: `python tests/quick_smoke_tests.py` - Critical endpoints only (removed)
- **Legacy Test**: `python tests/test_complete_112_endpoints.py` - Original 112 endpoint test (deprecated)

### Authentication & MongoDB Testing
- **Authentication Tests**: `python test_authentication_changes.py` - Test all authentication flows (candidate, recruiter, client)
- **MongoDB Scripts Test**: `python test_mongodb_scripts.py` - Test MongoDB schema management scripts
- **MongoDB Schema Verification**: `python services/gateway/verify_mongodb_schema.py` - Verify MongoDB collections and fields
- **MongoDB Index Creation**: `python services/gateway/create_mongodb_indexes.py` - Create recommended indexes
- **MongoDB Schema Migration**: `python services/gateway/migrate_mongodb_schema.py` - Migrate existing data

## 📊 What Gets Tested

### 🏗️ All 6 Services (108 Endpoints)
- **API Gateway**: 77 endpoints
- **AI Agent**: 6 endpoints  
- **LangGraph**: 25 endpoints
- **HR Portal**: Web interface accessibility
- **Client Portal**: Web interface accessibility
- **Candidate Portal**: Web interface accessibility

### 🔄 Complete Business Workflow
1. **Service Health Checks** - All services operational
2. **Core API Endpoints** - Basic functionality
3. **Authentication & Security** - 2FA, passwords, validation
4. **Business Logic Workflow** - Job → Candidate → Interview → Feedback
5. **AI Matching Engine** - Semantic matching and analysis
6. **LangGraph Workflows** - Automation and notifications
7. **Service Integration** - Cross-service communication
8. **Portal Accessibility** - Web interface availability

## 🎯 Test Categories

### Phase 1: Service Health (6 tests)
- Gateway health and root endpoints
- Agent service health checks
- LangGraph service health checks

### Phase 2: Core API (6 tests)
- OpenAPI schema validation
- Database connectivity
- Metrics and monitoring
- System diagnostics

### Phase 3: Authentication & Security (15 tests)
- Rate limiting and security headers
- Input validation and sanitization
- Email and phone validation
- 2FA setup, verification, and QR codes
- Password validation and generation
- Security policy enforcement

### Phase 4: Business Workflow (13 tests)
- Job creation and listing
- Client registration and authentication
- Candidate registration and login
- Bulk candidate upload
- Interview scheduling
- Feedback submission
- Complete end-to-end workflow

### Phase 5: AI Matching (6 tests)
- Agent database connectivity
- AI-powered candidate matching
- Batch matching for multiple jobs
- Detailed candidate analysis
- Gateway AI integration
- Performance validation

### Phase 6: LangGraph Workflows (5 tests)
- Workflow creation and management
- Status tracking and monitoring
- Multi-channel notifications
- Integration testing
- Statistics and analytics

### Phase 7: Service Integration (2 tests)
- Gateway ↔ Agent communication
- Gateway ↔ LangGraph communication
- Cross-service data consistency

### Phase 8: Portal Accessibility (3 tests)
- HR Portal web interface
- Client Portal web interface
- Candidate Portal web interface

## 📋 Test Data

### Common Test Inputs
```python
# Job Data
{
    "title": "Senior Python Developer",
    "department": "Engineering", 
    "location": "Mumbai",
    "experience_level": "Senior",
    "requirements": "Python, FastAPI, PostgreSQL, 5+ years"
}

# Candidate Data
{
    "name": "Test Candidate",
    "email": "test.candidate@example.com",
    "technical_skills": "Python, FastAPI, PostgreSQL, Docker, AWS",
    "experience_years": 5
}

# Client Data
{
    "client_id": "test_client_123",
    "company_name": "Test Company Ltd",
    "contact_email": "test.client@example.com"
}
```

## 📊 Report Generation

### Comprehensive Test Report
- **Executive Summary**: Overall success rate and status
- **Service-Level Results**: Per-service breakdown
- **Integration Results**: Cross-service communication
- **Portal Accessibility**: Web interface status
- **Business Workflow**: End-to-end process validation
- **Detailed Results**: Individual endpoint results
- **Recommendations**: Areas for improvement

### Report Sections
1. **📊 Executive Summary** - High-level metrics
2. **🏗️ Service-Level Results** - Per-service analysis
3. **🔗 Service Integration** - Cross-service testing
4. **🌐 Portal Accessibility** - Web interface testing
5. **💼 Business Workflow** - End-to-end validation
6. **🔍 Detailed Results** - Individual test results
7. **🎯 Recommendations** - Improvement suggestions

## 🔧 Configuration

### Environment Variables
```bash
# Recommended for full testing (will auto-discover if not provided)
export API_KEY_SECRET="your-production-api-key"

# Optional - enhanced test will discover alternatives if needed
export GATEWAY_SERVICE_URL="https://bhiv-hr-gateway-ltg0.onrender.com"
export AGENT_SERVICE_URL="https://bhiv-hr-agent-nhgg.onrender.com"
export LANGGRAPH_SERVICE_URL="https://bhiv-hr-langgraph.onrender.com"
export HR_PORTAL_URL="https://bhiv-hr-portal-u670.onrender.com"
export CLIENT_PORTAL_SERVICE_URL="https://bhiv-hr-client-portal-3iod.onrender.com"
export CANDIDATE_PORTAL_SERVICE_URL="https://bhiv-hr-candidate-portal-abe6.onrender.com"
```

### Enhanced Discovery Features
- **API Key Discovery**: Tests common API key patterns if none provided
- **LangGraph URL Discovery**: Tries multiple potential LangGraph service URLs
- **Authentication Setup**: Automatically registers test users and obtains tokens

### Test Configuration
- **Timeout**: 30 seconds per endpoint
- **Retry Logic**: No retries (single attempt)
- **Parallel Execution**: Sequential for data consistency
- **Error Handling**: Comprehensive error capture

## 📈 Success Criteria

### Overall System Health
- **✅ Excellent**: 90%+ success rate
- **⚠️ Attention Needed**: 70-89% success rate  
- **❌ Critical Issues**: <70% success rate

### Service-Level Health
- **Core Services**: Must be 100% operational
- **Business Logic**: Must be 95%+ operational
- **Security Features**: Must be 90%+ operational
- **Integration**: Must be 100% operational

## 🚀 Usage Examples

### Basic Test Run
```bash
python tests/comprehensive_endpoint_tests.py
```

### With Production API Key (Recommended)
```bash
export API_KEY_SECRET="your-production-api-key"
python tests/comprehensive_endpoint_tests.py
```

### With Custom Service URLs
```bash
export LANGGRAPH_SERVICE_URL="https://your-custom-langgraph-url.com"
export API_KEY_SECRET="your-production-api-key"
python tests/comprehensive_endpoint_tests.py
```

### Auto-Discovery Mode (No Configuration)
```bash
# Enhanced test will discover URLs and API keys automatically
python tests/comprehensive_endpoint_tests.py
```

### Direct Module Usage
```python
from tests.comprehensive_endpoint_tests import ComprehensiveEndpointTester
import asyncio

tester = ComprehensiveEndpointTester()
tester.run_sync_tests()  # For synchronous testing
# Or
tester.run_async_tests()  # For asynchronous testing
```

## 📄 Output Files

### Generated Reports
- **ENHANCED_COMPREHENSIVE_TEST_REPORT.md** - Enhanced detailed markdown report with discovery results
- **COMPREHENSIVE_TEST_REPORT.md** - Standard detailed markdown report (fallback)
- **Console Output** - Real-time test progress with enhanced status indicators
- **Error Logs** - Detailed error information with troubleshooting suggestions

### Report Format
```markdown
# 🧪 BHIV HR Platform - Comprehensive Endpoint Test Report

**Test Date**: 2025-01-21 10:30:00
**Total Test Time**: 45.2 seconds
**Success Rate**: 94.4%

## 📊 Executive Summary
| Metric | Value | Status |
|--------|-------|--------|
| Total Endpoints | 108 | 📋 Documented |
| Tested Endpoints | 108 | 🧪 Executed |
| Passed Tests | 98 | ✅ Success |
| Failed Tests | 10 | ❌ Failed |
| Success Rate | 94.4% | ✅ EXCELLENT |
```

## 🎯 Best Practices

### Before Running Tests
1. Ensure all services are deployed and running
2. Set proper API keys and credentials
3. Check network connectivity to production services
4. Review test data for conflicts

### During Testing
1. Monitor console output for real-time progress
2. Note any authentication or permission errors
3. Watch for timeout issues on slower endpoints
4. Check for rate limiting responses

### After Testing
1. Review comprehensive test report
2. Address any failed endpoints
3. Verify integration test results
4. Update documentation if needed

## 🔍 Troubleshooting

### Common Issues
- **Authentication Errors**: Enhanced test will attempt API key discovery
- **LangGraph 404 Errors**: Enhanced test will discover correct URL automatically
- **Timeout Errors**: Services may be slow to respond (enhanced error handling)
- **Rate Limiting**: Enhanced test includes rate limit detection
- **Network Issues**: Check internet connectivity

### Enhanced Troubleshooting
- **API Key Issues**: Test will try multiple common API key patterns
- **Service Discovery**: Automatic discovery of alternative service URLs
- **Authentication Tokens**: Automatic test user registration and token generation
- **Detailed Error Reports**: Enhanced error messages with specific recommendations

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**🎯 Goal**: Ensure 100% endpoint functionality with comprehensive workflow validation  
**📊 Target**: 95%+ success rate across all services  
**🔄 Frequency**: Run before deployments and weekly for monitoring  
**✨ Enhanced**: Automatic service discovery, API key validation, and authentication handling