-- ================================================================
-- FIX QUESTION CATEGORIES RLS POLICIES
-- ================================================================
-- This script adds missing RLS policies to allow admin operations
-- on the question_categories table (INSERT, UPDATE, DELETE)
-- ================================================================

-- Drop ALL existing policies to ensure clean slate
DROP POLICY IF EXISTS "Allow public to read active question categories" ON question_categories;
DROP POLICY IF EXISTS "Allow authenticated users to read all question categories" ON question_categories;
DROP POLICY IF EXISTS "Allow all users to insert question categories" ON question_categories;
DROP POLICY IF EXISTS "Allow authenticated users to insert question categories" ON question_categories;
DROP POLICY IF EXISTS "Allow all users to update question categories" ON question_categories;
DROP POLICY IF EXISTS "Allow authenticated users to update question categories" ON question_categories;
DROP POLICY IF EXISTS "Allow all users to delete non-system question categories" ON question_categories;
DROP POLICY IF EXISTS "Allow authenticated users to delete non-system question categories" ON question_categories;

-- ================================================================
-- CREATE COMPREHENSIVE RLS POLICIES
-- ================================================================

-- Policy 1: Allow everyone to read active categories
CREATE POLICY "Allow public to read active question categories" 
ON question_categories
FOR SELECT 
USING (is_active = true);

-- Policy 2: Allow authenticated users to read all categories
CREATE POLICY "Allow authenticated users to read all question categories" 
ON question_categories
FOR SELECT 
TO authenticated 
USING (true);

-- Policy 3: Allow all users (including anon) to INSERT new categories
-- This is needed for admin panel operations
CREATE POLICY "Allow all users to insert question categories" 
ON question_categories
FOR INSERT 
WITH CHECK (true);

-- Policy 4: Allow all users (including anon) to UPDATE categories
-- This is needed for admin panel operations including deactivation
CREATE POLICY "Allow all users to update question categories" 
ON question_categories
FOR UPDATE 
USING (true)
WITH CHECK (true);

-- Policy 5: Allow all users (including anon) to DELETE non-system categories
-- This is needed for admin panel operations
CREATE POLICY "Allow all users to delete non-system question categories" 
ON question_categories
FOR DELETE 
USING (is_system = false);

-- ================================================================
-- GRANT NECESSARY PERMISSIONS
-- ================================================================

-- Grant permissions to all users (anon and authenticated)
GRANT SELECT ON question_categories TO anon;
GRANT INSERT ON question_categories TO anon;
GRANT UPDATE ON question_categories TO anon;
GRANT DELETE ON question_categories TO anon;

GRANT SELECT ON question_categories TO authenticated;
GRANT INSERT ON question_categories TO authenticated;
GRANT UPDATE ON question_categories TO authenticated;
GRANT DELETE ON question_categories TO authenticated;

-- Grant sequence permissions for INSERT operations
GRANT USAGE, SELECT ON SEQUENCE question_categories_id_seq TO anon;
GRANT USAGE, SELECT ON SEQUENCE question_categories_id_seq TO authenticated;

-- Keep existing permissions for service_role
GRANT ALL ON question_categories TO service_role;
GRANT USAGE, SELECT ON SEQUENCE question_categories_id_seq TO service_role;

-- ================================================================
-- VERIFICATION
-- ================================================================

-- Display all policies on question_categories table
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'question_categories'
ORDER BY policyname;

-- Display permissions
SELECT 
    grantee,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_name = 'question_categories'
ORDER BY grantee, privilege_type;

-- ================================================================
-- COMPLETION MESSAGE
-- ================================================================

SELECT 'Question Categories RLS Policies Fixed! ✅' as status,
       'Authenticated users can now INSERT, UPDATE, and DELETE categories' as message;
