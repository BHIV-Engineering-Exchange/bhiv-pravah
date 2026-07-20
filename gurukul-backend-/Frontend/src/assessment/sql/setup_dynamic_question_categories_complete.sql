-- ================================================================
-- DYNAMIC QUESTION CATEGORIES - COMPLETE SETUP SCRIPT
-- ================================================================
-- Copy and paste this entire script into Supabase SQL Editor
-- This sets up the complete dynamic question categories system

-- Drop existing table if it exists (for clean installation)
-- This will also drop all associated policies automatically
DROP TABLE IF EXISTS question_categories CASCADE;

-- ================================================================
-- 1. CREATE QUESTION CATEGORIES TABLE
-- ================================================================

CREATE TABLE question_categories (
  id SERIAL PRIMARY KEY,
  category_id VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  icon VARCHAR(50),
  color VARCHAR(100),
  display_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  is_system BOOLEAN DEFAULT false, -- System categories cannot be deleted
  weight_percentage DECIMAL(5,2) DEFAULT 15.00, -- Default weight for question generation
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_question_categories_category_id ON question_categories(category_id);
CREATE INDEX idx_question_categories_active ON question_categories(is_active);
CREATE INDEX idx_question_categories_order ON question_categories(display_order);

-- ================================================================
-- 2. CREATE TRIGGER FOR AUTO-UPDATE TIMESTAMPS
-- ================================================================

CREATE OR REPLACE FUNCTION update_question_categories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_question_categories_updated_at
    BEFORE UPDATE ON question_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_question_categories_updated_at();

-- ================================================================
-- 3. INSERT DEFAULT QUESTION CATEGORIES
-- ================================================================

INSERT INTO question_categories (category_id, name, description, icon, color, display_order, is_system, weight_percentage) VALUES
('coding', 'Coding', 'Programming and software development questions', 'Code', 'text-blue-400 bg-blue-400/10 border-blue-400/20', 1, true, 25.00),
('logic', 'Logic', 'Logical reasoning and problem-solving questions', 'Brain', 'text-purple-400 bg-purple-400/10 border-purple-400/20', 2, true, 20.00),
('mathematics', 'Mathematics', 'Mathematical concepts and calculations', 'Calculator', 'text-green-400 bg-green-400/10 border-green-400/20', 3, true, 20.00),
('language', 'Language', 'Language skills and communication', 'MessageCircle', 'text-orange-400 bg-orange-400/10 border-orange-400/20', 4, true, 15.00),
('culture', 'Culture', 'Cultural knowledge and awareness', 'Globe', 'text-pink-400 bg-pink-400/10 border-pink-400/20', 5, true, 10.00),
('vedic_knowledge', 'Vedic Knowledge', 'Traditional knowledge and wisdom', 'BookOpen', 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20', 6, true, 5.00),
('current_affairs', 'Current Affairs', 'Current events and general knowledge', 'Newspaper', 'text-red-400 bg-red-400/10 border-red-400/20', 7, true, 5.00);

-- ================================================================
-- 4. SETUP QUESTION_BANKS TABLE INTEGRATION
-- ================================================================

DO $$
BEGIN
    -- Check if category_id column exists in question_banks
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'question_banks' AND column_name = 'category_id'
    ) THEN
        -- Add category_id column
        ALTER TABLE question_banks ADD COLUMN category_id VARCHAR(100);
        
        -- Create index for performance
        CREATE INDEX idx_question_banks_category_id ON question_banks(category_id);
        
        -- Update existing questions to use new category_ids
        -- Map old 'category' values to new category_id values
        UPDATE question_banks SET category_id = 
            CASE 
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
        WHERE category_id IS NULL;
        
        -- Add foreign key constraint
        ALTER TABLE question_banks 
        ADD CONSTRAINT fk_question_banks_category 
        FOREIGN KEY (category_id) REFERENCES question_categories(category_id) ON DELETE CASCADE;
        
        RAISE NOTICE 'Added category_id column to question_banks and migrated existing data';
    ELSE
        -- Update existing questions that might not be mapped
        UPDATE question_banks SET category_id = 
            CASE 
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
        
        RAISE NOTICE 'category_id column already exists in question_banks - updated unmapped questions';
    END IF;
END
$$;

-- ================================================================
-- 5. ENABLE ROW LEVEL SECURITY (RLS)
-- ================================================================

ALTER TABLE question_categories ENABLE ROW LEVEL SECURITY;

-- Create policies for question_categories table
-- Allow everyone to read active categories
CREATE POLICY "Allow public to read active question categories" ON question_categories
  FOR SELECT USING (is_active = true);

-- Allow authenticated users to read all categories
CREATE POLICY "Allow authenticated users to read all question categories" ON question_categories
  FOR SELECT TO authenticated USING (true);

-- ================================================================
-- 6. GRANT PERMISSIONS
-- ================================================================

GRANT SELECT ON question_categories TO anon;
GRANT SELECT ON question_categories TO authenticated;
GRANT ALL ON question_categories TO service_role;
GRANT USAGE, SELECT ON SEQUENCE question_categories_id_seq TO service_role;

-- ================================================================
-- 7. CREATE HELPER FUNCTIONS
-- ================================================================

-- Function to safely add new question categories
CREATE OR REPLACE FUNCTION add_question_category(
  p_category_id VARCHAR(100),
  p_name VARCHAR(255),
  p_description TEXT DEFAULT NULL,
  p_icon VARCHAR(50) DEFAULT 'HelpCircle',
  p_color VARCHAR(100) DEFAULT 'text-gray-400 bg-gray-400/10 border-gray-400/20',
  p_display_order INTEGER DEFAULT 10,
  p_weight_percentage DECIMAL(5,2) DEFAULT 15.00
)
RETURNS JSON AS $$
DECLARE
  result JSON;
  category_exists BOOLEAN;
BEGIN
  -- Check if category already exists
  SELECT EXISTS(SELECT 1 FROM question_categories WHERE category_id = p_category_id) INTO category_exists;
  
  IF category_exists THEN
    -- Return existing category
    SELECT row_to_json(question_categories.*) INTO result
    FROM question_categories 
    WHERE category_id = p_category_id;
    
    RETURN json_build_object(
      'success', true,
      'message', 'Question category already exists',
      'data', result
    );
  ELSE
    -- Insert new category
    INSERT INTO question_categories (category_id, name, description, icon, color, display_order, weight_percentage, is_active, is_system)
    VALUES (p_category_id, p_name, p_description, p_icon, p_color, p_display_order, p_weight_percentage, true, false)
    RETURNING row_to_json(question_categories.*) INTO result;
    
    RETURN json_build_object(
      'success', true,
      'message', 'Question category created successfully',
      'data', result
    );
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    RETURN json_build_object(
      'success', false,
      'message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get active question categories with question counts
CREATE OR REPLACE FUNCTION get_active_question_categories()
RETURNS TABLE(
  id INTEGER,
  category_id VARCHAR(100),
  name VARCHAR(255),
  description TEXT,
  icon VARCHAR(50),
  color VARCHAR(100),
  display_order INTEGER,
  weight_percentage DECIMAL(5,2),
  is_system BOOLEAN,
  question_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    qc.id,
    qc.category_id,
    qc.name,
    qc.description,
    qc.icon,
    qc.color,
    qc.display_order,
    qc.weight_percentage,
    qc.is_system,
    COALESCE(question_counts.count, 0) as question_count
  FROM question_categories qc
  LEFT JOIN (
    SELECT category_id, COUNT(*) as count
    FROM question_banks
    WHERE category_id IS NOT NULL
    GROUP BY category_id
  ) question_counts ON qc.category_id = question_counts.category_id
  WHERE qc.is_active = true
  ORDER BY qc.display_order ASC, qc.created_at ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================
-- 8. GRANT FUNCTION PERMISSIONS
-- ================================================================

GRANT EXECUTE ON FUNCTION add_question_category TO service_role;
GRANT EXECUTE ON FUNCTION get_active_question_categories TO authenticated;
GRANT EXECUTE ON FUNCTION get_active_question_categories TO anon;

-- ================================================================
-- 9. VERIFICATION AND RESULTS
-- ================================================================

-- Display setup completion status
SELECT 
  'Dynamic Question Categories Setup Complete! 🎉' as status,
  COUNT(*) as total_categories,
  COUNT(*) FILTER (WHERE is_system = true) as system_categories,
  COUNT(*) FILTER (WHERE is_system = false) as custom_categories
FROM question_categories;

-- Show all categories with question counts
SELECT 
  name,
  category_id,
  description,
  icon,
  weight_percentage,
  is_system,
  is_active
FROM question_categories 
ORDER BY display_order;

-- Verify migration results
SELECT 
  'Migration Verification' as status,
  COUNT(*) as total_questions,
  COUNT(*) FILTER (WHERE category_id IS NOT NULL) as migrated_questions,
  COUNT(*) FILTER (WHERE category_id IS NULL) as unmigrated_questions
FROM question_banks;

-- Show questions per category
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

-- ================================================================
-- SETUP COMPLETE!
-- ================================================================
-- Your dynamic question categories system is now ready to use!
-- 
-- Next steps:
-- 1. Access the admin panel to manage question categories
-- 2. Navigate to /admin and click "Question Categories"
-- 3. Add, edit, or customize categories as needed
-- 4. Start using the dynamic system for question generation
-- ================================================================