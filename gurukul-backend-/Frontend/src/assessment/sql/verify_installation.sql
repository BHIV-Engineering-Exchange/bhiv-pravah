-- ========================================
-- QUICK START: Verify 13-Domain System
-- ========================================
-- Run this script to verify the installation

-- 1. Check domains installed
SELECT 
    '✅ DOMAINS' as check_type,
    COUNT(*) as count,
    STRING_AGG(short_name, ', ' ORDER BY field_id) as domains
FROM study_fields
WHERE is_active = true;

-- 2. Check questions by domain
SELECT 
    '📊 QUESTIONS BY DOMAIN' as check_type,
    category as domain,
    COUNT(*) as total_questions,
    COUNT(CASE WHEN difficulty = 'easy' THEN 1 END) as easy,
    COUNT(CASE WHEN difficulty = 'medium' THEN 1 END) as medium,
    COUNT(CASE WHEN difficulty = 'hard' THEN 1 END) as hard
FROM question_banks
WHERE is_active = true
GROUP BY category
ORDER BY category;

-- 3. Total question count
SELECT 
    '📈 TOTAL STATS' as check_type,
    COUNT(*) as total_questions,
    COUNT(DISTINCT category) as total_domains,
    COUNT(CASE WHEN difficulty = 'easy' THEN 1 END) as total_easy,
    COUNT(CASE WHEN difficulty = 'medium' THEN 1 END) as total_medium,
    COUNT(CASE WHEN difficulty = 'hard' THEN 1 END) as total_hard
FROM question_banks
WHERE is_active = true;

-- 4. Sample questions from each domain (1 per domain)
SELECT 
    '🔍 SAMPLE QUESTIONS' as check_type,
    category as domain,
    difficulty,
    LEFT(question_text, 80) || '...' as question_preview
FROM (
    SELECT 
        category,
        difficulty,
        question_text,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY RANDOM()) as rn
    FROM question_banks
    WHERE is_active = true
) subquery
WHERE rn = 1
ORDER BY category;

-- 5. Check question-field mappings
SELECT 
    '🔗 MAPPINGS' as check_type,
    COUNT(*) as total_mappings,
    COUNT(DISTINCT question_id) as mapped_questions,
    COUNT(DISTINCT field_id) as mapped_domains
FROM question_field_mapping;

-- 6. Validate data integrity
SELECT 
    '✅ INTEGRITY CHECK' as check_type,
    CASE 
        WHEN COUNT(*) = 70 THEN '✅ All 70 questions present'
        ELSE '❌ Expected 70 questions, found ' || COUNT(*)
    END as status
FROM question_banks
WHERE is_active = true;

-- 7. Expected output summary
SELECT 
    '📋 EXPECTED CONFIGURATION' as info,
    '13 domains, 70 questions' as expected_setup,
    'IoT, Blockchain, Robotics, AI/ML/DS, Drones, Biotech, Pharma, Gaming, VR/AR, Cyber, Web, 3D, Quantum' as domain_list;

-- SUCCESS MESSAGE
SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM study_fields WHERE is_active = true) = 13
         AND (SELECT COUNT(*) FROM question_banks WHERE is_active = true) = 70
        THEN '✅✅✅ INSTALLATION SUCCESSFUL! System ready for multi-domain assessments.'
        ELSE '⚠️ Installation incomplete. Check output above for issues.'
    END as installation_status;
