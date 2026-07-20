# 🗄️ BHIV HR Platform - DBeaver Database Setup Guide

**Updated**: December 16, 2025 (Database Authentication Fixed)  
**Database**: PostgreSQL 17 (Schema v4.3.1)  
**Architecture**: Microservices (6 Services + Database)  
**Platform**: Render Cloud (Oregon, US West)  
**Status**: ✅ Production Ready | 19 Tables | 111 Endpoints | 99.9% Uptime | Database Issues Resolved

---

## 📋 Overview

**Complete professional guide for connecting to both Local and Production databases using DBeaver**

This comprehensive guide provides step-by-step instructions for setting up DBeaver connections to visualize and manage the BHIV HR Platform databases across different environments.

### **🏗️ Database Architecture Summary**
- **Schema Version**: v4.3.1 with Phase 3 semantic engine + RL integration
- **Total Tables**: 19 tables (13 core business + 5 security/audit + 1 AI/performance + 6 RL integration)
- **Extensions**: uuid-ossp, pg_stat_statements, pg_trgm, btree_gin
- **Features**: Advanced triggers, 75+ indexes, comprehensive audit logging, RL system, workflow automation
- **Performance**: Connection pooling, query optimization, real-time monitoring

### **🌐 Environment Overview**
| Environment | Database | Host | Port | Schema | Status |
|-------------|----------|------|------|--------|--------|
| **Local Development** | PostgreSQL 15/17 | localhost | 5432 | v4.3.0 | ✅ Active |
| **Production (Render)** | PostgreSQL 17 | Internal Render URL | 5432 | v4.3.0 | ✅ Live |

---

## 🚀 Quick Setup Summary

### **Connection Matrix**
| Environment | Host | Database | Username | SSL | Status |
|-------------|------|----------|----------|-----|--------|
| **Local** | localhost | bhiv_hr | bhiv_user | Disabled | ✅ Active - Auth Fixed |
| **Production** | `<internal_render_url>` | bhiv_hr | bhiv_user | Required | ✅ Live - Auth Fixed |

### **Schema Statistics**
- **Core Business Tables**: 8 (candidates, jobs, job_applications, feedback, interviews, offers, clients, users)
- **Security & Audit Tables**: 5 (audit_logs, rate_limits, csp_violations, security_events, api_keys)
- **AI & Performance Tables**: 1 (matching_cache)
- **RL Integration Tables**: 6 (rl_feedback, rl_model_performance, rl_training_data, rl_model_updates, company_scoring_preferences, rl_exploration_log)
- **System Management Tables**: 1 (schema_version)

---

## 📥 Prerequisites & Installation

### **1. Install DBeaver Community Edition**
```bash
# Download from official website (Recommended)
https://dbeaver.io/download/

# Package Manager Installation Options:
# Windows (Chocolatey)
choco install dbeaver

# macOS (Homebrew)
brew install --cask dbeaver-community

# Ubuntu/Debian (Snap)
sudo snap install dbeaver-ce

# Ubuntu/Debian (APT)
sudo add-apt-repository ppa:serge-rider/dbeaver-ce
sudo apt update
sudo apt install dbeaver-ce

# Arch Linux (AUR)
yay -S dbeaver
```

### **2. Verify System Requirements**
```yaml
Minimum Requirements:
  OS: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
  RAM: 4GB (8GB recommended)
  Java: OpenJDK 11+ (bundled with DBeaver)
  Disk Space: 500MB for installation
  Network: Internet connection for driver downloads

Recommended Configuration:
  RAM: 8GB+ for large datasets
  CPU: Multi-core for query performance
  SSD: For faster query execution
  Network: Stable connection for cloud databases
```

### **3. Verify Local Environment (Development)**
```bash
# Check Docker containers status
docker ps | grep postgres

# Start local environment if needed
cd "c:\BHIV HR PLATFORM"
docker-compose -f docker-compose.production.yml up -d

# Verify database health through API
curl http://localhost:8000/health
curl http://localhost:8000/test-candidates

# Check database directly
docker exec -it bhiv-hr-platform-db-1 psql -U bhiv_user -d bhiv_hr -c "SELECT version();"
```

---

## 🏠 Local Database Connection Setup

### **Step 1: Create New Connection**
1. **Launch DBeaver** Community Edition
2. **Click** "New Database Connection" (plug icon) or press `Ctrl+Shift+N`
3. **Select** "PostgreSQL" from the database list
4. **Click** "Next" to proceed

### **Step 2: Configure Connection Details**
```yaml
Main Connection Settings:
┌─────────────────────────────────────────────────────────────┐
│ Connection Name: BHIV HR - Local Development               │
│ Server Host:     localhost                                 │
│ Port:           5432                                       │
│ Database:       bhiv_hr                                    │
│ Username:       bhiv_user                                  │
│ Password:       bhiv_password                               │
│ Show all databases: ☑ (checked)                           │
│ Save password: ☑ (checked for convenience)                │
└─────────────────────────────────────────────────────────────┘
```

### **Step 3: Advanced Configuration**
1. **Click** "Driver properties" tab
2. **Configure** these essential properties:
   ```yaml
   Driver Properties:
   ├── ssl: false
   ├── sslmode: disable
   ├── ApplicationName: DBeaver-BHIV-Local
   ├── connectTimeout: 30
   ├── socketTimeout: 30
   └── prepareThreshold: 5
   ```

### **Step 4: Connection Testing**
1. **Click** "Test Connection" button
2. **Expected Result**: ✅ "Connected" message with connection details
3. **If prompted**: Allow DBeaver to download PostgreSQL driver automatically
4. **Verify**: Connection shows database version and schema information
5. **Click** "OK" to save the connection

### **Step 5: Connection Customization**
```yaml
Connection Appearance:
├── Name: BHIV HR - Local Development
├── Color: 🔵 Blue (for local environment identification)
├── Description: Local development database for BHIV HR Platform
└── Folder: Create "BHIV HR Platform" folder for organization
```

---

## ☁️ Production Database Connection Setup

### **Step 1: Create Production Connection**
1. **Open DBeaver** Community Edition
2. **Click** "New Database Connection" (plug icon)
3. **Select** "PostgreSQL" from database types
4. **Click** "Next" to continue

### **Step 2: Configure Production Details**
```yaml
Production Connection Settings:
┌─────────────────────────────────────────────────────────────────────┐
│ Connection Name: BHIV HR - Production (Render Cloud)                │
│ Server Host:     <internal_render_postgresql_url>                   │
│ Port:           5432                                                │
│ Database:       bhiv_hr                                             │
│ Username:       bhiv_user                                           │
│ Password:       bhiv_password                                       │
│ Show all databases: ☑ (checked)                                    │
│ Save password: ☑ (checked - ensure secure environment)             │
└─────────────────────────────────────────────────────────────────────┘

⚠️ Security Note: Use actual production credentials from Render dashboard
```

### **Step 3: SSL Configuration (MANDATORY for Production)**
1. **Click** "SSL" tab (located next to "Driver properties")
2. **Configure SSL settings** (Required for Render PostgreSQL):
   ```yaml
   SSL Configuration:
   ├── SSL mode: require (select from dropdown - MANDATORY)
   ├── SSL Factory: org.postgresql.ssl.DefaultJavaSSLFactory (from dropdown)
   ├── CA Certificate: (leave empty - auto-managed by Render)
   ├── Client Certificate: (leave empty - not required)
   ├── Client Private Key: (leave empty - not required)
   └── SSL Password: (leave empty - not required)
   ```

### **Step 4: Advanced Production Properties**
1. **Click** "Driver properties" tab
2. **Configure** production-optimized properties:
   ```yaml
   Production Driver Properties:
   ├── ApplicationName: DBeaver-BHIV-Production
   ├── connectTimeout: 30
   ├── socketTimeout: 60
   ├── loginTimeout: 30
   ├── prepareThreshold: 5
   ├── defaultRowFetchSize: 1000
   └── readOnly: true (recommended for safety)
   ```

### **Step 5: Test Production Connection**
1. **Click** "Test Connection" button
2. **Expected Result**: ✅ "Connected" message with SSL confirmation
3. **If SSL errors occur**: Verify SSL configuration in Step 3
4. **If timeout errors**: Check network connectivity and increase timeout values
5. **Click** "OK" to save connection

### **Step 6: Production Connection Customization**
```yaml
Production Connection Appearance:
├── Name: BHIV HR - Production (Render Cloud)
├── Color: 🔴 Red (for production environment identification)
├── Description: Production database hosted on Render Cloud Platform
├── Folder: BHIV HR Platform (same folder as local)
└── Read-only: ☑ (recommended for data safety)
```

---

## 🔄 Connection Management & Updates

### **Updating Existing Connections**
When database credentials change due to new deployments or security updates:

#### **Step 1: Edit Existing Connection**
1. **Right-click** existing connection in DBeaver navigator
2. **Select** "Edit Connection" from context menu
3. **Alternative**: Double-click connection name to edit

#### **Step 2: Update Connection Parameters**
```yaml
Fields to Update (when credentials change):
├── Server Host: Update to new hostname if changed
├── Database: Update database name if changed  
├── Password: Enter new password from Render dashboard
├── Keep Same: Port (5432), Username (bhiv_user), SSL settings
└── Test: Always test connection after updates
```

#### **Step 3: Verify Updated Connection**
```sql
-- Test query to verify connection functionality
SELECT 
    current_database() as database_name,
    current_user as username,
    version() as postgres_version,
    now() as connection_time,
    inet_server_addr() as server_ip,
    inet_server_port() as server_port;

-- Verify schema version
SELECT version, applied_at, description 
FROM schema_version 
ORDER BY applied_at DESC 
LIMIT 1;
```

### **Connection Backup & Restore**
```yaml
Backup Connection Settings:
1. File → Export → DBeaver → Connections
2. Select connections to backup
3. Choose secure location for .dbeaver file
4. Include passwords (if secure environment)

Restore Connection Settings:
1. File → Import → DBeaver → Connections  
2. Select .dbeaver backup file
3. Choose connections to restore
4. Test all restored connections
```

---

## 🔍 Database Schema Exploration

### **Complete Schema Structure (v4.3.0)**
```
📊 BHIV HR Platform Schema v4.3.0 - Production Ready
├── 🏢 Core Business Tables (8)
│   ├── 👥 candidates (Primary entity with 50+ fields)
│   │   ├── Basic Info: id, name, email, phone, location
│   │   ├── Professional: experience_years, technical_skills, resume_path
│   │   ├── Scoring: average_score (generated), status, created_at
│   │   └── Indexes: email (unique), skills (GIN), status, created_at
│   │
│   ├── 💼 jobs (Job postings with client relationships)
│   │   ├── Details: title, department, location, job_type
│   │   ├── Requirements: experience_level, requirements, salary_range
│   │   ├── Relations: client_id (FK), posted_by, status
│   │   └── Indexes: client_id, status, title, created_at
│   │
│   ├── 📋 job_applications (Application tracking)
│   │   ├── Relations: candidate_id (FK), job_id (FK)
│   │   ├── Content: cover_letter, resume_version, status
│   │   ├── Tracking: applied_date, updated_at, reviewed_by
│   │   └── Constraints: UNIQUE(candidate_id, job_id)
│   │
│   ├── 📝 feedback (BHIV Values Assessment - 5-point scale)
│   │   ├── Values: integrity, honesty, discipline, hard_work, gratitude
│   │   ├── Relations: candidate_id (FK), job_id (FK), application_id (FK)
│   │   ├── Scoring: average_score (generated), assessment_date
│   │   └── Indexes: candidate_id, job_id, average_score DESC
│   │
│   ├── 🎤 interviews (Interview management)
│   │   ├── Scheduling: interview_date, interview_time, duration_minutes
│   │   ├── Details: interviewer_name, interview_type, meeting_link
│   │   ├── Results: status, notes, rating (1-10), recommendation
│   │   └── Indexes: candidate_id, job_id, interview_date, status
│   │
│   ├── 💰 offers (Job offers and negotiations)
│   │   ├── Financial: salary_offered, currency, benefits_package (JSONB)
│   │   ├── Terms: start_date, terms_conditions, offer_letter_path
│   │   ├── Status: status, offer_date, response_deadline, accepted_date
│   │   └── Indexes: candidate_id, job_id, status, offer_date
│   │
│   ├── 🏢 clients (External companies)
│   │   ├── Company: client_id (unique), company_name, industry
│   │   ├── Contact: contact_email, contact_phone, website, address
│   │   ├── Security: password_hash, two_factor_enabled, backup_codes
│   │   └── Indexes: client_id, company_name, status, subscription_tier
│   │
│   └── 👤 users (Internal HR staff)
│       ├── Identity: username (unique), email (unique), full_name
│       ├── Security: password_hash, totp_secret, is_2fa_enabled
│       ├── Access: role, permissions (JSONB), status, last_login
│       └── Indexes: username, email, role, status, last_login
│
├── 🔐 Security & Audit Tables (5)
│   ├── 📋 audit_logs (Comprehensive activity tracking)
│   │   ├── Identity: user_id (FK), client_id (FK), candidate_id (FK)
│   │   ├── Action: action, resource, resource_id, old_values (JSONB)
│   │   ├── Context: ip_address, user_agent, session_id, timestamp
│   │   └── Indexes: user_id, client_id, action, resource, timestamp DESC
│   │
│   ├── ⚡ rate_limits (API rate limiting)
│   │   ├── Tracking: ip_address, endpoint, user_tier, request_count
│   │   ├── Windows: window_start, window_duration, blocked_until
│   │   ├── Relations: user_id (FK), client_id (FK)
│   │   └── Indexes: ip_address, endpoint, window_start, blocked_until
│   │
│   ├── 🛡️ csp_violations (Content Security Policy violations)
│   │   ├── Violation: violated_directive, blocked_uri, document_uri
│   │   ├── Context: ip_address, user_agent, session_id, timestamp
│   │   ├── Relations: user_id (FK), client_id (FK)
│   │   └── Indexes: violated_directive, ip_address, timestamp DESC
│   │
│   ├── 🔒 security_events (Security incident tracking)
│   │   ├── Event: event_type, severity, description, details (JSONB)
│   │   ├── Resolution: resolved, resolved_by, resolved_at
│   │   ├── Context: user_id (FK), client_id (FK), ip_address
│   │   └── Indexes: event_type, severity, resolved, timestamp DESC
│   │
│   └── 🔑 api_keys (API key management)
│       ├── Key: key_hash, key_prefix, name, description
│       ├── Access: permissions (JSONB), rate_limit_tier, expires_at
│       ├── Usage: last_used_at, usage_count, status
│       └── Indexes: key_hash, user_id, client_id, status, expires_at
│
├── 🤖 AI & Performance Tables (1)
│   └── 💾 matching_cache (AI matching results cache)
│       ├── Relations: job_id (FK), candidate_id (FK)
│       ├── Scores: match_score, skills_match_score, experience_match_score
│       ├── AI: algorithm_version (phase3_v1.0), reasoning, confidence_score
│       ├── Performance: processing_time_ms, cache_hit, expires_at
│       └── Indexes: job_id, candidate_id, match_score DESC, expires_at
│
├── 🧠 Reinforcement Learning Tables (6)
│   ├── 📊 rl_feedback (ML feedback for learning)
│   │   ├── Relations: candidate_id (FK), job_id (FK), match_id (FK)
│   │   ├── Feedback: feedback_type, feedback_score, hiring_outcome
│   │   ├── Performance: performance_rating, retention_months
│   │   └── Indexes: candidate_id, job_id, feedback_type, feedback_date
│   │
│   ├── 🎯 rl_model_performance (Model performance tracking)
│   │   ├── Metrics: accuracy_score, precision_score, recall_score, f1_score
│   │   ├── Training: training_samples, validation_samples, convergence_epoch
│   │   ├── Config: hyperparameters (JSONB), feature_importance (JSONB)
│   │   └── Indexes: model_version, accuracy_score DESC, evaluation_date
│   │
│   ├── 🔄 rl_training_data (Training dataset)
│   │   ├── Features: candidate_features (JSONB), job_features (JSONB)
│   │   ├── RL: state_representation (JSONB), action_taken, reward_signal
│   │   ├── Episodes: episode_id, step_number, terminal_state
│   │   └── Indexes: episode_id, outcome_label, created_at, used_in_training
│   │
│   ├── 📈 rl_model_updates (Model update tracking)
│   │   ├── Versions: old_model_version, new_model_version, update_type
│   │   ├── Performance: performance_improvement, accuracy_delta
│   │   ├── Deployment: deployment_status, updated_by, update_date
│   │   └── Indexes: new_model_version, deployment_status, update_date
│   │
│   ├── 🏢 company_scoring_preferences (Client-specific preferences)
│   │   ├── Relations: client_id (FK), scoring_weights (JSONB)
│   │   ├── Preferences: preferred_skills, required_experience_years
│   │   ├── Performance: avg_satisfaction_score, feedback_count
│   │   └── Indexes: client_id, avg_satisfaction_score, updated_at
│   │
│   └── 🎲 rl_exploration_log (Exploration strategy tracking)
│       ├── Strategy: exploration_strategy, exploration_rate, exploitation_rate
│       ├── Space: action_space_size, state_space_dimension
│       ├── Rewards: reward_received, cumulative_reward, episode_id
│       └── Indexes: exploration_strategy, episode_id, timestamp
│
└── 📈 System Management Tables (1)
    └── 🏷️ schema_version (Database version tracking)
        ├── Version: version (PK - current: v4.3.0), applied_at
        ├── Migration: migration_script, rollback_script, checksum
        ├── Execution: applied_by, execution_time_ms, status
        └── Indexes: applied_at DESC, status
```

### **Key Relationship Mapping**
```sql
-- Core Business Relationships
candidates (1) ←→ (N) job_applications ←→ (1) jobs ←→ (1) clients
candidates (1) ←→ (N) feedback ←→ (1) jobs
candidates (1) ←→ (N) interviews ←→ (1) jobs  
candidates (1) ←→ (N) offers ←→ (1) jobs
candidates (1) ←→ (N) matching_cache ←→ (1) jobs

-- Security & Audit Relationships
users (1) ←→ (N) audit_logs
clients (1) ←→ (N) audit_logs
users (1) ←→ (N) api_keys
clients (1) ←→ (N) api_keys

-- RL System Relationships
matching_cache (1) ←→ (N) rl_feedback
rl_feedback (N) → rl_training_data (N) → rl_model_performance (1)
clients (1) ←→ (1) company_scoring_preferences
```

---

## 📊 Essential Queries for Data Exploration

### **1. Schema Verification & Health Check**
```sql
-- Current schema version and status
SELECT 
    version,
    applied_at,
    description,
    status,
    execution_time_ms
FROM schema_version 
ORDER BY applied_at DESC 
LIMIT 5;

-- Complete table inventory with row counts
SELECT 
    schemaname,
    tablename,
    tableowner,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as table_size,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_name = t.tablename AND table_schema = 'public') as column_count
FROM pg_tables t
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(tablename::regclass) DESC;

-- Index usage and performance
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### **2. Comprehensive Data Overview**
```sql
-- Complete data counts across all tables
SELECT 
    'Core Business Tables' as category,
    'candidates' as table_name, 
    COUNT(*) as record_count,
    MAX(created_at) as latest_record
FROM candidates
UNION ALL
SELECT 'Core Business Tables', 'jobs', COUNT(*), MAX(created_at) FROM jobs
UNION ALL
SELECT 'Core Business Tables', 'job_applications', COUNT(*), MAX(applied_date) FROM job_applications
UNION ALL
SELECT 'Core Business Tables', 'feedback', COUNT(*), MAX(created_at) FROM feedback
UNION ALL
SELECT 'Core Business Tables', 'interviews', COUNT(*), MAX(created_at) FROM interviews
UNION ALL
SELECT 'Core Business Tables', 'offers', COUNT(*), MAX(created_at) FROM offers
UNION ALL
SELECT 'Core Business Tables', 'clients', COUNT(*), MAX(created_at) FROM clients
UNION ALL
SELECT 'Core Business Tables', 'users', COUNT(*), MAX(created_at) FROM users
UNION ALL
SELECT 'Security & Audit', 'audit_logs', COUNT(*), MAX(timestamp) FROM audit_logs
UNION ALL
SELECT 'Security & Audit', 'rate_limits', COUNT(*), MAX(created_at) FROM rate_limits
UNION ALL
SELECT 'Security & Audit', 'csp_violations', COUNT(*), MAX(timestamp) FROM csp_violations
UNION ALL
SELECT 'Security & Audit', 'security_events', COUNT(*), MAX(timestamp) FROM security_events
UNION ALL
SELECT 'Security & Audit', 'api_keys', COUNT(*), MAX(created_at) FROM api_keys
UNION ALL
SELECT 'AI & Performance', 'matching_cache', COUNT(*), MAX(created_at) FROM matching_cache
UNION ALL
SELECT 'RL Integration', 'rl_feedback', COUNT(*), MAX(created_at) FROM rl_feedback
UNION ALL
SELECT 'RL Integration', 'rl_model_performance', COUNT(*), MAX(evaluation_date) FROM rl_model_performance
UNION ALL
SELECT 'RL Integration', 'rl_training_data', COUNT(*), MAX(created_at) FROM rl_training_data
UNION ALL
SELECT 'RL Integration', 'rl_model_updates', COUNT(*), MAX(update_date) FROM rl_model_updates
UNION ALL
SELECT 'RL Integration', 'company_scoring_preferences', COUNT(*), MAX(updated_at) FROM company_scoring_preferences
UNION ALL
SELECT 'RL Integration', 'rl_exploration_log', COUNT(*), MAX(timestamp) FROM rl_exploration_log
ORDER BY category, record_count DESC;
```

### **3. Business Intelligence Queries**
```sql
-- Candidate performance summary with AI scores
SELECT 
    c.id,
    c.name,
    c.email,
    c.location,
    c.experience_years,
    c.average_score as values_score,
    COUNT(DISTINCT ja.id) as applications_count,
    COUNT(DISTINCT i.id) as interviews_count,
    COUNT(DISTINCT o.id) as offers_count,
    AVG(mc.match_score) as avg_ai_match_score,
    MAX(mc.created_at) as last_ai_match
FROM candidates c
LEFT JOIN job_applications ja ON c.id = ja.candidate_id
LEFT JOIN interviews i ON c.id = i.candidate_id
LEFT JOIN offers o ON c.id = o.candidate_id
LEFT JOIN matching_cache mc ON c.id = mc.candidate_id
WHERE c.status = 'active'
GROUP BY c.id, c.name, c.email, c.location, c.experience_years, c.average_score
ORDER BY c.average_score DESC, avg_ai_match_score DESC
LIMIT 20;

-- Job posting analytics with client information
SELECT 
    j.id,
    j.title,
    j.department,
    j.location,
    j.experience_level,
    c.company_name,
    c.subscription_tier,
    COUNT(DISTINCT ja.candidate_id) as applicants_count,
    COUNT(DISTINCT i.candidate_id) as interviewed_count,
    COUNT(DISTINCT o.candidate_id) as offers_made,
    AVG(mc.match_score) as avg_match_score,
    j.status,
    j.created_at
FROM jobs j
LEFT JOIN clients c ON j.client_id = c.client_id
LEFT JOIN job_applications ja ON j.id = ja.job_id
LEFT JOIN interviews i ON j.id = i.job_id
LEFT JOIN offers o ON j.id = o.job_id
LEFT JOIN matching_cache mc ON j.id = mc.job_id
GROUP BY j.id, j.title, j.department, j.location, j.experience_level, 
         c.company_name, c.subscription_tier, j.status, j.created_at
ORDER BY j.created_at DESC;

-- RL system performance analysis
SELECT 
    rmp.model_version,
    rmp.algorithm_type,
    rmp.accuracy_score,
    rmp.precision_score,
    rmp.recall_score,
    rmp.f1_score,
    rmp.training_samples,
    rmp.evaluation_date,
    COUNT(rf.id) as feedback_count,
    AVG(rf.feedback_score) as avg_feedback_score
FROM rl_model_performance rmp
LEFT JOIN rl_feedback rf ON rf.created_at >= rmp.evaluation_date
GROUP BY rmp.model_version, rmp.algorithm_type, rmp.accuracy_score, 
         rmp.precision_score, rmp.recall_score, rmp.f1_score,
         rmp.training_samples, rmp.evaluation_date
ORDER BY rmp.evaluation_date DESC;
```

### **4. System Performance & Monitoring**
```sql
-- Database performance metrics
SELECT 
    'Database Size' as metric,
    pg_size_pretty(pg_database_size(current_database())) as value,
    'Total database size including indexes' as description
UNION ALL
SELECT 
    'Active Connections',
    COUNT(*)::text,
    'Current active database connections'
FROM pg_stat_activity 
WHERE state = 'active' AND datname = current_database()
UNION ALL
SELECT 
    'Cache Hit Ratio',
    ROUND(
        (sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read))) * 100, 2
    )::text || '%',
    'Percentage of queries served from cache'
FROM pg_statio_user_tables
UNION ALL
SELECT 
    'Index Hit Ratio',
    ROUND(
        (sum(idx_blks_hit) / (sum(idx_blks_hit) + sum(idx_blks_read))) * 100, 2
    )::text || '%',
    'Percentage of index queries served from cache'
FROM pg_statio_user_indexes;

-- Table activity and performance
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;

-- Query performance analysis (if pg_stat_statements enabled)
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_time DESC
LIMIT 10;
```

---

## 🎯 DBeaver Workspace Organization

### **1. Professional Project Structure**
```
DBeaver Workspace Organization:
├── 📁 BHIV HR Platform
│   ├── 🔵 Local Development
│   │   ├── 📊 Core Business Tables
│   │   │   ├── candidates, jobs, job_applications
│   │   │   ├── feedback, interviews, offers
│   │   │   └── clients, users
│   │   ├── 🔐 Security & Audit Tables
│   │   │   ├── audit_logs, rate_limits
│   │   │   ├── csp_violations, security_events
│   │   │   └── api_keys
│   │   ├── 🤖 AI & RL Tables
│   │   │   ├── matching_cache
│   │   │   ├── rl_feedback, rl_model_performance
│   │   │   ├── rl_training_data, rl_model_updates
│   │   │   ├── company_scoring_preferences
│   │   │   └── rl_exploration_log
│   │   └── 📝 Development Queries
│   │       ├── schema_exploration.sql
│   │       ├── data_validation.sql
│   │       └── performance_testing.sql
│   │
│   └── 🔴 Production (Render Cloud)
│       ├── 📊 Core Business Tables (Read-Only)
│       ├── 🔐 Security & Audit Tables (Read-Only)
│       ├── 🤖 AI & RL Tables (Read-Only)
│       └── 📈 Production Monitoring
│           ├── system_health.sql
│           ├── performance_metrics.sql
│           ├── security_monitoring.sql
│           └── business_analytics.sql
```

### **2. Saved Query Organization**
```sql
-- Create organized folders for queries
-- Right-click connection → SQL Editor → New SQL Script

-- 📊 Business Analytics Folder
-- File: candidate_performance_dashboard.sql
SELECT 
    c.name,
    c.average_score,
    COUNT(ja.id) as applications,
    AVG(mc.match_score) as avg_ai_score
FROM candidates c
LEFT JOIN job_applications ja ON c.id = ja.candidate_id
LEFT JOIN matching_cache mc ON c.id = mc.candidate_id
GROUP BY c.id, c.name, c.average_score
ORDER BY c.average_score DESC;

-- File: job_posting_analytics.sql
SELECT 
    j.title,
    cl.company_name,
    COUNT(ja.id) as applicants,
    AVG(f.average_score) as avg_candidate_score
FROM jobs j
LEFT JOIN clients cl ON j.client_id = cl.client_id
LEFT JOIN job_applications ja ON j.id = ja.job_id
LEFT JOIN feedback f ON ja.candidate_id = f.candidate_id
GROUP BY j.id, j.title, cl.company_name
ORDER BY applicants DESC;

-- 🔍 System Monitoring Folder
-- File: database_health_check.sql
SELECT 
    'Schema Version' as check_type,
    version as status
FROM schema_version 
ORDER BY applied_at DESC 
LIMIT 1;

-- File: performance_overview.sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size,
    n_live_tup as live_rows
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
```

### **3. Advanced DBeaver Configuration**
```yaml
Preferences → Data Viewer:
├── Result Sets:
│   ├── Max rows in memory: 10000
│   ├── Max rows per page: 1000
│   ├── Auto-fetch next segment: ☑
│   ├── Show row numbers: ☑
│   └── Show column description: ☑
├── Data Formatting:
│   ├── Date format: yyyy-MM-dd HH:mm:ss
│   ├── Time format: HH:mm:ss
│   ├── Number format: #,##0.00
│   ├── Boolean format: true/false
│   └── NULL value text: <NULL>
├── Data Editor:
│   ├── Auto-save on focus loss: ☑
│   ├── Confirm data changes: ☑
│   ├── Show foreign key values: ☑
│   └── Disable expensive operations: ☑
└── SQL Editor:
    ├── Auto-completion: ☑
    ├── Highlight matching brackets: ☑
    ├── Show line numbers: ☑
    ├── Word wrap: ☑
    └── Syntax highlighting: ☑
```

---

## 🔧 Advanced Troubleshooting

### **Common Connection Issues & Solutions**

#### **✅ Recent Fix: Database Authentication Issue (December 16, 2025)**

**Issue Resolved:**
- **Problem**: PostgreSQL password authentication failed for user "bhiv_user"
- **Solution**: Database user password reset to match .env configuration
- **Status**: ✅ **RESOLVED** - All database connections now working
- **Impact**: Jobs API restored (27 jobs), Candidates API restored (34 candidates)

**Verification in DBeaver:**
```sql
-- Test connection
SELECT current_database(), current_user, 'Connection successful' as status;

-- Verify current data
SELECT 'candidates' as table_name, COUNT(*) as records FROM candidates
UNION ALL
SELECT 'jobs', COUNT(*) FROM jobs;
-- Expected: candidates=34, jobs=27
```

#### **1. Local Database Connection Failures**
```bash
# Issue: "Connection refused" or "Database not accessible"
# Diagnosis Commands:
docker ps | grep postgres
docker logs bhiv-hr-platform-db-1

# Solutions:
# Start Docker services
cd "c:\BHIV HR PLATFORM"
docker-compose -f docker-compose.production.yml up -d

# Verify database is running
docker exec -it bhiv-hr-platform-db-1 psql -U bhiv_user -d bhiv_hr -c "\l"

# Fix authentication issues (December 16, 2025 fix)
docker exec bhiv-hr-platform-db-1 psql -U postgres -d bhiv_hr -c "ALTER USER bhiv_user PASSWORD 'bhiv_password';"

# Check port availability
netstat -an | findstr :5432

# Reset Docker network (if needed)
docker-compose down
docker system prune -f
docker-compose up -d
```

#### **2. Production SSL Connection Errors**
```yaml
Error Types & Solutions:

SSL Connection Required:
├── Error: "SSL connection is required"
├── Solution: Configure SSL in DBeaver
│   ├── SSL Tab → SSL mode: require
│   ├── SSL Factory: org.postgresql.ssl.DefaultJavaSSLFactory
│   └── Leave certificate fields empty

SSL Handshake Failed:
├── Error: "SSL handshake failed"
├── Solutions:
│   ├── Verify SSL mode is "require" (not "prefer")
│   ├── Check network connectivity to Render
│   ├── Increase connection timeout to 60 seconds
│   └── Verify hostname is correct (no typos)

Certificate Verification Failed:
├── Error: "Certificate verification failed"
├── Solutions:
│   ├── Ensure CA Certificate field is empty
│   ├── Use DefaultJavaSSLFactory
│   ├── Check system date/time is correct
│   └── Update Java/DBeaver to latest version
```

#### **3. Authentication & Authorization Issues**
```yaml
Authentication Failed:
├── Error: "password authentication failed for user"
├── Solutions:
│   ├── Verify username: bhiv_user (case-sensitive)
│   ├── Check password from Render dashboard
│   ├── Ensure no extra spaces in credentials
│   └── Try copying password directly from Render

Permission Denied:
├── Error: "permission denied for table/schema"
├── Solutions:
│   ├── Verify user has correct permissions
│   ├── Check if user is connecting to correct database
│   ├── Ensure schema is 'public' (default)
│   └── Contact admin for permission review

Connection Limit Exceeded:
├── Error: "too many connections for role"
├── Solutions:
│   ├── Close unused DBeaver connections
│   ├── Use connection pooling settings
│   ├── Increase connection timeout
│   └── Monitor concurrent connections
```

#### **4. Performance & Timeout Issues**
```yaml
Query Timeout Solutions:
├── Increase socket timeout in Driver Properties
├── Use LIMIT clauses for large result sets
├── Create indexes for frequently queried columns
├── Use EXPLAIN ANALYZE to optimize slow queries
└── Consider read replicas for heavy analytics

Connection Timeout Solutions:
├── Increase connectTimeout to 60 seconds
├── Check network stability and latency
├── Use connection keep-alive settings
├── Monitor database server load
└── Consider connection retry logic

Memory Issues:
├── Reduce result set size with LIMIT
├── Increase DBeaver memory allocation
├── Use streaming for large datasets
├── Close unused query tabs
└── Clear query result cache regularly
```

### **Performance Optimization Strategies**

#### **1. Connection Pool Optimization**
```yaml
Local Development Pool:
├── Initial Connections: 2
├── Maximum Connections: 5
├── Connection Timeout: 30 seconds
├── Idle Timeout: 10 minutes
└── Validation Query: SELECT 1

Production Pool:
├── Initial Connections: 1
├── Maximum Connections: 3
├── Connection Timeout: 60 seconds
├── Idle Timeout: 5 minutes
├── Read-Only Mode: ☑ (recommended)
└── Validation Query: SELECT version()
```

#### **2. Query Optimization Guidelines**
```sql
-- ✅ Good Practices
-- Use specific columns instead of SELECT *
SELECT id, name, email FROM candidates LIMIT 100;

-- Use indexes for WHERE clauses
SELECT * FROM candidates WHERE email = 'specific@email.com';

-- Use EXPLAIN ANALYZE for performance tuning
EXPLAIN ANALYZE SELECT * FROM candidates 
WHERE experience_years > 5 
ORDER BY average_score DESC;

-- ❌ Avoid These Patterns
-- Don't use SELECT * on large tables without LIMIT
-- Don't use functions in WHERE clauses without functional indexes
-- Don't join large tables without proper indexes
-- Don't use LIKE '%pattern%' on large text columns without GIN indexes
```

#### **3. Memory Management**
```yaml
DBeaver Memory Settings:
├── Heap Size: -Xmx4g (4GB for large datasets)
├── Result Set Limit: 10000 rows max
├── Auto-fetch: Disabled for large tables
├── Query Timeout: 300 seconds
└── Connection Pool: Limited to 5 per database

Query Best Practices:
├── Use LIMIT for exploratory queries
├── Close result tabs when finished
├── Use streaming for large exports
├── Clear query history regularly
└── Monitor memory usage in Task Manager
```

---

## 📊 Visual Data Exploration & Analytics

### **1. Entity Relationship Diagram Creation**
```yaml
Steps to Create ER Diagram:
1. Right-click database connection
2. Select "View Diagram" or "ER Diagram"
3. Drag tables from navigator to canvas
4. DBeaver auto-detects foreign key relationships
5. Customize layout and appearance
6. Save diagram for documentation

Recommended Tables for ER Diagram:
├── Core Flow: candidates → job_applications → jobs → clients
├── Assessment: candidates → feedback → jobs
├── Process: candidates → interviews → offers
├── AI System: candidates → matching_cache → jobs
└── RL System: matching_cache → rl_feedback → rl_training_data
```

### **2. Data Export & Reporting Options**
```yaml
Export Formats Available:
├── 📊 Excel (.xlsx) - Best for business users
├── 📄 CSV (.csv) - Universal data exchange
├── 🗄️ SQL Insert Statements - Database migration
├── 📋 JSON (.json) - API integration
├── 📈 HTML Report - Web presentation
├── 🖼️ XML (.xml) - Structured data
└── 📋 Markdown (.md) - Documentation

Export Configuration:
├── Include column headers: ☑
├── Include row numbers: ☐
├── Date format: ISO 8601
├── Number format: Decimal notation
├── NULL value representation: <empty>
└── Character encoding: UTF-8
```

### **3. Custom Dashboard Creation**
```sql
-- Create materialized views for dashboard queries
CREATE MATERIALIZED VIEW candidate_dashboard AS
SELECT 
    c.id,
    c.name,
    c.email,
    c.location,
    c.experience_years,
    c.average_score,
    COUNT(DISTINCT ja.id) as total_applications,
    COUNT(DISTINCT i.id) as total_interviews,
    COUNT(DISTINCT o.id) as total_offers,
    AVG(mc.match_score) as avg_ai_match_score,
    MAX(ja.applied_date) as last_application_date,
    c.status,
    c.created_at
FROM candidates c
LEFT JOIN job_applications ja ON c.id = ja.candidate_id
LEFT JOIN interviews i ON c.id = i.candidate_id
LEFT JOIN offers o ON c.id = o.candidate_id
LEFT JOIN matching_cache mc ON c.id = mc.candidate_id
GROUP BY c.id, c.name, c.email, c.location, c.experience_years, 
         c.average_score, c.status, c.created_at;

-- Refresh materialized view (run periodically)
REFRESH MATERIALIZED VIEW candidate_dashboard;

-- Create business intelligence view
CREATE VIEW business_metrics AS
SELECT 
    'Total Candidates' as metric,
    COUNT(*)::text as value,
    'Active candidates in system' as description
FROM candidates WHERE status = 'active'
UNION ALL
SELECT 
    'Total Jobs',
    COUNT(*)::text,
    'Open job positions'
FROM jobs WHERE status = 'open'
UNION ALL
SELECT 
    'Applications This Month',
    COUNT(*)::text,
    'Job applications in current month'
FROM job_applications 
WHERE applied_date >= date_trunc('month', CURRENT_DATE)
UNION ALL
SELECT 
    'Average Match Score',
    ROUND(AVG(match_score), 2)::text,
    'AI matching accuracy'
FROM matching_cache 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
```

---

## 🔒 Security Best Practices & Compliance

### **1. Connection Security Configuration**
```yaml
Security Checklist:
├── SSL/TLS Configuration:
│   ├── ☑ SSL enabled for production connections
│   ├── ☑ Certificate validation configured
│   ├── ☑ Secure cipher suites used
│   └── ☑ Connection encryption verified
├── Credential Management:
│   ├── ☑ Strong passwords used
│   ├── ☑ Credentials stored securely in DBeaver
│   ├── ☑ Regular password rotation schedule
│   └── ☑ No credentials in query history
├── Access Control:
│   ├── ☑ Read-only access for production
│   ├── ☑ Principle of least privilege
│   ├── ☑ User activity monitoring
│   └── ☑ Session timeout configured
└── Network Security:
    ├── ☑ VPN connection when required
    ├── ☑ Firewall rules configured
    ├── ☑ IP whitelisting enabled
    └── ☑ Network traffic encrypted
```

### **2. Query Safety Guidelines**
```sql
-- ✅ Safe Query Practices
-- Always use LIMIT for exploratory queries
SELECT * FROM candidates LIMIT 100;

-- Use transactions for data modifications
BEGIN;
UPDATE candidates SET status = 'inactive' WHERE id = 123;
-- Verify changes before committing
SELECT * FROM candidates WHERE id = 123;
COMMIT; -- or ROLLBACK if incorrect

-- Use parameterized queries to prevent SQL injection
-- In DBeaver, use variables: ${variable_name}
SELECT * FROM candidates WHERE email = '${candidate_email}';

-- ❌ Dangerous Practices to Avoid
-- Never run UPDATE/DELETE without WHERE clause
-- Never execute untrusted SQL from external sources
-- Never store sensitive data in query history
-- Never share connection credentials
```

### **3. Audit & Compliance Features**
```sql
-- Monitor user activity
SELECT 
    user_id,
    action,
    resource,
    ip_address,
    timestamp,
    success
FROM audit_logs 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY timestamp DESC;

-- Track data access patterns
SELECT 
    resource,
    COUNT(*) as access_count,
    COUNT(DISTINCT user_id) as unique_users,
    MAX(timestamp) as last_access
FROM audit_logs 
WHERE action = 'view' 
  AND timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY resource
ORDER BY access_count DESC;

-- Security event monitoring
SELECT 
    event_type,
    severity,
    COUNT(*) as event_count,
    MAX(timestamp) as latest_event
FROM security_events 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY event_type, severity
ORDER BY severity DESC, event_count DESC;
```

---

## 📈 Monitoring & Maintenance

### **1. Database Health Monitoring**
```sql
-- Comprehensive health check query
WITH health_metrics AS (
    SELECT 
        'Database Size' as metric,
        pg_size_pretty(pg_database_size(current_database())) as value,
        'green' as status
    UNION ALL
    SELECT 
        'Active Connections',
        COUNT(*)::text,
        CASE WHEN COUNT(*) > 50 THEN 'red' 
             WHEN COUNT(*) > 20 THEN 'yellow' 
             ELSE 'green' END
    FROM pg_stat_activity 
    WHERE state = 'active'
    UNION ALL
    SELECT 
        'Cache Hit Ratio',
        ROUND((sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read))) * 100, 2)::text || '%',
        CASE WHEN (sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read))) > 0.95 THEN 'green'
             WHEN (sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read))) > 0.90 THEN 'yellow'
             ELSE 'red' END
    FROM pg_statio_user_tables
    UNION ALL
    SELECT 
        'Longest Running Query',
        EXTRACT(EPOCH FROM (now() - query_start))::int::text || ' seconds',
        CASE WHEN EXTRACT(EPOCH FROM (now() - query_start)) > 300 THEN 'red'
             WHEN EXTRACT(EPOCH FROM (now() - query_start)) > 60 THEN 'yellow'
             ELSE 'green' END
    FROM pg_stat_activity 
    WHERE state = 'active' AND query_start IS NOT NULL
    ORDER BY query_start ASC
    LIMIT 1
)
SELECT * FROM health_metrics ORDER BY 
    CASE status 
        WHEN 'red' THEN 1 
        WHEN 'yellow' THEN 2 
        WHEN 'green' THEN 3 
    END;
```

### **2. Performance Trend Analysis**
```sql
-- Table growth analysis
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as current_size,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    CASE 
        WHEN n_live_tup > 0 THEN ROUND((n_dead_tup::float / n_live_tup::float) * 100, 2)
        ELSE 0 
    END as dead_row_percentage,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;

-- Query performance trends (requires pg_stat_statements)
SELECT 
    LEFT(query, 100) as query_preview,
    calls,
    total_time,
    mean_time,
    ROUND((total_time / sum(total_time) OVER()) * 100, 2) as percent_total_time
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_time DESC
LIMIT 20;
```

### **3. Automated Maintenance Tasks**
```sql
-- Create maintenance procedures
CREATE OR REPLACE FUNCTION maintenance_report()
RETURNS TABLE(
    check_name text,
    status text,
    details text,
    recommendation text
) AS $$
BEGIN
    -- Check for tables needing vacuum
    RETURN QUERY
    SELECT 
        'Vacuum Analysis' as check_name,
        CASE WHEN COUNT(*) > 0 THEN 'WARNING' ELSE 'OK' END as status,
        COUNT(*)::text || ' tables with >20% dead rows' as details,
        'Run VACUUM ANALYZE on affected tables' as recommendation
    FROM pg_stat_user_tables 
    WHERE n_dead_tup > 0 AND (n_dead_tup::float / GREATEST(n_live_tup, 1)::float) > 0.2;
    
    -- Check for unused indexes
    RETURN QUERY
    SELECT 
        'Index Usage',
        CASE WHEN COUNT(*) > 0 THEN 'INFO' ELSE 'OK' END,
        COUNT(*)::text || ' potentially unused indexes',
        'Review and consider dropping unused indexes'
    FROM pg_stat_user_indexes 
    WHERE idx_scan = 0 AND schemaname = 'public';
    
    -- Check for long-running queries
    RETURN QUERY
    SELECT 
        'Long Running Queries',
        CASE WHEN COUNT(*) > 0 THEN 'WARNING' ELSE 'OK' END,
        COUNT(*)::text || ' queries running >5 minutes',
        'Investigate and optimize slow queries'
    FROM pg_stat_activity 
    WHERE state = 'active' 
      AND query_start < now() - interval '5 minutes'
      AND query NOT LIKE '%maintenance_report%';
END;
$$ LANGUAGE plpgsql;

-- Run maintenance report
SELECT * FROM maintenance_report();
```

---

## 📚 Additional Resources & Documentation

### **Official Documentation Links**
- **[DBeaver Documentation](https://dbeaver.io/docs/)** - Complete user guide
- **[PostgreSQL Documentation](https://www.postgresql.org/docs/)** - Database reference
- **[Render PostgreSQL Guide](https://render.com/docs/databases)** - Cloud database setup
- **[SQL Best Practices](https://www.postgresql.org/docs/current/sql.html)** - Query optimization

### **BHIV HR Platform Documentation**
- **[Project Structure](../../architecture/PROJECT_STRUCTURE.md)** - Complete architecture overview
- **[Database Schema](../../services/db/consolidated_schema.sql)** - Full schema definition
- **[API Documentation](../../api/API_DOCUMENTATION.md)** - REST API reference
- **[Deployment Guide](../guides/DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Connection Diagram](CONNECTION_DIAGRAM.md)** - Database connection architecture

### **Quick Reference Commands**
```bash
# Local Environment
docker ps | grep postgres                                    # Check local database
curl http://localhost:8000/health                           # API health check
docker logs bhiv-hr-platform-db-1                          # Database logs

# Production Environment  
curl https://bhiv-hr-gateway-ltg0.onrender.com/health      # Production API health
curl https://bhiv-hr-gateway-ltg0.onrender.com/test-candidates # Database connectivity

# DBeaver Shortcuts
Ctrl+Shift+N    # New connection
Ctrl+Enter      # Execute query
Ctrl+Shift+O    # Format SQL
F4              # Edit connection
Ctrl+Shift+C    # Copy as INSERT
```

### **Connection String Templates**
```bash
# Local Development
postgresql://bhiv_user:bhiv_password@localhost:5432/bhiv_hr

# Production (Internal - for reference only)
postgresql://bhiv_user:bhiv_password@<internal_render_host>:5432/bhiv_hr

# Connection Parameters
?sslmode=require&application_name=DBeaver-BHIV&connect_timeout=30
```

---

## ✅ Setup Verification Checklist

### **🏠 Local Development Connection**
- [ ] DBeaver Community Edition installed and updated
- [ ] Docker containers running (PostgreSQL service active)
- [ ] Local connection created with correct parameters
- [ ] Connection test successful (✅ "Connected" message)
- [ ] Can view all 19 tables in schema
- [ ] Sample queries execute without errors
- [ ] Schema version shows v4.3.0
- [ ] Performance queries return expected results
- [ ] Connection saved with blue color coding

### **☁️ Production Connection**
- [ ] Production connection created with SSL configuration
- [ ] SSL mode set to "require" with DefaultJavaSSLFactory
- [ ] Connection test successful with SSL confirmation
- [ ] Can access production data (read-only recommended)
- [ ] All 19 tables visible and accessible
- [ ] Business intelligence queries functional
- [ ] Monitoring queries working correctly
- [ ] Connection saved with red color coding
- [ ] Read-only mode enabled for safety

### **📊 Data Exploration & Analytics**
- [ ] Entity relationship diagram created and saved
- [ ] Core business queries bookmarked and organized
- [ ] Performance monitoring queries tested
- [ ] Security audit queries functional
- [ ] RL system analytics queries working
- [ ] Export functionality tested (Excel, CSV, JSON)
- [ ] Custom views and materialized views created
- [ ] Dashboard queries optimized and saved

### **🔒 Security & Compliance**
- [ ] SSL/TLS encryption verified for production
- [ ] Credentials stored securely in DBeaver
- [ ] Read-only access configured for production
- [ ] Query safety guidelines implemented
- [ ] Audit logging queries functional
- [ ] Security monitoring active
- [ ] Access control policies understood
- [ ] Compliance requirements met

### **🔧 Performance & Optimization**
- [ ] Connection pooling configured appropriately
- [ ] Query timeout settings optimized
- [ ] Memory allocation configured for dataset size
- [ ] Index usage monitoring active
- [ ] Performance trend analysis functional
- [ ] Maintenance procedures documented
- [ ] Troubleshooting procedures tested
- [ ] Backup and recovery procedures understood

---

## 🎉 Setup Complete

### **✅ BHIV HR Platform Database Access Established**

**Congratulations!** You now have professional, secure, and optimized database access to the BHIV HR Platform through DBeaver Community Edition.

### **🌟 Key Achievements**
- **Dual Environment Access**: Both local development and production databases configured
- **Enterprise Security**: SSL/TLS encryption and read-only production access
- **Professional Organization**: Structured workspace with categorized queries
- **Performance Optimization**: Connection pooling and query optimization configured
- **Comprehensive Monitoring**: Health checks, performance metrics, and security auditing
- **Business Intelligence**: Advanced analytics and reporting capabilities

### **🚀 Next Steps**
1. **Explore the Data**: Use the provided business intelligence queries to understand the platform
2. **Create Custom Reports**: Build dashboards for your specific analytical needs
3. **Monitor Performance**: Regularly run health check and performance queries
4. **Stay Updated**: Keep DBeaver updated and monitor schema version changes
5. **Maintain Security**: Follow security best practices and audit access regularly

---

*Built with Integrity, Honesty, Discipline, Hard Work & Gratitude*

**BHIV HR Platform v4.3.1** - Enterprise AI-powered recruiting platform with comprehensive database access and professional data management capabilities. Database authentication issues resolved December 16, 2025.