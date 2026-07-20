-- =====================================================
-- SUPABASE DATABASE SETUP FOR AUTHENTICATION SYSTEM
-- =====================================================
-- Run these SQL commands in Supabase SQL Editor
-- Dashboard → SQL Editor → New Query → Paste & Run
-- =====================================================

-- 1. CREATE PROFILES TABLE
-- This stores additional user information beyond what Supabase Auth provides
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  first_name TEXT,
  last_name TEXT,
  company_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. ENABLE ROW LEVEL SECURITY
-- This ensures users can only access their own data
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 3. CREATE RLS POLICIES
-- Policy: Users can view their own profile
CREATE POLICY "Users can view own profile"
  ON public.profiles
  FOR SELECT
  USING (auth.uid() = id);

-- Policy: Users can insert their own profile during signup
CREATE POLICY "Users can insert own profile"
  ON public.profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = id);

-- Policy: Users can delete their own profile (optional)
CREATE POLICY "Users can delete own profile"
  ON public.profiles
  FOR DELETE
  USING (auth.uid() = id);

-- 4. CREATE FUNCTION TO AUTO-UPDATE updated_at
-- This automatically updates the updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. CREATE TRIGGER FOR AUTO-UPDATE
-- Attach the function to the profiles table
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at();

-- 6. CREATE FUNCTION TO AUTO-CREATE PROFILE (Optional but recommended)
-- This automatically creates a profile when a user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, created_at, updated_at)
  VALUES (
    NEW.id,
    NEW.email,
    NOW(),
    NOW()
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. CREATE TRIGGER FOR AUTO-PROFILE CREATION
-- This runs after a new user is created in auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- 8. CREATE INDEXES FOR PERFORMANCE
-- Speed up queries on commonly searched columns
CREATE INDEX IF NOT EXISTS profiles_email_idx ON public.profiles(email);
CREATE INDEX IF NOT EXISTS profiles_created_at_idx ON public.profiles(created_at);

-- =====================================================
-- VERIFICATION QUERIES
-- Run these to verify the setup worked correctly
-- =====================================================

-- Check if profiles table exists
SELECT EXISTS (
  SELECT FROM information_schema.tables 
  WHERE table_schema = 'public' 
  AND table_name = 'profiles'
);

-- Check RLS policies
SELECT 
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd
FROM pg_policies
WHERE tablename = 'profiles';

-- Check triggers
SELECT 
  trigger_name,
  event_manipulation,
  event_object_table,
  action_statement
FROM information_schema.triggers
WHERE event_object_table = 'profiles'
  OR event_object_table = 'users';

-- =====================================================
-- TEST DATA (Optional - for development only)
-- =====================================================
-- Uncomment to insert test profile (only after signing up)
-- Replace 'USER_ID_HERE' with actual UUID from auth.users

/*
INSERT INTO public.profiles (id, email, first_name, last_name, company_name)
VALUES (
  'USER_ID_HERE'::uuid,
  'test@example.com',
  'Test',
  'User',
  'Test Company'
);
*/

-- =====================================================
-- CLEANUP (Use with caution!)
-- =====================================================
-- Uncomment to remove everything and start fresh

/*
-- Drop triggers
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;

-- Drop functions
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS public.update_updated_at();

-- Drop policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can delete own profile" ON public.profiles;

-- Drop table
DROP TABLE IF EXISTS public.profiles;
*/

-- =====================================================
-- NOTES
-- =====================================================
/*
1. The profiles table is automatically populated when users sign up
   via the on_auth_user_created trigger.

2. If you need to manually create a profile for existing users:
   INSERT INTO profiles (id, email) 
   SELECT id, email FROM auth.users 
   WHERE id NOT IN (SELECT id FROM profiles);

3. The RLS policies ensure that:
   - Users can only see their own profile
   - Users can only update their own data
   - No user can access another user's data

4. To add more fields to profiles, use:
   ALTER TABLE profiles ADD COLUMN new_field_name TEXT;

5. For production, consider adding:
   - Phone number field
   - Address fields
   - Role/permissions field
   - Last login timestamp
   - Account status (active/suspended)

6. Remember to set up email templates in:
   Supabase Dashboard → Authentication → Email Templates
*/
