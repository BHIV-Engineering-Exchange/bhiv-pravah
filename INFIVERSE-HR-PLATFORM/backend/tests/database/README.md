# Database Tests

This directory contains all database-related test files for the BHIV HR Platform.

## Files

- `database_candidate_verification.py` - Candidate data verification tests
- `candidate_portal_database_test.py` - Candidate portal database integration tests  
- `client_portal_database_test.py` - Client portal database integration tests

## Usage

```bash
# Run all database tests
python -m pytest tests/database/

# Run specific test
python tests/database/database_candidate_verification.py
```

## Database Connection

All tests use the production Render PostgreSQL database:
- **Host**: Render PostgreSQL 17
- **Schema**: v4.2.0 (13 core tables)
- **Authentication**: Environment variables from config/