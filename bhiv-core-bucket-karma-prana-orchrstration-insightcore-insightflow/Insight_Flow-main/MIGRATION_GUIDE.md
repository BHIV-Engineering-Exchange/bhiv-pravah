# Supabase to Sovereign Core Migration Guide

## Overview
This guide provides step-by-step instructions for migrating from Supabase to Sovereign Core in the InsightFlow system.

## 🔄 Migration Process

### Phase 1: Preparation
1. **Backup Current Data**
   ```bash
   # Export Supabase data
   supabase db dump --file backup_$(date +%Y%m%d).sql
   ```

2. **Validate Current Configuration**
   ```python
   from app.core.config import settings
   status, issues = settings.validate_migration_config()
   print(f"Current mode: {status}")
   for issue in issues: print(f"Issue: {issue}")
   ```

### Phase 2: Sovereign Core Setup
1. **Set up Sovereign Core Database**
   ```sql
   -- Run the same schema as Supabase (see README.md)
   CREATE TABLE agents (...);
   CREATE TABLE routing_logs (...);
   -- etc.
   ```

2. **Configure Environment Variables**
   ```bash
   # Add Sovereign Core configuration
   USE_SOVEREIGN_CORE=true
   SOVEREIGN_DB_HOST=your-sovereign-db-host
   SOVEREIGN_DB_PORT=5432
   SOVEREIGN_DB_NAME=insightflow_sovereign
   SOVEREIGN_DB_USER=insightflow_user
   SOVEREIGN_DB_PASSWORD=your_secure_password
   SOVEREIGN_SERVICE_KEY=your_secure_service_key
   SOVEREIGN_JWT_SECRET=your_secure_jwt_secret
   ```

### Phase 3: Data Migration
1. **Export Data from Supabase**
   ```python
   # Use Supabase client to export data
   from supabase import create_client
   
   supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
   
   # Export agents
   agents = supabase.table('agents').select('*').execute()
   
   # Export routing_logs
   logs = supabase.table('routing_logs').select('*').execute()
   
   # Export feedback_events
   feedback = supabase.table('feedback_events').select('*').execute()
   ```

2. **Import Data to Sovereign Core**
   ```python
   # Use Sovereign Core database connection
   import asyncpg
   
   conn = await asyncpg.connect(
       host=settings.SOVEREIGN_DB_HOST,
       port=settings.SOVEREIGN_DB_PORT,
       database=settings.SOVEREIGN_DB_NAME,
       user=settings.SOVEREIGN_DB_USER,
       password=settings.SOVEREIGN_DB_PASSWORD
   )
   
   # Insert data into Sovereign Core
   for agent in agents.data:
       await conn.execute(
           "INSERT INTO agents (...) VALUES (...)",
           *agent.values()
       )
   ```

### Phase 4: Testing
1. **Test with Dual Configuration**
   ```bash
   # Keep both configurations temporarily
   USE_SOVEREIGN_CORE=true
   # Keep SUPABASE_* vars for rollback
   ```

2. **Validate Migration**
   ```python
   from app.core.config import settings
   status, issues = settings.validate_migration_config()
   
   if issues:
       print("Migration issues found:")
       for issue in issues:
           print(f"  - {issue}")
   else:
       print("Migration validation passed!")
   ```

### Phase 5: Cleanup
1. **Remove Supabase Configuration**
   ```bash
   # Remove from environment
   unset SUPABASE_URL
   unset SUPABASE_ANON_KEY
   unset SUPABASE_SERVICE_KEY
   ```

2. **Final Validation**
   ```python
   from app.core.config import settings
   status, issues = settings.validate_migration_config()
   
   # Should show: status='sovereign_core', issues=[]
   ```

## 🛠️ Migration Commands

### Check Current Status
```bash
python -c "
from app.core.config import settings
status, issues = settings.validate_migration_config()
print(f'Mode: {status}')
if issues:
    print('Issues:')
    for issue in issues: print(f'  - {issue}')
else:
    print('✅ Configuration valid')
"
```

### Get Migration Guide
```bash
python -c "
from app.core.config import settings
import json
guide = settings.get_migration_guide()
print(json.dumps(guide, indent=2))
"
```

### Test Database Connection
```bash
python -c "
from app.core.config import settings
if settings.USE_SOVEREIGN_CORE:
    print('Testing Sovereign Core connection...')
    # Test connection logic here
else:
    print('Testing Supabase connection...')
    # Test connection logic here
"
```

## 🚨 Rollback Plan

If migration fails, rollback steps:

1. **Revert Environment Variables**
   ```bash
   USE_SOVEREIGN_CORE=false
   # Restore SUPABASE_* variables
   ```

2. **Restart Application**
   ```bash
   docker-compose restart
   ```

3. **Validate Rollback**
   ```python
   from app.core.config import settings
   assert not settings.USE_SOVEREIGN_CORE
   assert settings.SUPABASE_URL is not None
   ```

## 📋 Migration Checklist

### Pre-Migration
- [ ] Backup Supabase data
- [ ] Set up Sovereign Core database
- [ ] Generate secure keys for Sovereign Core
- [ ] Test Sovereign Core connectivity

### During Migration
- [ ] Configure Sovereign Core environment variables
- [ ] Set USE_SOVEREIGN_CORE=true
- [ ] Migrate data from Supabase to Sovereign Core
- [ ] Test application functionality
- [ ] Validate migration configuration

### Post-Migration
- [ ] Remove Supabase environment variables
- [ ] Final configuration validation
- [ ] Monitor application performance
- [ ] Update documentation

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```
   Error: Could not connect to Sovereign Core database
   Solution: Check SOVEREIGN_DB_* environment variables
   ```

2. **Migration Validation Failed**
   ```
   Error: Both Supabase and Sovereign Core configs present
   Solution: Remove SUPABASE_* environment variables after migration
   ```

3. **Service Key Authentication Failed**
   ```
   Error: Invalid Sovereign service key
   Solution: Generate new SOVEREIGN_SERVICE_KEY and SOVEREIGN_JWT_SECRET
   ```

### Debug Commands
```bash
# Check environment variables
env | grep -E "(SUPABASE|SOVEREIGN)"

# Test configuration loading
python -c "from app.core.config import settings; print(settings.USE_SOVEREIGN_CORE)"

# Validate migration status
python -c "
from app.core.config import settings
status, issues = settings.validate_migration_config()
print(f'Status: {status}')
print(f'Issues: {len(issues)}')
"
```

## 📊 Migration Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Preparation | 1-2 hours | Backup data, setup Sovereign Core |
| Migration | 2-4 hours | Data transfer and configuration |
| Testing | 1-2 hours | Validation and testing |
| Cleanup | 30 minutes | Remove old configuration |
| **Total** | **4-8 hours** | Complete migration process |

---

**Note**: Always test migration in a staging environment before production deployment.