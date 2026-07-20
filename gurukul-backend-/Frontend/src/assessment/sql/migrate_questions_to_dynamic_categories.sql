-- Migration Script: Questions to Dynamic Categories
-- This script ensures all existing questions are properly migrated to use dynamic categories

-- Check current state of question_banks table
DO $$
DECLARE
    column_exists BOOLEAN;
    migration_needed BOOLEAN := false;
    total_questions INTEGER;
    unmapped_questions INTEGER;
BEGIN
    -- Check if category_id column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'question_banks' AND column_name = 'category_id'
    ) INTO column_exists;
    
    -- Get total questions count
    SELECT COUNT(*) INTO total_questions FROM question_banks;
    
    RAISE NOTICE 'Found % total questions in database', total_questions;
    
    IF NOT column_exists THEN
        RAISE NOTICE 'category_id column does not exist - migration needed';
        migration_needed := true;
    ELSE
        -- Check how many questions need migration
        SELECT COUNT(*) INTO unmapped_questions 
        FROM question_banks 
        WHERE category_id IS NULL OR category_id = '';
        
        RAISE NOTICE 'Found % questions without category_id mapping', unmapped_questions;
        
        IF unmapped_questions > 0 THEN
            migration_needed := true;
        END IF;
    END IF;
    
    -- Perform migration if needed
    IF migration_needed THEN
        RAISE NOTICE 'Starting question category migration...';
        
        -- Add category_id column if it doesn't exist
        IF NOT column_exists THEN
            ALTER TABLE question_banks ADD COLUMN category_id VARCHAR(100);
            CREATE INDEX IF NOT EXISTS idx_question_banks_category_id ON question_banks(category_id);
            RAISE NOTICE 'Added category_id column to question_banks table';
        END IF;
        
        -- Migrate existing questions based on their current 'category' field
        UPDATE question_banks 
        SET category_id = CASE 
            WHEN LOWER(TRIM(category)) IN ('coding', 'code', 'programming') THEN 'coding'
            WHEN LOWER(TRIM(category)) IN ('logic', 'logical reasoning', 'reasoning') THEN 'logic'
            WHEN LOWER(TRIM(category)) IN ('mathematics', 'math', 'maths', 'mathematical') THEN 'mathematics'
            WHEN LOWER(TRIM(category)) IN ('language', 'english', 'communication', 'linguistics') THEN 'language'
            WHEN LOWER(TRIM(category)) IN ('culture', 'cultural', 'society', 'social') THEN 'culture'
            WHEN LOWER(TRIM(category)) IN ('vedic knowledge', 'vedic', 'traditional', 'ancient') THEN 'vedic_knowledge'
            WHEN LOWER(TRIM(category)) IN ('current affairs', 'current', 'affairs', 'news', 'general knowledge') THEN 'current_affairs'
            WHEN LOWER(TRIM(category)) IN ('science', 'scientific') THEN 'science'
            WHEN LOWER(TRIM(category)) IN ('history', 'historical') THEN 'history'
            ELSE 'logic' -- Default fallback
        END
        WHERE category_id IS NULL OR category_id = '';
        
        -- Get count of migrated questions
        SELECT COUNT(*) INTO unmapped_questions FROM question_banks WHERE category_id IS NOT NULL;
        RAISE NOTICE 'Successfully migrated % questions to use dynamic categories', unmapped_questions;
        
        -- Add foreign key constraint if it doesn't exist
        BEGIN
            ALTER TABLE question_banks 
            ADD CONSTRAINT fk_question_banks_category 
            FOREIGN KEY (category_id) REFERENCES question_categories(category_id) ON DELETE CASCADE;
            RAISE NOTICE 'Added foreign key constraint between question_banks and question_categories';
        EXCEPTION
            WHEN duplicate_object THEN
                RAISE NOTICE 'Foreign key constraint already exists';
        END;
        
    ELSE
        RAISE NOTICE 'No migration needed - all questions already have dynamic categories';
    END IF;
END
$$;

-- Verify migration results
SELECT 
    'Migration Verification' as status,
    COUNT(*) as total_questions,
    COUNT(*) FILTER (WHERE category_id IS NOT NULL) as migrated_questions,
    COUNT(*) FILTER (WHERE category_id IS NULL) as unmigrated_questions
FROM question_banks;

-- Show questions per category after migration
SELECT 
    qc.name as category_name,
    qc.category_id,
    COUNT(qb.question_id) as question_count,
    qc.is_system,
    qc.weight_percentage
FROM question_categories qc
LEFT JOIN question_banks qb ON qc.category_id = qb.category_id
WHERE qc.is_active = true
GROUP BY qc.id, qc.name, qc.category_id, qc.is_system, qc.weight_percentage, qc.display_order
ORDER BY qc.display_order;

-- Check for any questions with invalid category_id
SELECT 
    'Orphaned Questions Check' as status,
    COUNT(*) as orphaned_count
FROM question_banks qb
LEFT JOIN question_categories qc ON qb.category_id = qc.category_id
WHERE qc.category_id IS NULL AND qb.category_id IS NOT NULL;

-- Show any questions that couldn't be mapped
SELECT 
    question_id,
    category as original_category,
    category_id as mapped_category_id,
    question_text,
    created_by
FROM question_banks 
WHERE category_id IS NULL 
LIMIT 10;

-- Update statistics
ANALYZE question_banks;
ANALYZE question_categories;

RAISE NOTICE 'Question migration to dynamic categories completed successfully!';