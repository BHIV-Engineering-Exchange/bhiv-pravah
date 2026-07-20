-- Finalize Dynamic Study Fields System
-- Run this in your Supabase SQL Editor to complete the migration

-- Step 1: Ensure all required columns exist in study_fields table
DO $$
BEGIN
    -- Ensure field_id column exists and is properly set
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'field_id') THEN
        ALTER TABLE study_fields ADD COLUMN field_id TEXT;
        UPDATE study_fields SET field_id = id WHERE field_id IS NULL;
        ALTER TABLE study_fields ALTER COLUMN field_id SET NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_study_fields_field_id_unique ON study_fields(field_id);
    END IF;
    
    -- Ensure icon column exists
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'icon') THEN
        ALTER TABLE study_fields ADD COLUMN icon TEXT DEFAULT '📚';
    END IF;
    
    -- Ensure color column exists
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'color') THEN
        ALTER TABLE study_fields ADD COLUMN color TEXT DEFAULT 'text-gray-400 bg-gray-400/10 border-gray-400/20';
    END IF;
    
    -- Ensure is_active column exists
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'is_active') THEN
        ALTER TABLE study_fields ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- Step 2: Update existing records with proper field_id, icons, and colors
UPDATE study_fields 
SET 
  field_id = COALESCE(field_id, id),
  icon = CASE 
    WHEN COALESCE(field_id, id) = 'stem' THEN '🔬'
    WHEN COALESCE(field_id, id) = 'business' THEN '💼'
    WHEN COALESCE(field_id, id) = 'social_sciences' THEN '🏛️'
    WHEN COALESCE(field_id, id) = 'health_medicine' THEN '⚕️'
    WHEN COALESCE(field_id, id) = 'creative_arts' THEN '🎨'
    WHEN COALESCE(field_id, id) = 'other' THEN '📚'
    ELSE COALESCE(icon, '📚')
  END,
  color = CASE 
    WHEN COALESCE(field_id, id) = 'stem' THEN 'text-blue-400 bg-blue-400/10 border-blue-400/20'
    WHEN COALESCE(field_id, id) = 'business' THEN 'text-green-400 bg-green-400/10 border-green-400/20'
    WHEN COALESCE(field_id, id) = 'social_sciences' THEN 'text-purple-400 bg-purple-400/10 border-purple-400/20'
    WHEN COALESCE(field_id, id) = 'health_medicine' THEN 'text-red-400 bg-red-400/10 border-red-400/20'
    WHEN COALESCE(field_id, id) = 'creative_arts' THEN 'text-pink-400 bg-pink-400/10 border-pink-400/20'
    WHEN COALESCE(field_id, id) = 'other' THEN 'text-gray-400 bg-gray-400/10 border-gray-400/20'
    ELSE COALESCE(color, 'text-gray-400 bg-gray-400/10 border-gray-400/20')
  END,
  is_active = COALESCE(is_active, true),
  updated_at = NOW()
WHERE field_id IS NULL 
   OR icon IS NULL 
   OR icon = '' 
   OR color IS NULL 
   OR color = '' 
   OR is_active IS NULL;

-- Step 3: Insert any missing default fields
INSERT INTO study_fields (field_id, name, icon, description, color, is_active, created_at, updated_at)
VALUES 
  ('stem', 'STEM', '🔬', 'Science, Technology, Engineering, and Mathematics', 'text-blue-400 bg-blue-400/10 border-blue-400/20', true, NOW(), NOW()),
  ('business', 'Business', '💼', 'Business and Economics', 'text-green-400 bg-green-400/10 border-green-400/20', true, NOW(), NOW()),
  ('social_sciences', 'Social Sciences', '🏛️', 'Social Sciences and Humanities', 'text-purple-400 bg-purple-400/10 border-purple-400/20', true, NOW(), NOW()),
  ('health_medicine', 'Health & Medicine', '⚕️', 'Healthcare and Medical Sciences', 'text-red-400 bg-red-400/10 border-red-400/20', true, NOW(), NOW()),
  ('creative_arts', 'Creative Arts', '🎨', 'Arts, Design, and Creative Fields', 'text-pink-400 bg-pink-400/10 border-pink-400/20', true, NOW(), NOW())
ON CONFLICT (field_id) DO UPDATE SET
  name = EXCLUDED.name,
  icon = EXCLUDED.icon,
  description = EXCLUDED.description,
  color = EXCLUDED.color,
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

-- Step 4: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_study_fields_field_id ON study_fields(field_id);
CREATE INDEX IF NOT EXISTS idx_study_fields_active ON study_fields(is_active);
CREATE INDEX IF NOT EXISTS idx_study_fields_name ON study_fields(name);

-- Step 5: Update RLS policies for full dynamic access
DROP POLICY IF EXISTS "Allow all operations on study_fields for development" ON study_fields;
DROP POLICY IF EXISTS "Anyone can view study fields" ON study_fields;
DROP POLICY IF EXISTS "Allow all operations for development" ON study_fields;

-- Create comprehensive RLS policy for development
CREATE POLICY "Allow all operations on study_fields for development" ON study_fields
    FOR ALL TO PUBLIC USING (true);

-- Step 6: Ensure updated_at trigger exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_study_fields_updated_at ON study_fields;
CREATE TRIGGER update_study_fields_updated_at 
    BEFORE UPDATE ON study_fields 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Step 7: Clean up any orphaned question field mappings
DELETE FROM question_field_mapping 
WHERE field_id NOT IN (SELECT field_id FROM study_fields WHERE is_active = true);

-- Step 8: Verification and final status
SELECT 
  'Dynamic Fields Migration Complete!' as status,
  COUNT(*) as total_fields,
  COUNT(CASE WHEN field_id IS NOT NULL THEN 1 END) as fields_with_field_id,
  COUNT(CASE WHEN icon IS NOT NULL AND icon != '' THEN 1 END) as fields_with_icon,
  COUNT(CASE WHEN color IS NOT NULL AND color != '' THEN 1 END) as fields_with_color,
  COUNT(CASE WHEN is_active = true THEN 1 END) as active_fields
FROM study_fields;

-- Show current field structure
SELECT 
  field_id,
  name,
  icon,
  description,
  color,
  is_active,
  created_at
FROM study_fields 
WHERE is_active = true
ORDER BY created_at;

-- Show question field mapping counts
SELECT 
  sf.field_id,
  sf.name,
  sf.icon,
  COUNT(qfm.question_id) as question_count
FROM study_fields sf
LEFT JOIN question_field_mapping qfm ON sf.field_id = qfm.field_id
WHERE sf.is_active = true
GROUP BY sf.field_id, sf.name, sf.icon
ORDER BY sf.created_at;

-- Success message
SELECT 'Dynamic Study Fields system is now fully operational! 🎉' as final_status;