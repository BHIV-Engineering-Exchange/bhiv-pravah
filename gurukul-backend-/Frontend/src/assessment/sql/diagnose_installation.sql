-- ========================================
-- DIAGNOSTIC SCRIPT - Run if verification fails
-- ========================================
-- This will help identify what went wrong

-- Step 1: Check if study_fields table exists and has data
SELECT 
    'CHECK 1: study_fields table' as diagnostic,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_rows
FROM study_fields;

-- Step 2: List all domains in study_fields
SELECT 
    'CHECK 2: Domain list' as diagnostic,
    field_id,
    field_name,
    short_name,
    is_active
FROM study_fields
ORDER BY field_id;

-- Step 3: Check if question_banks table exists and has data
SELECT 
    'CHECK 3: question_banks table' as diagnostic,
    COUNT(*) as total_questions,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_questions
FROM question_banks;

-- Step 4: Check question categories (should match domain names)
SELECT 
    'CHECK 4: Question categories' as diagnostic,
    category,
    COUNT(*) as question_count
FROM question_banks
WHERE is_active = true
GROUP BY category
ORDER BY category;

-- Step 5: Check for questions WITHOUT category
SELECT 
    'CHECK 5: Questions missing category' as diagnostic,
    COUNT(*) as count_without_category
FROM question_banks
WHERE category IS NULL OR category = '';

-- Step 6: Check question_categories table
SELECT 
    'CHECK 6: question_categories table' as diagnostic,
    COUNT(*) as total_categories
FROM question_categories;

-- Step 7: List all categories
SELECT 
    'CHECK 7: Category list' as diagnostic,
    category_id,
    category_name,
    is_active
FROM question_categories
ORDER BY category_id;

-- Step 8: Check question_field_mapping table
SELECT 
    'CHECK 8: question_field_mapping table' as diagnostic,
    COUNT(*) as total_mappings
FROM question_field_mapping;

-- Step 9: Sample of question_field_mapping
SELECT 
    'CHECK 9: Sample mappings' as diagnostic,
    qfm.mapping_id,
    qfm.question_id,
    qfm.field_id,
    sf.short_name as domain_name,
    LEFT(qb.question_text, 50) as question_preview
FROM question_field_mapping qfm
LEFT JOIN study_fields sf ON qfm.field_id = sf.field_id
LEFT JOIN question_banks qb ON qfm.question_id = qb.question_id
LIMIT 10;

-- Step 10: Summary Report
SELECT 
    'SUMMARY REPORT' as diagnostic,
    (SELECT COUNT(*) FROM study_fields WHERE is_active = true) as domains_count,
    (SELECT COUNT(*) FROM question_banks WHERE is_active = true) as questions_count,
    (SELECT COUNT(*) FROM question_categories) as categories_count,
    (SELECT COUNT(*) FROM question_field_mapping) as mappings_count;

-- Step 11: Identify the specific problem
SELECT 
    'DIAGNOSIS' as result,
    CASE 
        WHEN (SELECT COUNT(*) FROM study_fields WHERE is_active = true) < 13 
        THEN '❌ PROBLEM: study_fields has fewer than 13 domains. Run migrate_to_13_domains.sql again.'
        
        WHEN (SELECT COUNT(*) FROM question_banks WHERE is_active = true) < 70
        THEN '❌ PROBLEM: question_banks has fewer than 70 questions. Run insert_70_domain_questions.sql again.'
        
        WHEN (SELECT COUNT(*) FROM question_banks WHERE is_active = true) = 0
        THEN '❌ PROBLEM: No questions found. Run insert_70_domain_questions.sql.'
        
        WHEN (SELECT COUNT(*) FROM study_fields WHERE is_active = true) = 0
        THEN '❌ PROBLEM: No domains found. Run migrate_to_13_domains.sql.'
        
        WHEN (SELECT COUNT(*) FROM study_fields WHERE is_active = true) = 13
         AND (SELECT COUNT(*) FROM question_banks WHERE is_active = true) = 70
        THEN '✅ SUCCESS: All data present! Re-run verify_installation.sql.'
        
        ELSE '⚠️ UNKNOWN ISSUE: Check the output above for details.'
    END as diagnosis_result;
