# Supabase Setup Guide for Gurukul Application

## Quick Setup Steps

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Wait for the project to be ready

### 2. Run SQL Setup

1. In your Supabase dashboard, go to **SQL Editor**
2. Copy and paste the entire content of `src/sql/complete_supabase_setup.sql`
3. Click **Run** to execute the script

This will create:

- ✅ `students` table with proper structure
- ✅ `form_configurations` table for dynamic forms
- ✅ All necessary indexes for performance
- ✅ Row Level Security policies
- ✅ Auto-updating timestamps
- ✅ Default form configuration
- ✅ Sample student data for testing

### 3. Get Your Supabase Credentials

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy your **Project URL** and **anon public** key

### 4. Set Up Environment Variables

Create a `.env.local` file in your project root with:

```env
VITE_SUPABASE_URL=your_project_url_here
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_SUPABASE_TABLE=students

# Admin Credentials (change these for security)
VITE_ADMIN_USERNAME=admin
VITE_ADMIN_PASSWORD=admin123
```

### 5. Test Your Setup

1. Start your development server: `npm run dev`
2. Go to `/admin` (login with the credentials you set in your `.env.local` file)
3. You should see the sample students
4. Go to `/intake` to test the form submission

## Database Schema Overview

### Students Table

```sql
students (
  id UUID PRIMARY KEY,
  user_id TEXT,
  name TEXT,
  email TEXT UNIQUE,
  student_id TEXT,
  grade TEXT,
  tier TEXT CHECK (tier IN ('Seed', 'Tree', 'Sky')),
  responses JSONB,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)
```

### Form Configurations Table

```sql
form_configurations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  fields JSONB NOT NULL,
  is_active BOOLEAN,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)
```

## Features Enabled

### ✅ Student Intake System

- Dynamic form configuration
- JSONB storage for flexible responses
- Automatic tier assignment (Seed → Tree → Sky)
- Email-based user identification

### ✅ Admin Panel

- View all students
- Edit student profiles
- Manage form configurations
- Real-time form builder

### ✅ Security

- Row Level Security enabled
- Authenticated user policies
- Input validation and sanitization

### ✅ Performance

- Optimized indexes on frequently queried fields
- GIN index on JSONB responses for fast searching
- Automatic timestamp updates

## Troubleshooting

### Common Issues

**1. "relation does not exist" error**

- Make sure you ran the complete SQL setup script
- Check that tables were created in the public schema

**2. "permission denied" error**

- Verify your RLS policies are set up correctly
- Check your Supabase anon key is correct

**3. Form not loading**

- Ensure the default form configuration was inserted
- Check browser console for any JavaScript errors

**4. Environment variables not working**

- Make sure `.env.local` is in your project root
- Restart your development server after adding env vars
- Verify the variable names start with `VITE_`

### Verification Queries

Run these in Supabase SQL Editor to verify setup:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name IN ('students', 'form_configurations');

-- Check sample data
SELECT name, email, tier FROM students;

-- Check active form config
SELECT name, is_active FROM form_configurations WHERE is_active = true;
```

## Next Steps

1. **Customize the form**: Use the admin panel to modify form fields
2. **Add authentication**: Integrate with Clerk or Supabase Auth
3. **Implement assessment logic**: Add scoring and tier assignment
4. **Add more features**: Progress tracking, badges, etc.

Your Gurukul application is now ready to use! 🚀
