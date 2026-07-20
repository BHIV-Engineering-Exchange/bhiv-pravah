-- Fix study_fields table ID constraint error
-- Run this in your Supabase SQL Editor

-- Step 1: Check current table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'study_fields' 
ORDER BY ordinal_position;

-- Step 2: Fix the ID issue based on table structure
DO $$
DECLARE
    id_data_type TEXT;
BEGIN
    -- Get the data type of the id column
    SELECT data_type INTO id_data_type
    FROM information_schema.columns 
    WHERE table_name = 'study_fields' AND column_name = 'id';
    
    RAISE NOTICE 'ID column data type: %', id_data_type;
    
    -- Handle different ID column types
    IF id_data_type = 'text' THEN
        -- If id is TEXT, use field_id as id value
        RAISE NOTICE 'Handling TEXT id column';
        
        -- Update existing records to have proper id values
        UPDATE study_fields 
        SET id = field_id 
        WHERE id IS NULL AND field_id IS NOT NULL;
        
        -- Insert missing default fields with explicit id
        INSERT INTO study_fields (id, field_id, name, icon, description, color, is_active, created_at, updated_at)
        VALUES 
          ('stem', 'stem', 'STEM', '🔬', 'Science, Technology, Engineering, and Mathematics', 'text-blue-400 bg-blue-400/10 border-blue-400/20', true, NOW(), NOW()),
          ('business', 'business', 'Business', '💼', 'Business and Economics', 'text-green-400 bg-green-400/10 border-green-400/20', true, NOW(), NOW()),
          ('social_sciences', 'social_sciences', 'Social Sciences', '🏛️', 'Social Sciences and Humanities', 'text-purple-400 bg-purple-400/10 border-purple-400/20', true, NOW(), NOW()),
          ('health_medicine', 'health_medicine', 'Health & Medicine', '⚕️', 'Healthcare and Medical Sciences', 'text-red-400 bg-red-400/10 border-red-400/20', true, NOW(), NOW()),
          ('creative_arts', 'creative_arts', 'Creative Arts', '🎨', 'Arts, Design, and Creative Fields', 'text-pink-400 bg-pink-400/10 border-pink-400/20', true, NOW(), NOW())
        ON CONFLICT (id) DO UPDATE SET
          field_id = EXCLUDED.field_id,
          name = EXCLUDED.name,
          icon = EXCLUDED.icon,
          description = EXCLUDED.description,
          color = EXCLUDED.color,
          is_active = EXCLUDED.is_active,
          updated_at = NOW();
          
    ELSIF id_data_type = 'uuid' THEN
        -- If id is UUID, let it auto-generate but ensure field_id is unique
        RAISE NOTICE 'Handling UUID id column';
        
        -- Insert missing default fields (UUID will auto-generate)
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
    ELSE
        RAISE NOTICE 'Unknown id column type: %', id_data_type;
    END IF;
END $$;

-- Step 3: Ensure all required columns exist and have proper values
DO $$
BEGIN
    -- Add field_id column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'field_id') THEN
        ALTER TABLE study_fields ADD COLUMN field_id TEXT;
        UPDATE study_fields SET field_id = id WHERE field_id IS NULL;
        ALTER TABLE study_fields ALTER COLUMN field_id SET NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_study_fields_field_id_unique ON study_fields(field_id);
    END IF;
    
    -- Add icon column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'icon') THEN
        ALTER TABLE study_fields ADD COLUMN icon TEXT DEFAULT '📚';
    END IF;
    
    -- Add color column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'color') THEN
        ALTER TABLE study_fields ADD COLUMN color TEXT DEFAULT 'text-gray-400 bg-gray-400/10 border-gray-400/20';
    END IF;
    
    -- Add is_active column if missing
    IF NOT EXISTS (SELECT FROM information_schema.columns 
                  WHERE table_name = 'study_fields' AND column_name = 'is_active') THEN
        ALTER TABLE study_fields ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- Step 4: Update any records with missing values
UPDATE study_fields 
SET 
  field_id = COALESCE(field_id, id),
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
  updated_at = NOW()
WHERE field_id IS NULL 
   OR icon IS NULL 
   OR icon = '' 
   OR color IS NULL 
   OR color = '' 
   OR is_active IS NULL;

-- Step 5: Create necessary indexes
CREATE INDEX IF NOT EXISTS idx_study_fields_field_id ON study_fields(field_id);
CREATE INDEX IF NOT EXISTS idx_study_fields_active ON study_fields(is_active);
CREATE INDEX IF NOT EXISTS idx_study_fields_name ON study_fields(name);

-- Step 6: Update RLS policies
DROP POLICY IF EXISTS "Allow all operations on study_fields for development" ON study_fields;
CREATE POLICY "Allow all operations on study_fields for development" ON study_fields
    FOR ALL TO PUBLIC USING (true);

-- Step 7: Ensure updated_at trigger exists
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

-- Step 8: Verification
SELECT 
  'Migration Status' as status,
  COUNT(*) as total_fields,
  COUNT(CASE WHEN id IS NOT NULL THEN 1 END) as fields_with_id,
  COUNT(CASE WHEN field_id IS NOT NULL THEN 1 END) as fields_with_field_id,
  COUNT(CASE WHEN icon IS NOT NULL AND icon != '' THEN 1 END) as fields_with_icon,
  COUNT(CASE WHEN color IS NOT NULL AND color != '' THEN 1 END) as fields_with_color,
  COUNT(CASE WHEN is_active = true THEN 1 END) as active_fields
FROM study_fields;

-- Show final table structure
SELECT 
  id,
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

SELECT 'Study fields table successfully fixed! 🎉' as final_status;