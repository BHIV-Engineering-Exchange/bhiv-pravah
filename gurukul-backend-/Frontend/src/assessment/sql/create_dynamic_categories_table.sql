-- Dynamic Categories Table Creation Script
-- This table stores form sections/categories that can be managed dynamically by admin

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

-- Create an index on category_id for faster lookups
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

-- Insert default categories (similar to current hardcoded sections)
INSERT INTO form_categories (category_id, name, description, icon, color, display_order, is_system) VALUES
('background_selection', 'Background Selection', 'Tell us about your academic background and goals', 'GraduationCap', 'text-blue-400 bg-blue-400/10 border-blue-400/20', -3, true),
('personal_info', 'Personal Information', 'Basic information about you', 'User', 'text-green-400 bg-green-400/10 border-green-400/20', 0, true),
('academic_info', 'Academic Details', 'Your educational background and preferences', 'BookOpen', 'text-purple-400 bg-purple-400/10 border-purple-400/20', 1, true),
('preferences', 'Learning Preferences', 'How you prefer to learn', 'Settings', 'text-orange-400 bg-orange-400/10 border-orange-400/20', 2, true),
('general', 'Additional Information', 'Other relevant details', 'FileText', 'text-gray-400 bg-gray-400/10 border-gray-400/20', 3, true);

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
COMMENT ON TABLE form_categories IS 'Stores form sections/categories that can be dynamically managed';
COMMENT ON COLUMN form_categories.category_id IS 'Unique identifier for the category';
COMMENT ON COLUMN form_categories.name IS 'Display name of the category';
COMMENT ON COLUMN form_categories.description IS 'Description shown to users';
COMMENT ON COLUMN form_categories.icon IS 'Lucide icon name for the category';
COMMENT ON COLUMN form_categories.color IS 'Tailwind CSS classes for category styling';
COMMENT ON COLUMN form_categories.display_order IS 'Order in which categories appear in forms';
COMMENT ON COLUMN form_categories.is_active IS 'Whether this category is currently active';
COMMENT ON COLUMN form_categories.is_system IS 'System categories cannot be deleted by admin';