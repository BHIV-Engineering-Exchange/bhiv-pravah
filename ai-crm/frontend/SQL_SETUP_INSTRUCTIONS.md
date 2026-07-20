# 📋 SQL Setup Instructions for Supabase

If you're getting the error **"EXPLAIN only works on a single SQL statement"**, follow these instructions:

## ✅ Recommended: Use the Single Script (Easiest)

1. **Open** `supabase_setup_single.sql` file
2. **Copy ALL the contents** (Ctrl+A, then Ctrl+C)
3. **Go to Supabase Dashboard** → **SQL Editor** → **New Query**
4. **Paste the entire script** (Ctrl+V)
5. **Make sure ALL text is selected** (you should see the entire script highlighted)
6. **Click "Run"** or press **Ctrl+Enter**
7. ✅ You should see "Success. No rows returned"

## 🔄 Alternative: Run in Parts (If Single Script Doesn't Work)

If the single script still gives errors, run each part separately:

### Part 1: Create Table
1. Open `supabase_setup_part1.sql`
2. Copy and paste into SQL Editor
3. Click Run

### Part 2: Create Policies
1. Open `supabase_setup_part2.sql`
2. Copy and paste into SQL Editor
3. Click Run

### Part 3: Create Functions & Triggers
1. Open `supabase_setup_part3.sql`
2. Copy and paste into SQL Editor
3. Click Run

### Part 4: Create Indexes
1. Open `supabase_setup_part4.sql`
2. Copy and paste into SQL Editor
3. Click Run

## ⚠️ Important Tips

1. **Select ALL text** before running - Make sure you've selected the entire SQL script, not just part of it
2. **One query at a time** - If using parts, run them one by one, not all at once
3. **Check for errors** - If you see an error, read it carefully. Some errors (like "already exists") are okay
4. **Verify setup** - After running, check Table Editor to see if `profiles` table exists

## 🔍 Verify Your Setup

After running the SQL, verify everything worked:

1. **Check Table**
   - Go to **Table Editor** in Supabase
   - You should see `profiles` table
   - It should have columns: id, email, first_name, last_name, company_name, avatar_url, created_at, updated_at

2. **Check Policies**
   - Go to **Authentication** → **Policies**
   - You should see 4 policies for the `profiles` table

3. **Test Signup**
   - Try creating an account in your app
   - Check if a profile is automatically created in the `profiles` table

## 🐛 Troubleshooting

### Error: "relation already exists"
- This means the table already exists - that's okay! The script uses `IF NOT EXISTS` so it won't break

### Error: "policy already exists"
- This means policies already exist - you can either:
  - Drop existing policies first, OR
  - Skip creating policies (they're already there)

### Error: "function already exists"
- This is okay - the script uses `CREATE OR REPLACE` so it will update existing functions

### Still getting EXPLAIN error?
- Make sure you're selecting ALL the text in the SQL Editor
- Try running the parts separately (Part 1, then Part 2, etc.)
- Make sure there are no extra SELECT statements mixed in

---

**Need help?** The single script (`supabase_setup_single.sql`) should work in most cases. If not, use the parts method.

