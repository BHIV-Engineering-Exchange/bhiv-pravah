# EMS Backend Database Solution (Free Tier Limitation)

## Problem
Render free tier only allows **one PostgreSQL database**, but EMS and Gurukul have conflicting table names:
- Both use `users` table
- Both use `lessons` table  
- Both use `prana_packets` table

## Solutions

### Option 1: Use Same Database (Quick Fix) ⚠️
**Risk:** Table name conflicts will cause errors

**Steps:**
1. Use the same `DATABASE_URL` as Gurukul Backend
2. EMS will try to create its own tables
3. If table names conflict, you'll get errors

**When this works:**
- If EMS tables are created first, Gurukul might fail
- If Gurukul tables exist, EMS will fail to create conflicting tables
- **Not recommended** - will cause issues

### Option 2: Use PostgreSQL Schemas (Recommended) ✅
**Best solution** - Use same database but different schemas

**How it works:**
- Same PostgreSQL database
- Different schemas (like folders in a database)
- EMS uses `ems` schema
- Gurukul uses `gurukul` schema (or `public`)

**Implementation:**
Update EMS Backend `DATABASE_URL` to include schema:
```
postgresql://user:password@host:port/dbname?options=-csearch_path%3Dems
```

Or modify the connection to use schema prefix.

### Option 3: Upgrade to Paid Tier 💰
- Render Starter plan: $7/month
- Allows multiple databases
- Clean separation of data

### Option 4: Use External Database (Free) 🆓
- Use a free PostgreSQL from:
  - **Supabase** (free tier)
  - **Neon** (free tier)
  - **ElephantSQL** (free tier)
- Then use that connection string for EMS

## Recommended: Option 4 (External Free Database)

**Best for free tier:**
1. Sign up for **Supabase** (free): https://supabase.com
2. Create a new project
3. Get the PostgreSQL connection string
4. Use that for EMS Backend `DATABASE_URL`

**Or use Neon:**
1. Sign up for **Neon** (free): https://neon.tech
2. Create a database
3. Get connection string
4. Use for EMS Backend

Both are free and give you a separate database!

