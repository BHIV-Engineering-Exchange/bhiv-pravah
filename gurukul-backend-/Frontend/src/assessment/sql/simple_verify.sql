-- ========================================
-- SIMPLE VERIFICATION (Compatible with older PostgreSQL)
-- ========================================

-- Count domains
SELECT COUNT(*) as domain_count 
FROM study_fields 
WHERE is_active = true;
-- Expected: 13

-- Count questions  
SELECT COUNT(*) as question_count
FROM question_banks
WHERE is_active = true;
-- Expected: 70

-- List all domains
SELECT field_id, field_name, short_name
FROM study_fields
WHERE is_active = true
ORDER BY field_id;
-- Expected: 13 rows (IoT, Blockchain, Robotics, etc.)

-- Count questions per domain
SELECT category, COUNT(*) as count
FROM question_banks
WHERE is_active = true
GROUP BY category
ORDER BY category;
-- Expected: 13 categories, 4-6 questions each

-- Final check
SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM study_fields WHERE is_active = true) = 13
         AND (SELECT COUNT(*) FROM question_banks WHERE is_active = true) = 70
        THEN '✅ SUCCESS'
        ELSE '❌ FAILED'
    END as status;
