-- Complete Dynamic Categories Setup Script
-- This script sets up the dynamic categories system for form management

-- Drop existing table if it exists (for clean installation)
DROP TABLE IF EXISTS form_categories CASCADE;

-- Create the form_categories table
CREATE TABLE form_categories (
  id SERIAL PRIMARY KEY,
  category_id VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  icon VARCHAR(50),
  color VARCHAR(100),
  display_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  is_system BOOLEAN DEFAULT false, -- System categories cannot be deleted
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_form_categories_category_id ON form_categories(category_id);
CREATE INDEX idx_form_categories_active ON form_categories(is_active);
CREATE INDEX idx_form_categories_order ON form_categories(display_order);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_form_categories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_form_categories_updated_at
    BEFORE UPDATE ON form_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_form_categories_updated_at();

-- Insert default categories (system categories that match existing form structure)
INSERT INTO form_categories (category_id, name, description, icon, color, display_order, is_system) VALUES
('background_selection', 'Background Selection', 'Tell us about your academic background and goals', 'GraduationCap', 'text-blue-400 bg-blue-400/10 border-blue-400/20', -3, true),
('personal_info', 'Personal Information', 'Basic information about you', 'User', 'text-green-400 bg-green-400/10 border-green-400/20', 0, true),
('academic_info', 'Academic Details', 'Your educational background and preferences', 'BookOpen', 'text-purple-400 bg-purple-400/10 border-purple-400/20', 1, true),
('preferences', 'Learning Preferences', 'How you prefer to learn and study', 'Settings', 'text-orange-400 bg-orange-400/10 border-orange-400/20', 2, true),
('skills_experience', 'Skills & Experience', 'Your current skills and professional experience', 'Star', 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20', 3, false),
('goals_aspirations', 'Goals & Aspirations', 'Your learning goals and career aspirations', 'Target', 'text-pink-400 bg-pink-400/10 border-pink-400/20', 4, false),
('availability_schedule', 'Availability & Schedule', 'Your time availability and learning schedule preferences', 'Clock', 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20', 5, false),
('technical_background', 'Technical Background', 'Your technical skills and programming experience', 'Code', 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20', 6, false),
('general', 'Additional Information', 'Other relevant details and miscellaneous information', 'FileText', 'text-gray-400 bg-gray-400/10 border-gray-400/20', 10, true);

-- Enable Row Level Security (RLS)
ALTER TABLE form_categories ENABLE ROW LEVEL SECURITY;

-- Create policies for form_categories table
-- Allow everyone to read active categories
CREATE POLICY "Allow public to read active categories" ON form_categories
  FOR SELECT USING (is_active = true);

-- Allow authenticated users to read all categories
CREATE POLICY "Allow authenticated users to read all categories" ON form_categories
  FOR SELECT TO authenticated USING (true);

-- Admin operations will be handled through service layer with elevated privileges
-- We'll use the service role for admin operations

-- Grant permissions
GRANT SELECT ON form_categories TO anon;
GRANT SELECT ON form_categories TO authenticated;
GRANT ALL ON form_categories TO service_role;
GRANT USAGE, SELECT ON SEQUENCE form_categories_id_seq TO service_role;

-- Comments for documentation
COMMENT ON TABLE form_categories IS 'Stores form sections/categories that can be dynamically managed by administrators';
COMMENT ON COLUMN form_categories.category_id IS 'Unique identifier for the category (used in code)';
COMMENT ON COLUMN form_categories.name IS 'Display name of the category shown to users';
COMMENT ON COLUMN form_categories.description IS 'Description shown to users in form sections';
COMMENT ON COLUMN form_categories.icon IS 'Lucide icon name for the category (e.g., User, BookOpen, Settings)';
COMMENT ON COLUMN form_categories.color IS 'Tailwind CSS classes for category styling (e.g., text-blue-400 bg-blue-400/10)';
COMMENT ON COLUMN form_categories.display_order IS 'Order in which categories appear in forms (lower numbers first)';
COMMENT ON COLUMN form_categories.is_active IS 'Whether this category is currently active and visible';
COMMENT ON COLUMN form_categories.is_system IS 'System categories cannot be deleted by administrators';

-- Create a function to safely add new categories
CREATE OR REPLACE FUNCTION add_form_category(
  p_category_id VARCHAR(100),
  p_name VARCHAR(255),
  p_description TEXT DEFAULT NULL,
  p_icon VARCHAR(50) DEFAULT 'Settings',
  p_color VARCHAR(100) DEFAULT 'text-gray-400 bg-gray-400/10 border-gray-400/20',
  p_display_order INTEGER DEFAULT 10
)
RETURNS JSON AS $$
DECLARE
  result JSON;
  category_exists BOOLEAN;
BEGIN
  -- Check if category already exists
  SELECT EXISTS(SELECT 1 FROM form_categories WHERE category_id = p_category_id) INTO category_exists;
  
  IF category_exists THEN
    -- Return existing category
    SELECT row_to_json(form_categories.*) INTO result
    FROM form_categories 
    WHERE category_id = p_category_id;
    
    RETURN json_build_object(
      'success', true,
      'message', 'Category already exists',
      'data', result
    );
  ELSE
    -- Insert new category
    INSERT INTO form_categories (category_id, name, description, icon, color, display_order, is_active, is_system)
    VALUES (p_category_id, p_name, p_description, p_icon, p_color, p_display_order, true, false)
    RETURNING row_to_json(form_categories.*) INTO result;
    
    RETURN json_build_object(
      'success', true,
      'message', 'Category created successfully',
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

-- Create a function to get categories in display order
CREATE OR REPLACE FUNCTION get_active_categories()
RETURNS TABLE(
  id INTEGER,
  category_id VARCHAR(100),
  name VARCHAR(255),
  description TEXT,
  icon VARCHAR(50),
  color VARCHAR(100),
  display_order INTEGER,
  is_system BOOLEAN
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    fc.id,
    fc.category_id,
    fc.name,
    fc.description,
    fc.icon,
    fc.color,
    fc.display_order,
    fc.is_system
  FROM form_categories fc
  WHERE fc.is_active = true
  ORDER BY fc.display_order ASC, fc.created_at ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION add_form_category TO service_role;
GRANT EXECUTE ON FUNCTION get_active_categories TO authenticated;
GRANT EXECUTE ON FUNCTION get_active_categories TO anon;

-- Insert some example custom categories to demonstrate the system
SELECT add_form_category('contact_info', 'Contact Information', 'How to reach you', 'Phone', 'text-blue-500 bg-blue-500/10 border-blue-500/20', 1);
SELECT add_form_category('emergency_contact', 'Emergency Contact', 'Emergency contact details', 'Heart', 'text-red-500 bg-red-500/10 border-red-500/20', 7);
SELECT add_form_category('special_requirements', 'Special Requirements', 'Any special accommodations or requirements', 'Shield', 'text-purple-500 bg-purple-500/10 border-purple-500/20', 8);

-- Display final results
SELECT 
  'Dynamic Categories Setup Complete!' as status,
  COUNT(*) as total_categories,
  COUNT(*) FILTER (WHERE is_system = true) as system_categories,
  COUNT(*) FILTER (WHERE is_system = false) as custom_categories
FROM form_categories;

-- Show all categories
SELECT 
  category_id,
  name,
  description,
  icon,
  display_order,
  is_system,
  is_active
FROM form_categories 
ORDER BY display_order, created_at;