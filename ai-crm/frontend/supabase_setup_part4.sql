-- =====================================================
-- PART 4: CREATE INDEXES
-- =====================================================
-- Run this fourth in Supabase SQL Editor

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS profiles_email_idx ON public.profiles(email);
CREATE INDEX IF NOT EXISTS profiles_created_at_idx ON public.profiles(created_at);

