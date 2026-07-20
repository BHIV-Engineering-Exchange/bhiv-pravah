# PRANA Ledger Integrity (Hardened)

## Overview
The PRANA Ledger has been hardened with a "Vedic Chain" of cryptographic hashes, ensuring that all telemetry and critical outputs are tamper-evident. Any modification or deletion of historical data will be immediately detected by the Verification Engine.

## Architecture
Each record in the `prana_packets`, `review_output_versions`, and `next_task_versions` tables now includes:
*   `previous_hash`: The SHA-256 hash of the preceding record in the chain.
*   `current_hash`: The SHA-256 hash of the canonical JSON representation of the current record.

## Components

### 1. Deterministic Repository
Located at `backend/app/services/deterministic_repo.py`. This is the central service for adding and verifying chained records.

### 2. Verification Engine
Logic encapsulated in `DeterministicRepository.verify_entire_ledger()`.
Run manually via:
```powershell
python backend/scripts/verify_ledger_integrity.py
```

### 3. Migration Utility
Used to backfill hashes for legacy data:
```powershell
python backend/scripts/migrate_ledger_hashes.py
```

## Maintenance Guidelines
1.  **Never Modify Directly**: Do not use SQL to update records in the chained tables. Use the repository services.
2.  **Regular Audits**: Schedule a weekly cron job to run `verify_ledger_integrity.py` and alert if the status is anything but `PASS`.
3.  **Genesis State**: The very first record in any chain links to the Genesis Hash (`0` * 64).
