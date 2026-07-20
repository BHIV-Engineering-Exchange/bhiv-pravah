-- Migration Script: Add Dynamic Field Management to Existing Database
-- Run this in your Supabase SQL Editor

-- Step 1: Add missing columns to existing study_fields table
DO $$
BEGIN
    -- Add field_id column if it doesn't exist
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'field_id') THEN
        ALTER TABLE study_fields ADD COLUMN field_id TEXT;
        -- Copy existing id values to field_id
        UPDATE study_fields SET field_id = id WHERE field_id IS NULL;
        -- Make field_id NOT NULL and unique
        ALTER TABLE study_fields ALTER COLUMN field_id SET NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_study_fields_field_id_unique ON study_fields(field_id);
        RAISE NOTICE 'Added field_id column and populated from existing id column';
    END IF;
    
    -- Add icon column if it doesn't exist
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'icon') THEN
        ALTER TABLE study_fields ADD COLUMN icon TEXT DEFAULT '📚';
        RAISE NOTICE 'Added icon column';
    END IF;
    
    -- Add color column if it doesn't exist
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'color') THEN
        ALTER TABLE study_fields ADD COLUMN color TEXT DEFAULT 'text-gray-400 bg-gray-400/10 border-gray-400/20';
        RAISE NOTICE 'Added color column';
    END IF;
    
    -- Add is_active column if it doesn't exist
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'is_active') THEN
        ALTER TABLE study_fields ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
        RAISE NOTICE 'Added is_active column';
    END IF;
END $$;

-- Step 2: Update existing records with proper icons and colors
UPDATE study_fields SET 
  icon = CASE 
    WHEN field_id = 'stem' OR id = 'stem' THEN '🔬'
    WHEN field_id = 'business' OR id = 'business' THEN '💼'
    WHEN field_id = 'social_sciences' OR id = 'social_sciences' THEN '🏛️'
    WHEN field_id = 'health_medicine' OR id = 'health_medicine' THEN '⚕️'
    WHEN field_id = 'creative_arts' OR id = 'creative_arts' THEN '🎨'
    WHEN field_id = 'other' OR id = 'other' THEN '📚'
    ELSE '📚'
  END,
  color = CASE 
    WHEN field_id = 'stem' OR id = 'stem' THEN 'text-blue-400 bg-blue-400/10 border-blue-400/20'
    WHEN field_id = 'business' OR id = 'business' THEN 'text-green-400 bg-green-400/10 border-green-400/20'
    WHEN field_id = 'social_sciences' OR id = 'social_sciences' THEN 'text-purple-400 bg-purple-400/10 border-purple-400/20'
    WHEN field_id = 'health_medicine' OR id = 'health_medicine' THEN 'text-red-400 bg-red-400/10 border-red-400/20'
    WHEN field_id = 'creative_arts' OR id = 'creative_arts' THEN 'text-pink-400 bg-pink-400/10 border-pink-400/20'
    WHEN field_id = 'other' OR id = 'other' THEN 'text-gray-400 bg-gray-400/10 border-gray-400/20'
    ELSE 'text-gray-400 bg-gray-400/10 border-gray-400/20'
  END,
  is_active = COALESCE(is_active, true),
  updated_at = NOW()
WHERE (icon IS NULL OR icon = '' OR icon = '📚') 
   OR (color IS NULL OR color = '' OR color = 'text-gray-400 bg-gray-400/10 border-gray-400/20')
   OR is_active IS NULL;

-- Step 3: Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_study_fields_field_id ON study_fields(field_id);
CREATE INDEX IF NOT EXISTS idx_study_fields_active ON study_fields(is_active);

-- Step 4: Update RLS policies for dynamic field management
DROP POLICY IF EXISTS "Allow all operations on study_fields for development" ON study_fields;
DROP POLICY IF EXISTS "Anyone can view study fields" ON study_fields;
DROP POLICY IF EXISTS "Allow all operations for development" ON study_fields;

-- Create comprehensive RLS policy for development
CREATE POLICY "Allow all operations on study_fields for development" ON study_fields
    FOR ALL TO PUBLIC USING (true);

-- Step 5: Ensure updated_at trigger exists
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

-- Step 6: Verify the migration
SELECT 
  'Migration Results:' as status,
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
  color,
  is_active,
  created_at
FROM study_fields 
ORDER BY created_at;

-- Success message
SELECT 'Dynamic Study Fields migration completed successfully! You can now use the enhanced Question Bank Manager.' as final_status;