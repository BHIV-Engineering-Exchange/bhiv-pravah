# Fix Scripts

This directory contains fix and maintenance scripts for the BHIV HR Platform.

## Files

- `fix_candidates_table.py` - Candidate table structure fixes
- `fix_client_password.py` - Client password reset and fixes
- `reset_client_lock.py` - Reset client account locks

## Usage

```bash
# Run specific fix script
python tests/fixes/fix_candidates_table.py
python tests/fixes/fix_client_password.py
python tests/fixes/reset_client_lock.py
```

## Safety Notes

- These scripts modify production data
- Always backup before running fixes
- Test in development environment first
- Verify database connection before execution

## Database Access

All fix scripts require:
- Production database credentials
- Proper authentication tokens
- Administrative privileges