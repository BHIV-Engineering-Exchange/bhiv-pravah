-- Create form_configurations table for storing dynamic form configurations
CREATE TABLE IF NOT EXISTS form_configurations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  fields JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_active BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster queries on active configurations
CREATE INDEX IF NOT EXISTS idx_form_configurations_active ON form_configurations(is_active);

-- Create index for faster queries on updated_at
CREATE INDEX IF NOT EXISTS idx_form_configurations_updated_at ON form_configurations(updated_at);

-- Enable Row Level Security (RLS)
ALTER TABLE form_configurations ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for authenticated users (adjust as needed)
CREATE POLICY "Allow all operations for authenticated users" ON form_configurations
  FOR ALL USING (true);

-- Insert default form configuration
INSERT INTO form_configurations (
  id,
  name,
  description,
  fields,
  is_active,
  created_at,
  updated_at
) VALUES (
  'default_config',
  'Default Student Intake Form',
  'Default form configuration matching the original intake form',
  '[
    {
      "id": "name",
      "type": "text",
      "label": "Full Name",
      "placeholder": "e.g., Asha Gupta",
      "required": true,
      "order": 1,
      "validation": {
        "minLength": 2,
        "maxLength": 100
      }
    },
    {
      "id": "age",
      "type": "number",
      "label": "Age",
      "placeholder": "17",
      "required": false,
      "order": 2,
      "validation": {
        "min": 5,
        "max": 100
      }
    },
    {
      "id": "email",
      "type": "email",
      "label": "Email",
      "placeholder": "your.email@example.com",
      "required": false,
      "order": 3,
      "validation": {
        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      }
    },
    {
      "id": "phone",
      "type": "text",
      "label": "Phone",
      "placeholder": "999-000-1234",
      "required": false,
      "order": 4,
      "validation": {
        "pattern": "^[\\d\\s\\-\\+\\(\\)]+$"
      }
    },
    {
      "id": "education_level",
      "type": "select",
      "label": "Education Level",
      "placeholder": "Select your education level",
      "required": false,
      "order": 5,
      "options": [
        { "value": "high_school", "label": "High School" },
        { "value": "undergraduate", "label": "Undergraduate" },
        { "value": "graduate", "label": "Graduate" },
        { "value": "postgraduate", "label": "Postgraduate" },
        { "value": "other", "label": "Other" }
      ]
    },
    {
      "id": "field_of_study",
      "type": "text",
      "label": "Field of Study",
      "placeholder": "CS, Math, Humanities, ...",
      "required": false,
      "order": 6
    },
    {
      "id": "current_skills",
      "type": "textarea",
      "label": "Current Skills (comma separated)",
      "placeholder": "JavaScript, Algebra, Writing",
      "required": false,
      "order": 7,
      "helpText": "Example: JavaScript, Algebra, Writing"
    },
    {
      "id": "interests",
      "type": "textarea",
      "label": "Interests (comma separated)",
      "placeholder": "Programming, Mathematics, Art",
      "required": false,
      "order": 8,
      "helpText": "Example: Programming, Mathematics, Art"
    },
    {
      "id": "goals",
      "type": "textarea",
      "label": "Goals",
      "placeholder": "What do you want to achieve?",
      "required": false,
      "order": 9
    },
    {
      "id": "preferred_learning_style",
      "type": "radio",
      "label": "Preferred Learning Style",
      "required": false,
      "order": 10,
      "options": [
        { "value": "video", "label": "Video" },
        { "value": "text", "label": "Text" },
        { "value": "interactive", "label": "Interactive" },
        { "value": "mixed", "label": "Mixed" }
      ]
    },
    {
      "id": "availability_per_week_hours",
      "type": "number",
      "label": "Availability per week (hours)",
      "placeholder": "6",
      "required": false,
      "order": 11,
      "validation": {
        "min": 0,
        "max": 168
      }
    },
    {
      "id": "experience_years",
      "type": "number",
      "label": "Prior experience (years)",
      "placeholder": "0",
      "required": false,
      "order": 12,
      "validation": {
        "min": 0,
        "max": 50
      }
    }
  ]'::jsonb,
  true,
  NOW(),
  NOW()
) ON CONFLICT (id) DO NOTHING;

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_form_configurations_updated_at 
    BEFORE UPDATE ON form_configurations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
