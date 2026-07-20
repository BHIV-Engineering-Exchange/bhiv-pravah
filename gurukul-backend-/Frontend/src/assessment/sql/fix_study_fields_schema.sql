-- Quick fix for study_fields table schema
-- Run this in your Supabase SQL Editor

-- First, let's check the current table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'study_fields' 
ORDER BY ordinal_position;

-- Add missing columns if they don't exist
DO $$
BEGIN
    -- Add field_id column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'field_id') THEN
        ALTER TABLE study_fields ADD COLUMN field_id TEXT UNIQUE;
        RAISE NOTICE 'Added field_id column';
    END IF;
    
    -- Add short_name column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'short_name') THEN
        ALTER TABLE study_fields ADD COLUMN short_name TEXT;
        RAISE NOTICE 'Added short_name column';
    END IF;
    
    -- Add icon column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'icon') THEN
        ALTER TABLE study_fields ADD COLUMN icon TEXT DEFAULT '📚';
        RAISE NOTICE 'Added icon column';
    END IF;
    
    -- Add color column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'color') THEN
        ALTER TABLE study_fields ADD COLUMN color TEXT DEFAULT 'text-gray-400 bg-gray-400/10 border-gray-400/20';
        RAISE NOTICE 'Added color column';
    END IF;
    
    -- Add is_active column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'is_active') THEN
        ALTER TABLE study_fields ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
        RAISE NOTICE 'Added is_active column';
    END IF;
    
    -- Add subcategories column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'subcategories') THEN
        ALTER TABLE study_fields ADD COLUMN subcategories JSONB DEFAULT '[]';
        RAISE NOTICE 'Added subcategories column';
    END IF;
    
    -- Add question_weights column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'question_weights') THEN
        ALTER TABLE study_fields ADD COLUMN question_weights JSONB DEFAULT '{}';
        RAISE NOTICE 'Added question_weights column';
    END IF;
    
    -- Add difficulty_distribution column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'difficulty_distribution') THEN
        ALTER TABLE study_fields ADD COLUMN difficulty_distribution JSONB DEFAULT '{}';
        RAISE NOTICE 'Added difficulty_distribution column';
    END IF;
END $$;

-- Update existing records to ensure they have values for new fields
UPDATE study_fields 
SET 
  field_id = COALESCE(field_id, LOWER(REPLACE(name, ' ', '_'))),
  short_name = COALESCE(short_name, name),
  icon = COALESCE(icon, '📚'),
  color = COALESCE(color, 'text-gray-400 bg-gray-400/10 border-gray-400/20'),
  is_active = COALESCE(is_active, true),
  subcategories = COALESCE(subcategories, '[]'::jsonb),
  question_weights = COALESCE(question_weights, '{}'::jsonb),
  difficulty_distribution = COALESCE(difficulty_distribution, '{}'::jsonb),
  updated_at = NOW()
WHERE field_id IS NULL OR short_name IS NULL OR icon IS NULL OR color IS NULL;

-- Make required fields NOT NULL
ALTER TABLE study_fields ALTER COLUMN field_id SET NOT NULL;
ALTER TABLE study_fields ALTER COLUMN short_name SET NOT NULL;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_study_fields_field_id ON study_fields(field_id);
CREATE INDEX IF NOT EXISTS idx_study_fields_active ON study_fields(is_active);

-- Update RLS policies to allow all operations for development
DROP POLICY IF EXISTS "Allow all operations on study_fields for development" ON study_fields;
CREATE POLICY "Allow all operations on study_fields for development" ON study_fields
    FOR ALL TO PUBLIC USING (true);

-- Show final table structure
SELECT 
  'Final table structure:' as status,
  array_agg(column_name ORDER BY ordinal_position) as columns
FROM information_schema.columns 
WHERE table_name = 'study_fields';

-- Show existing data
SELECT 
  'Existing data:' as status,
  field_id,
  name,
  short_name,
  icon,
  is_active
FROM study_fields 
ORDER BY created_at;

SELECT 'Schema fix complete! ✅' as final_status;