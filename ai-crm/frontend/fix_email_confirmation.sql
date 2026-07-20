-- =====================================================
-- QUICK FIX: Manually Confirm Email Address
-- =====================================================
-- Run this in Supabase SQL Editor to confirm your email
-- Dashboard → SQL Editor → New Query → Paste & Run
-- =====================================================

-- Replace 'your-email@example.com' with your actual email address
UPDATE auth.users 
SET email_confirmed_at = NOW(),
    confirmed_at = NOW()
WHERE email = 'your-email@example.com';

-- =====================================================
-- Verify the update worked
-- =====================================================
SELECT 
  id,
  email,
  email_confirmed_at,
  confirmed_at,
  created_at
FROM auth.users 
WHERE email = 'your-email@example.com';

-- =====================================================
-- Alternative: Confirm ALL users (Development only!)
-- =====================================================
-- Uncomment to confirm all unconfirmed users

/*
UPDATE auth.users 
SET email_confirmed_at = NOW(),
    confirmed_at = NOW()
WHERE email_confirmed_at IS NULL;
*/

-- =====================================================
-- Check all users confirmation status
-- =====================================================
SELECT 
  email,
  CASE 
    WHEN email_confirmed_at IS NOT NULL THEN '✅ Confirmed'
    ELSE '❌ Not Confirmed'
  END as status,
  email_confirmed_at,
  created_at
FROM auth.users
ORDER BY created_at DESC;
