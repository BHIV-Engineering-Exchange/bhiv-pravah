# Fix Supabase Database Connection Issue

## Problem
The direct connection to Supabase (port 5432) is being blocked by network/firewall:
```
connection to server at "db.jjlhxfhstolhtekolmky.supabase.co", port 5432 failed: Network is unreachable
```

## Solution: Use Connection Pooler

Supabase provides a **connection pooler** that's more reliable for cloud deployments like Render.

### Steps to Fix:

1. **Get Connection Pooler URL from Supabase:**
   - Go to: https://supabase.com/dashboard/project/jjlhxfhstolhtekolmky
   - Click: **Settings** → **Database**
   - Scroll to: **Connection string** section
   - Select: **Connection Pooling** tab
   - Choose: **Session mode** (recommended for SQLAlchemy)
   - Copy the connection string
   - It should look like:
     ```
     postgresql://postgres.jjlhxfhstolhtekolmky:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
     ```

2. **Update DATABASE_URL in Render:**
   - Go to Render Dashboard → EMS Backend service → Environment
   - Find `DATABASE_URL`
   - Replace with the connection pooler URL (port 6543)
   - Make sure to replace `[YOUR-PASSWORD]` with: `WpDz7bjJltWa7im4`

3. **Alternative: Check Supabase Firewall**
   - Go to Supabase Dashboard → Settings → Database
   - Check **Connection Pooling** settings
   - Make sure it's enabled
   - Or check **Network Restrictions** and allow all IPs (0.0.0.0/0)

## Connection Pooler Format:
```
postgresql://postgres.jjlhxfhstolhtekolmky:WpDz7bjJltWa7im4@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

**Note:** The username format changes from `postgres` to `postgres.jjlhxfhstolhtekolmky` when using the pooler.

