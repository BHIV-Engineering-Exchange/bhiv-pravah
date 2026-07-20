# Sovereign Fusion Layer Runbook

## Operational Guide

This runbook provides step-by-step instructions for operating and maintaining the Sovereign Fusion Layer.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Starting the Service](#starting-the-service)
3. [Health Checks](#health-checks)
4. [Monitoring](#monitoring)
5. [Troubleshooting](#troubleshooting)
6. [Database Maintenance](#database-maintenance)
7. [Model Updates](#model-updates)
8. [Backup Procedures](#backup-procedures)

## Initial Setup

### Prerequisites

1. **Python 3.9+** installed
2. **CUDA-capable GPU** (recommended) or CPU
3. **PostgreSQL** or SQLite database
4. **Model checkpoint** available

### Installation Steps

1. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Verify Checkpoint**:
   ```bash
   python -c "import pickle; f = open('checkpoint_info.pkl', 'rb'); data = pickle.load(f); print(data); f.close()"
   ```

3. **Initialize Database**:
   ```bash
   python create_tables.py
   ```

4. **Verify Adapter Registry**:
   ```bash
   cat adapters/registry.json
   ```

5. **Verify Prosody Mappings**:
   ```bash
   cat data/prosody_mappings.json
   ```

## Starting the Service

### Development Mode

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Environment Variables

```bash
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
export CUDA_VISIBLE_DEVICES=0
uvicorn app.main:app --reload
```

## Health Checks

### Basic Health Check

```bash
curl http://localhost:8000/api/v1/sovereign/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "model_loaded": true,
  "service": "sovereign_fusion_layer"
}
```

### Full Pipeline Test

```bash
curl -X POST http://localhost:8000/api/v1/sovereign/infer \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is mathematics?",
    "lang": "en",
    "target_lang": "ar",
    "tone": "educational"
  }'
```

**Expected**: Response with `output` and `pipeline_stages` array.

## Monitoring

### Key Metrics to Monitor

1. **Model Loading Status**:
   - Check `/api/v1/sovereign/health` endpoint
   - `model_loaded` should be `true`

2. **Pipeline Performance**:
   - Monitor `processing_time_ms` in pipeline stages
   - LM Core: Should be < 5 seconds
   - KSML: Should be < 200ms
   - Full pipeline: Should be < 10 seconds

3. **RL Rewards**:
   - Check `rl_rewards` table for reward collection
   - Monitor average reward values
   - Check for errors in reward processing

4. **Database Health**:
   - Monitor `rl_episodes` table growth
   - Check for database connection errors
   - Monitor query performance

### Log Monitoring

**Key Log Messages**:
- `Model loaded successfully`: Model initialization complete
- `Episode {id} merged with {n} rewards`: RL episode saved
- `Policy {name} updated`: RL policy updated
- `Adapter selected for language {lang}`: Adapter selection working

**Error Patterns to Watch**:
- `LM Core failed`: Model inference error
- `Failed to merge episode`: Database error
- `Adapter not found`: Missing adapter file
- `Prosody hint generation failed`: Prosody mapping error

## Troubleshooting

### Issue: Model Not Loading

**Symptoms**:
- `model_loaded: false` in health check
- Errors in logs about checkpoint path

**Steps**:
1. Verify `checkpoint_info.pkl` exists:
   ```bash
   ls -la checkpoint_info.pkl
   ```

2. Check checkpoint path:
   ```bash
   python -c "import pickle; f = open('checkpoint_info.pkl', 'rb'); data = pickle.load(f); print(data.get('checkpoint_path')); f.close()"
   ```

3. Verify checkpoint directory exists:
   ```bash
   ls -la <checkpoint_path>
   ```

4. Check VRAM availability:
   ```bash
   nvidia-smi
   ```

**Solution**: Ensure checkpoint path is correct and VRAM is available.

### Issue: Adapter Not Found

**Symptoms**:
- `adapter_selection` stage shows `status: "skipped"`
- Logs show "No adapter found"

**Steps**:
1. Check registry file:
   ```bash
   cat adapters/registry.json
   ```

2. Verify adapter file exists:
   ```bash
   ls -la adapters/ar_adapter.bin
   ```

3. Check adapter path in registry matches actual file location

**Solution**: Update `registry.json` with correct adapter path or add adapter file.

### Issue: RL Rewards Not Saving

**Symptoms**:
- Episodes not appearing in database
- Errors about database session

**Steps**:
1. Check database connection:
   ```bash
   python -c "from app.core.database import SessionLocal; db = SessionLocal(); print('Connected'); db.close()"
   ```

2. Verify tables exist:
   ```sql
   SELECT * FROM rl_episodes LIMIT 1;
   SELECT * FROM rl_rewards LIMIT 1;
   ```

3. Check database logs for errors

**Solution**: Ensure database is running and tables are created.

### Issue: Slow Inference

**Symptoms**:
- Pipeline takes > 10 seconds
- High CPU/GPU usage

**Steps**:
1. Check model loading (first call is slower):
   ```bash
   # First call will be slower due to model loading
   ```

2. Monitor resource usage:
   ```bash
   nvidia-smi  # For GPU
   htop  # For CPU
   ```

3. Check for memory leaks:
   - Monitor memory usage over time
   - Restart service if memory grows continuously

**Solution**: 
- Use GPU for faster inference
- Increase batch size if processing multiple requests
- Consider model quantization for faster inference

## Database Maintenance

### Backup Database

```bash
# PostgreSQL
pg_dump -U user -d dbname > backup_$(date +%Y%m%d).sql

# SQLite
cp gurukul.db backup_$(date +%Y%m%d).db
```

### Clean Old Episodes

```sql
-- Delete episodes older than 30 days
DELETE FROM rl_rewards 
WHERE episode_id IN (
  SELECT id FROM rl_episodes 
  WHERE created_at < NOW() - INTERVAL '30 days'
);

DELETE FROM rl_episodes 
WHERE created_at < NOW() - INTERVAL '30 days';
```

### Check Database Size

```sql
-- PostgreSQL
SELECT pg_size_pretty(pg_database_size('dbname'));

-- SQLite
SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();
```

## Model Updates

### Updating Model Checkpoint

1. **Backup Current Model**:
   ```bash
   cp checkpoint_info.pkl checkpoint_info.pkl.backup
   ```

2. **Update Checkpoint Info**:
   ```python
   import pickle
   new_info = {
       "checkpoint_path": "/path/to/new/checkpoint",
       "base_model_name": "unsloth/llama-3.2-3b-instruct-bnb-4bit",
       # ... other fields
   }
   with open('checkpoint_info.pkl', 'wb') as f:
       pickle.dump(new_info, f)
   ```

3. **Restart Service**:
   ```bash
   # Service will reload model on next request
   ```

### Updating Adapters

1. **Add New Adapter**:
   - Place adapter file in `adapters/` directory
   - Update `adapters/registry.json` with adapter metadata

2. **Sync from NAS** (if configured):
   ```bash
   python scripts/sync_adapters_nas.py
   ```

## Backup Procedures

### Daily Backups

1. **Database Backup**:
   ```bash
   # Add to cron
   0 2 * * * pg_dump -U user -d dbname > /backups/db_$(date +\%Y\%m\%d).sql
   ```

2. **Configuration Backup**:
   ```bash
   tar -czf config_backup_$(date +%Y%m%d).tar.gz \
     checkpoint_info.pkl \
     adapters/ \
     data/prosody_mappings.json
   ```

### Recovery Procedures

1. **Restore Database**:
   ```bash
   psql -U user -d dbname < backup_20250120.sql
   ```

2. **Restore Configuration**:
   ```bash
   tar -xzf config_backup_20250120.tar.gz
   ```

## Emergency Procedures

### Service Down

1. **Check Service Status**:
   ```bash
   curl http://localhost:8000/api/v1/sovereign/health
   ```

2. **Check Logs**:
   ```bash
   tail -f logs/app.log
   ```

3. **Restart Service**:
   ```bash
   # Kill existing process
   pkill -f "uvicorn app.main:app"
   
   # Start new process
   uvicorn app.main:app --reload
   ```

### Database Connection Lost

1. **Check Database Status**:
   ```bash
   # PostgreSQL
   systemctl status postgresql
   
   # SQLite
   ls -la gurukul.db
   ```

2. **Restart Database** (if needed):
   ```bash
   systemctl restart postgresql
   ```

3. **Verify Connection**:
   ```bash
   python -c "from app.core.database import SessionLocal; db = SessionLocal(); print('OK'); db.close()"
   ```

## Performance Tuning

### GPU Optimization

1. **Set CUDA Device**:
   ```bash
   export CUDA_VISIBLE_DEVICES=0
   ```

2. **Enable Mixed Precision**:
   - Already enabled in model loading (float16)

### Database Optimization

1. **Add Indexes**:
   ```sql
   CREATE INDEX idx_rl_rewards_episode ON rl_rewards(episode_id);
   CREATE INDEX idx_rl_rewards_source ON rl_rewards(source);
   CREATE INDEX idx_rl_episodes_lang ON rl_episodes(target_lang);
   ```

2. **Vacuum Database** (PostgreSQL):
   ```sql
   VACUUM ANALYZE;
   ```

## Support Contacts

- **Technical Issues**: Check logs first, then escalate
- **Model Issues**: Verify checkpoint and VRAM
- **Database Issues**: Check connection and tables

## Change Log

- **2025-01-20**: Initial runbook created
- **Day 1-5**: Core functionality implemented
- **Day 7**: Documentation and runbook completed

