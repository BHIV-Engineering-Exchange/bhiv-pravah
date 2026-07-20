-- Complete fix for study_fields table constraints
-- Run this in your Supabase SQL Editor

-- Step 1: Check current table structure and constraints
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'study_fields' 
ORDER BY ordinal_position;

-- Step 2: Add all missing columns first
DO $$
BEGIN
    -- Add field_id column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'field_id') THEN
        ALTER TABLE study_fields ADD COLUMN field_id TEXT;
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
END $$;

-- Step 3: Update existing records to fill in missing values
UPDATE study_fields 
SET 
  field_id = COALESCE(field_id, id),
  short_name = CASE 
    WHEN short_name IS NULL THEN
      CASE 
        WHEN COALESCE(field_id, id) = 'stem' THEN 'STEM'
        WHEN COALESCE(field_id, id) = 'business' THEN 'Business'
        WHEN COALESCE(field_id, id) = 'social_sciences' THEN 'Social Sciences'
        WHEN COALESCE(field_id, id) = 'health_medicine' THEN 'Health & Medicine'
        WHEN COALESCE(field_id, id) = 'creative_arts' THEN 'Creative Arts'
        WHEN COALESCE(field_id, id) = 'other' THEN 'Other'
        ELSE COALESCE(name, 'Unknown')
      END
    ELSE short_name
  END,
  icon = CASE 
    WHEN icon IS NULL OR icon = '' THEN
      CASE 
        WHEN COALESCE(field_id, id) = 'stem' THEN '🔬'
        WHEN COALESCE(field_id, id) = 'business' THEN '💼'
        WHEN COALESCE(field_id, id) = 'social_sciences' THEN '🏛️'
        WHEN COALESCE(field_id, id) = 'health_medicine' THEN '⚕️'
        WHEN COALESCE(field_id, id) = 'creative_arts' THEN '🎨'
        WHEN COALESCE(field_id, id) = 'other' THEN '📚'
        ELSE '📚'
      END
    ELSE icon
  END,
  color = CASE 
    WHEN color IS NULL OR color = '' THEN
      CASE 
        WHEN COALESCE(field_id, id) = 'stem' THEN 'text-blue-400 bg-blue-400/10 border-blue-400/20'
        WHEN COALESCE(field_id, id) = 'business' THEN 'text-green-400 bg-green-400/10 border-green-400/20'
        WHEN COALESCE(field_id, id) = 'social_sciences' THEN 'text-purple-400 bg-purple-400/10 border-purple-400/20'
        WHEN COALESCE(field_id, id) = 'health_medicine' THEN 'text-red-400 bg-red-400/10 border-red-400/20'
        WHEN COALESCE(field_id, id) = 'creative_arts' THEN 'text-pink-400 bg-pink-400/10 border-pink-400/20'
        WHEN COALESCE(field_id, id) = 'other' THEN 'text-gray-400 bg-gray-400/10 border-gray-400/20'
        ELSE 'text-gray-400 bg-gray-400/10 border-gray-400/20'
      END
    ELSE color
  END,
  is_active = COALESCE(is_active, true),
  updated_at = NOW();

-- Step 4: Now set NOT NULL constraints after filling in values
DO $$
BEGIN
    -- Make field_id NOT NULL if it isn't already
    IF EXISTS (SELECT FROM information_schema.columns 
              WHERE table_name = 'study_fields' 
              AND column_name = 'field_id' 
              AND is_nullable = 'YES') THEN
        ALTER TABLE study_fields ALTER COLUMN field_id SET NOT NULL;
        RAISE NOTICE 'Set field_id to NOT NULL';
    END IF;
    
    -- Make short_name NOT NULL if it isn't already
    IF EXISTS (SELECT FROM information_schema.columns 
              WHERE table_name = 'study_fields' 
              AND column_name = 'short_name' 
              AND is_nullable = 'YES') THEN
        ALTER TABLE study_fields ALTER COLUMN short_name SET NOT NULL;
        RAISE NOTICE 'Set short_name to NOT NULL';
    END IF;
END $$;

-- Step 5: Insert missing default fields with all required columns
DO $$
DECLARE
    id_data_type TEXT;
BEGIN
    -- Get the data type of the id column
    SELECT data_type INTO id_data_type
    FROM information_schema.columns 
    WHERE table_name = 'study_fields' AND column_name = 'id';
    
    IF id_data_type = 'text' THEN
        -- If id is TEXT, use field_id as id value
        INSERT INTO study_fields (id, field_id, name, short_name, icon, description, color, is_active, created_at, updated_at)
        VALUES 
          ('stem', 'stem', 'STEM', 'STEM', '🔬', 'Science, Technology, Engineering, and Mathematics', 'text-blue-400 bg-blue-400/10 border-blue-400/20', true, NOW(), NOW()),
          ('business', 'business', 'Business', 'Business', '💼', 'Business and Economics', 'text-green-400 bg-green-400/10 border-green-400/20', true, NOW(), NOW()),
          ('social_sciences', 'social_sciences', 'Social Sciences', 'Social Sciences', '🏛️', 'Social Sciences and Humanities', 'text-purple-400 bg-purple-400/10 border-purple-400/20', true, NOW(), NOW()),
          ('health_medicine', 'health_medicine', 'Health & Medicine', 'Health & Medicine', '⚕️', 'Healthcare and Medical Sciences', 'text-red-400 bg-red-400/10 border-red-400/20', true, NOW(), NOW()),
          ('creative_arts', 'creative_arts', 'Creative Arts', 'Creative Arts', '🎨', 'Arts, Design, and Creative Fields', 'text-pink-400 bg-pink-400/10 border-pink-400/20', true, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
          field_id = EXCLUDED.field_id,
          name = EXCLUDED.name,
          short_name = EXCLUDED.short_name,
          icon = EXCLUDED.icon,
          description = EXCLUDED.description,
          color = EXCLUDED.color,
          is_active = EXCLUDED.is_active,
          updated_at = NOW();
    ELSE
        -- If id is UUID, let it auto-generate
        INSERT INTO study_fields (field_id, name, short_name, icon, description, color, is_active, created_at, updated_at)
        VALUES 
          ('stem', 'STEM', 'STEM', '🔬', 'Science, Technology, Engineering, and Mathematics', 'text-blue-400 bg-blue-400/10 border-blue-400/20', true, NOW(), NOW()),
          ('business', 'Business', 'Business', '💼', 'Business and Economics', 'text-green-400 bg-green-400/10 border-green-400/20', true, NOW(), NOW()),
          ('social_sciences', 'Social Sciences', 'Social Sciences', '🏛️', 'Social Sciences and Humanities', 'text-purple-400 bg-purple-400/10 border-purple-400/20', true, NOW(), NOW()),
          ('health_medicine', 'Health & Medicine', 'Health & Medicine', '⚕️', 'Healthcare and Medical Sciences', 'text-red-400 bg-red-400/10 border-red-400/20', true, NOW(), NOW()),
          ('creative_arts', 'Creative Arts', 'Creative Arts', '🎨', 'Arts, Design, and Creative Fields', 'text-pink-400 bg-pink-400/10 border-pink-400/20', true, NOW(), NOW())
        ON CONFLICT (field_id) DO UPDATE SET
          name = EXCLUDED.name,
          short_name = EXCLUDED.short_name,
          icon = EXCLUDED.icon,
          description = EXCLUDED.description,
          color = EXCLUDED.color,
          is_active = EXCLUDED.is_active,
          updated_at = NOW();
    END IF;
END $$;

-- Step 6: Create necessary indexes
CREATE INDEX IF NOT EXISTS idx_study_fields_field_id ON study_fields(field_id);
CREATE INDEX IF NOT EXISTS idx_study_fields_active ON study_fields(is_active);
CREATE INDEX IF NOT EXISTS idx_study_fields_name ON study_fields(name);
CREATE INDEX IF NOT EXISTS idx_study_fields_short_name ON study_fields(short_name);

-- Step 7: Create unique constraint on field_id if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_constraint WHERE conname = 'study_fields_field_id_key') THEN
        ALTER TABLE study_fields ADD CONSTRAINT study_fields_field_id_key UNIQUE (field_id);
        RAISE NOTICE 'Added unique constraint on field_id';
    END IF;
END $$;

-- Step 8: Update RLS policies
DROP POLICY IF EXISTS "Allow all operations on study_fields for development" ON study_fields;
CREATE POLICY "Allow all operations on study_fields for development" ON study_fields
    FOR ALL TO PUBLIC USING (true);

-- Step 9: Ensure updated_at trigger exists
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

-- Step 10: Final verification
SELECT 
  'Migration Complete!' as status,
  COUNT(*) as total_fields,
  COUNT(CASE WHEN id IS NOT NULL THEN 1 END) as fields_with_id,
  COUNT(CASE WHEN field_id IS NOT NULL THEN 1 END) as fields_with_field_id,
  COUNT(CASE WHEN short_name IS NOT NULL THEN 1 END) as fields_with_short_name,
  COUNT(CASE WHEN icon IS NOT NULL AND icon != '' THEN 1 END) as fields_with_icon,
  COUNT(CASE WHEN color IS NOT NULL AND color != '' THEN 1 END) as fields_with_color,
  COUNT(CASE WHEN is_active = true THEN 1 END) as active_fields
FROM study_fields;

-- Show final table structure
SELECT 
  id,
  field_id,
  name,
  short_name,
  icon,
  description,
  color,
  is_active,
  created_at
FROM study_fields 
WHERE is_active = true
ORDER BY created_at;

-- Show table constraints
SELECT 
    tc.constraint_name, 
    tc.constraint_type,
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_name = 'study_fields'
ORDER BY tc.constraint_type, kcu.column_name;

SELECT 'Study fields table completely fixed with all constraints! 🎉' as final_status;