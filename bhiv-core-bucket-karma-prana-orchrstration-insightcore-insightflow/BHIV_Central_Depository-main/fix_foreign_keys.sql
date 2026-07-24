-- Fix for testing: Remove foreign key constraint temporarily
-- This allows testing without creating real Supabase Auth users

ALTER TABLE specs DROP CONSTRAINT IF EXISTS specs_user_id_fkey;
ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS evaluations_evaluator_id_fkey;

-- Add back as a simple UUID column without foreign key
ALTER TABLE specs ALTER COLUMN user_id TYPE UUID;
ALTER TABLE evaluations ALTER COLUMN evaluator_id TYPE UUID;

-- Test the fix
SELECT 'Foreign key constraints removed for testing' AS status;