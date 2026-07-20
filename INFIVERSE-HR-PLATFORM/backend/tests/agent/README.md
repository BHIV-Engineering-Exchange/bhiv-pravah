# Agent Service Tests

This directory contains all tests related to the AI Agent Service, including:

## Test Categories

### Agent Service Tests
- `test_agent_*.py` - Core agent service functionality tests
- `diagnose_agent_service.py` - Agent service diagnostics
- `check_agent_status.py` - Agent status monitoring
- `validate_agent_schema.py` - Schema validation for agent service

### AI Matching Tests
- `test_ai_matching_*.py` - AI matching algorithm tests
- `test_deployed_ai_matching.py` - Production AI matching tests
- `test_final_ai_matching.py` - Final AI matching validation
- `debug_batch_matching.py` - Batch matching debugging

### Agent Fixes
- `fix_agent_timeout.py` - Agent timeout issue fixes

## Running Tests

```bash
# Run all agent tests
python -m pytest tests/agent/

# Run specific test category
python tests/agent/test_agent_endpoints.py
python tests/agent/test_ai_matching_comprehensive.py
```

## Test Coverage
- Agent service endpoints (6 endpoints)
- AI matching algorithms (Phase 3)
- Batch processing functionality
- Timeout and error handling
- Schema validation