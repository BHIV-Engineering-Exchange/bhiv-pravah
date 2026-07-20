-- Diagnostic script to check study_fields table structure
-- Run this in your Supabase SQL Editor first

-- 1. Check if the table exists
SELECT 
    'Table exists check' as check_type,
    CASE WHEN EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'study_fields' AND table_schema = 'public'
    ) THEN 'YES' ELSE 'NO' END as result;

-- 2. Show current table structure
SELECT 
    'Current columns' as check_type,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'study_fields' AND table_schema = 'public'
ORDER BY ordinal_position;

-- 3. Check what data currently exists
SELECT 
    'Current data' as check_type,
    COUNT(*) as total_rows
FROM study_fields;

-- 4. Show sample data (if any)
SELECT 
    'Sample data' as check_type,
    *
FROM study_fields 
LIMIT 3;

-- 5. List missing columns that the frontend expects
WITH expected_columns AS (
    SELECT unnest(ARRAY[
        'id', 'field_id', 'name', 'short_name', 'icon', 'description', 
        'color', 'is_active', 'subcategories', 'question_weights', 
        'difficulty_distribution', 'created_at', 'updated_at'
    ]) as expected_column
),
existing_columns AS (
    SELECT column_name
    FROM information_schema.columns 
    WHERE table_name = 'study_fields' AND table_schema = 'public'
)
SELECT 
    'Missing columns' as check_type,
    e.expected_column,
    CASE WHEN ex.column_name IS NULL THEN 'MISSING' ELSE 'EXISTS' END as status
FROM expected_columns e
LEFT JOIN existing_columns ex ON e.expected_column = ex.column_name
ORDER BY e.expected_column;

-- 6. Check RLS policies
SELECT 
    'RLS policies' as check_type,
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies 
WHERE tablename = 'study_fields' AND schemaname = 'public';

SELECT 'Diagnostic complete! Check the results above.' as status;