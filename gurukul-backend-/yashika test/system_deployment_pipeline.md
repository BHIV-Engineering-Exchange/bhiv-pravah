# Global Deployment Sovereignty & Rollback Strategy

## 1. Deployment Philosophy
We treat the Gurukul Backend, EMS System, and Frontend as a unified state. A failure in one is a failure in all.

## 2. Deployment Pipeline (`deploy_all.sh`)
The automated pipeline executes the following steps:
1. **Audit**: Pre-flight check of all service configs.
2. **Backup**: Atomic backup of all codebases into `./backups/`.
3. **Build**: Concurrent builds for Frontend and EMS.
4. **Launch**: Synchronized restart of FastAPI services (Core + EMS).
5. **Verification**: Automated ping of all `/health` endpoints.

## 3. Rollback Strategy (`rollback_all.sh`)
In the event of a critical failure (Watchdog timeout or 500 status):
1. **Halt**: Stop all current deployment traffic.
2. **Revert**: Identify the most recent global backup.
3. **Restore**: Overwrite all service states with the backup version.
4. **Verify**: Post-rollback health audit.

## 4. Versioning
Every release is recorded in `yashika task/VERSION` with a unique timestamp for auditability.
