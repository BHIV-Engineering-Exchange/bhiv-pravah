-- Add ai_enabled column to study_fields table

-- Check if ai_enabled column exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'ai_enabled') THEN
        ALTER TABLE study_fields ADD COLUMN ai_enabled BOOLEAN DEFAULT TRUE;
        RAISE NOTICE 'Added ai_enabled column to study_fields table';
    END IF;
END $$;

-- Update existing records to ensure they have ai_enabled set
UPDATE study_fields 
SET ai_enabled = TRUE
WHERE ai_enabled IS NULL;

-- Make ai_enabled NOT NULL
ALTER TABLE study_fields ALTER COLUMN ai_enabled SET NOT NULL;

-- Show final table structure
SELECT 
    'Final table structure:' as status,
    array_agg(column_name ORDER BY ordinal_position) as columns
FROM information_schema.columns 
WHERE table_name = 'study_fields';

SELECT 'AI toggle column added successfully! ✅' as final_status;