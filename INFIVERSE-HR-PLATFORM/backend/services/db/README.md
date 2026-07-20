# 🗄️ Database Service (Legacy PostgreSQL Reference)

**Status**: ⚠️ **Historical Reference Only - PostgreSQL Schema Preserved for Backward Compatibility**

**Note**: This directory contains PostgreSQL schema files for historical reference. The BHIV HR Platform has fully migrated to **MongoDB Atlas** as the primary database. These PostgreSQL files are preserved for backward compatibility and migration documentation purposes.

**Migration Status**: ✅ **MongoDB Atlas Production Ready** (Current Primary Database)
**PostgreSQL**: 📦 **Legacy Reference** (No longer in active use)

---

## 📋 Overview

**Current Production Database**: MongoDB Atlas (Cloud-hosted NoSQL)
**Legacy Database**: PostgreSQL schema files (historical reference only)

This directory contains PostgreSQL schema files that were used in earlier versions of the BHIV HR Platform. These files are preserved for:
- Historical reference and documentation
- Backward compatibility analysis
- Migration path documentation
- Legacy system understanding

**Active Database Operations**: All current backend services use MongoDB Atlas for persistent storage.

## Schema Structure (Legacy PostgreSQL)

**Core Application Tables:**
- `candidates`: Candidate profiles and authentication
- `jobs`: Job postings (HR and client)
- `feedback`: 5-point BHIV values assessment
- `interviews`: Scheduling and management
- `offers`: Job offer management
- `users`: Internal HR users (with 2FA)
- `clients`: External client companies (JWT auth)
- `audit_logs`: Security and compliance
- `rate_limits`: API rate limiting
- `csp_violations`: Content Security Policy monitoring
- `matching_cache`: AI matching results cache
- `company_scoring_preferences`: RL/AI learning engine

**System Tables:**
- `client_auth`, `client_sessions`, `schema_version`, `pg_stat_statements`, `pg_stat_statements_info`

**Note**: These PostgreSQL tables are documented for historical purposes. The current system uses MongoDB collections with equivalent functionality.

## Key Features (Legacy PostgreSQL)

- Data validation with CHECK constraints
- 25+ performance indexes (GIN for full-text search)
- Triggers for audit logging and timestamps
- PostgreSQL functions for advanced operations

**Note**: These features are documented for PostgreSQL. The current MongoDB implementation uses equivalent features:
- Schema validation instead of CHECK constraints
- Indexes for performance optimization
- Change streams for audit logging
- Aggregation pipelines for advanced operations

## Usage

**Historical Purpose**: These PostgreSQL schemas were used by earlier versions of the backend microservices for persistent storage.

**Current Production**: All backend services (Gateway port 8000, Agent port 9000, LangGraph port 9001) now use MongoDB Atlas for persistent storage.

Migration Status: The system successfully migrated from PostgreSQL to MongoDB Atlas on January 22, 2026. All data was migrated, and MongoDB is now the production database with 111 total endpoints across the three services.

**Legacy Files Purpose**: 
- Documentation and migration analysis
- Historical system understanding
- Backward compatibility reference
- Development and testing scenarios

## 🔄 Current Database Implementation (MongoDB Atlas)

**Production Database**: MongoDB Atlas
**Connection**: MongoDB Atlas Cluster (bhiv_hr database)
**Services**: All 3 microservices use MongoDB (ports 8000, 9000, 9001)
**Endpoints**: 111 total across all services
**Collections**: 17+ MongoDB collections replacing PostgreSQL tables

For current MongoDB schema documentation, see:
- `backend/docs/database/DATABASE_DOCUMENTATION.md`
- `backend/docs/database/MONGODB_COLLECTIONS.md`
- `backend/docs/database/MONGODB_ATLAS_SETUP.md`

## 📚 Local Development (Legacy PostgreSQL)

The PostgreSQL setup instructions below are preserved for historical reference. For current development, refer to MongoDB Atlas setup in the main backend documentation.

```bash
# Using Docker (Legacy PostgreSQL Reference)
docker run -d --name bhiv-db \
  -e POSTGRES_DB=bhiv_hr \
  -e POSTGRES_USER=bhiv_user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:17-alpine

# Initialize schema (Historical Reference)
psql postgresql://bhiv_user:password@localhost:5432/bhiv_hr -f consolidated_schema.sql
```

---
**BHIV HR Platform Database Service** - Legacy PostgreSQL Reference Documentation

**Last Updated**: January 22, 2026
**Current Database**: MongoDB Atlas (Production)
**Legacy Database**: PostgreSQL (Historical Reference)
**Migration Status**: ✅ Completed January 22, 2026
**Services**: 3 Microservices (8000, 9000, 9001) with 111 total endpoints
**Collections**: 17+ MongoDB collections (replacing PostgreSQL tables)

*Built with Integrity, Honesty, Discipline, Hard Work & Gratitude*
