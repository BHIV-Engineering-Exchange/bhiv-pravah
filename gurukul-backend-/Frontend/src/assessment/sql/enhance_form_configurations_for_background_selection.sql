-- Enhanced Form Configuration Schema with Background Selection Support
-- Run this script to add background selection configuration to form_configurations table

-- Add background selection configuration columns to form_configurations
ALTER TABLE form_configurations 
ADD COLUMN IF NOT EXISTS background_selection_config JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS include_background_selection BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS form_sections JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS field_visibility_rules JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS conditional_logic JSONB DEFAULT '{}';

-- Add comments for new columns
COMMENT ON COLUMN form_configurations.background_selection_config IS 'Configuration for background selection fields (field_of_study, class_level, learning_goals)';
COMMENT ON COLUMN form_configurations.include_background_selection IS 'Whether to include background selection fields in this form';
COMMENT ON COLUMN form_configurations.form_sections IS 'Organized sections of the form with metadata';
COMMENT ON COLUMN form_configurations.field_visibility_rules IS 'Rules for showing/hiding fields based on other field values';
COMMENT ON COLUMN form_configurations.conditional_logic IS 'Advanced conditional logic for dynamic form behavior';

-- Create an index on background_selection_config for faster queries
CREATE INDEX IF NOT EXISTS idx_form_configs_background_config 
ON form_configurations USING gin (background_selection_config);

-- Create an index on form_sections for section-based queries
CREATE INDEX IF NOT EXISTS idx_form_configs_sections 
ON form_configurations USING gin (form_sections);

-- Update existing form configurations to include background selection by default
UPDATE form_configurations 
SET include_background_selection = true,
    background_selection_config = '{
      "field_of_study": {
        "enabled": true,
        "required": true,
        "order": -3,
        "styling": {
          "displayType": "card_grid",
          "gridCols": "2",
          "showIcons": true,
          "showDescriptions": true
        }
      },
      "class_level": {
        "enabled": true,
        "required": true,
        "order": -2,
        "styling": {
          "displayType": "card_grid",
          "gridCols": "2"
        }
      },
      "learning_goals": {
        "enabled": true,
        "required": true,
        "order": -1,
        "styling": {
          "displayType": "card_grid",
          "gridCols": "2"
        }
      }
    }'::jsonb,
    form_sections = '{
      "background_selection": {
        "title": "Learning Background",
        "description": "Help us personalize your learning experience",
        "order": 0,
        "icon": "GraduationCap"
      },
      "personal_info": {
        "title": "Personal Information",
        "description": "Basic information about you",
        "order": 1,
        "icon": "User"
      },
      "academic_info": {
        "title": "Academic Details",
        "description": "Your educational background and interests",
        "order": 2,
        "icon": "BookOpen"
      },
      "preferences": {
        "title": "Learning Preferences",
        "description": "How you prefer to learn and engage",
        "order": 3,
        "icon": "Settings"
      }
    }'::jsonb
WHERE include_background_selection IS NULL;

-- Create a function to validate background selection configuration
CREATE OR REPLACE FUNCTION validate_background_selection_config(config JSONB)
RETURNS BOOLEAN AS $$
BEGIN
  -- Check if config has required fields
  IF NOT (config ? 'field_of_study' AND config ? 'class_level' AND config ? 'learning_goals') THEN
    RETURN FALSE;
  END IF;
  
  -- Check if each field has required properties
  IF NOT (
    config->'field_of_study' ? 'enabled' AND
    config->'class_level' ? 'enabled' AND
    config->'learning_goals' ? 'enabled'
  ) THEN
    RETURN FALSE;
  END IF;
  
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Add a check constraint to ensure valid background selection configuration
ALTER TABLE form_configurations 
ADD CONSTRAINT check_background_selection_config 
CHECK (
  include_background_selection = FALSE OR 
  validate_background_selection_config(background_selection_config)
);

-- Create a view for easier querying of enhanced form configurations
CREATE OR REPLACE VIEW enhanced_form_configurations AS
SELECT 
  fc.*,
  CASE 
    WHEN fc.include_background_selection = true THEN
      jsonb_build_object(
        'hasBackgroundSelection', true,
        'backgroundFields', fc.background_selection_config,
        'sections', fc.form_sections,
        'totalFields', (
          CASE WHEN fc.include_background_selection THEN 3 ELSE 0 END +
          jsonb_array_length(fc.fields)
        )
      )
    ELSE
      jsonb_build_object(
        'hasBackgroundSelection', false,
        'sections', fc.form_sections,
        'totalFields', jsonb_array_length(fc.fields)
      )
  END as enhanced_metadata
FROM form_configurations fc;

-- Create a function to get complete form configuration with background selection
CREATE OR REPLACE FUNCTION get_enhanced_form_config(config_id UUID DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
  config_record RECORD;
  enhanced_config JSONB;
  background_fields JSONB;
  all_fields JSONB;
BEGIN
  -- Get the form configuration (active if no ID specified)
  IF config_id IS NULL THEN
    SELECT * INTO config_record 
    FROM form_configurations 
    WHERE is_active = true 
    LIMIT 1;
  ELSE
    SELECT * INTO config_record 
    FROM form_configurations 
    WHERE id = config_id;
  END IF;
  
  IF NOT FOUND THEN
    RETURN NULL;
  END IF;
  
  -- Build background selection fields if enabled
  IF config_record.include_background_selection THEN
    background_fields := '[
      {
        "id": "field_of_study",
        "type": "radio",
        "label": "What field are you studying or working in?",
        "required": true,
        "order": -3,
        "section": "background_selection",
        "helpText": "This helps us personalize your learning experience",
        "options": [],
        "styling": {
          "displayType": "card_grid",
          "gridCols": "2",
          "showIcons": true,
          "showDescriptions": true
        }
      },
      {
        "id": "class_level", 
        "type": "radio",
        "label": "What is your current education level?",
        "required": true,
        "order": -2,
        "section": "background_selection",
        "options": [
          {"value": "high_school", "label": "High School (9th-12th Grade)"},
          {"value": "undergraduate", "label": "Undergraduate (Bachelor\\'s)"},
          {"value": "graduate", "label": "Graduate (Master\\'s)"},
          {"value": "postgraduate", "label": "Postgraduate (PhD/Doctorate)"},
          {"value": "professional", "label": "Professional/Working"}
        ],
        "styling": {
          "displayType": "card_grid",
          "gridCols": "2"
        }
      },
      {
        "id": "learning_goals",
        "type": "radio", 
        "label": "What is your main learning goal?",
        "required": true,
        "order": -1,
        "section": "background_selection",
        "options": [
          {"value": "skill_building", "label": "Build specific skills for career"},
          {"value": "academic_support", "label": "Academic support & exam prep"},
          {"value": "career_change", "label": "Career change or transition"},
          {"value": "personal_growth", "label": "Personal growth & learning"},
          {"value": "certification", "label": "Professional certification"},
          {"value": "exploration", "label": "Explore new interests"}
        ],
        "styling": {
          "displayType": "card_grid",
          "gridCols": "2"
        }
      }
    ]'::jsonb;
    
    -- Merge background fields with form fields
    all_fields := background_fields || config_record.fields;
  ELSE
    all_fields := config_record.fields;
  END IF;
  
  -- Build the enhanced configuration
  enhanced_config := jsonb_build_object(
    'id', config_record.id,
    'name', config_record.name,
    'description', config_record.description,
    'fields', all_fields,
    'is_active', config_record.is_active,
    'created_at', config_record.created_at,
    'updated_at', config_record.updated_at,
    'hasBackgroundSelection', config_record.include_background_selection,
    'backgroundConfig', config_record.background_selection_config,
    'sections', config_record.form_sections,
    'fieldVisibilityRules', config_record.field_visibility_rules,
    'conditionalLogic', config_record.conditional_logic,
    'metadata', jsonb_build_object(
      'totalFields', jsonb_array_length(all_fields),
      'hasConditionalLogic', config_record.conditional_logic != '{}'::jsonb,
      'sectionCount', jsonb_object_keys(config_record.form_sections)
    )
  );
  
  RETURN enhanced_config;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT ON enhanced_form_configurations TO authenticated;
GRANT EXECUTE ON FUNCTION get_enhanced_form_config(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION validate_background_selection_config(JSONB) TO authenticated;

-- Insert a default enhanced form configuration if none exists
INSERT INTO form_configurations (
  name, 
  description, 
  fields, 
  is_active,
  include_background_selection,
  background_selection_config,
  form_sections
)
SELECT 
  'Enhanced Student Intake Form',
  'Comprehensive student intake form with personalized background selection',
  '[
    {
      "id": "name",
      "type": "text",
      "label": "Full Name",
      "placeholder": "e.g., Asha Gupta",
      "required": true,
      "order": 1,
      "section": "personal_info"
    },
    {
      "id": "email", 
      "type": "email",
      "label": "Email",
      "placeholder": "your.email@example.com",
      "required": false,
      "order": 2,
      "section": "personal_info"
    },
    {
      "id": "age",
      "type": "number",
      "label": "Age", 
      "placeholder": "17",
      "required": false,
      "order": 3,
      "section": "personal_info"
    }
  ]'::jsonb,
  true,
  true,
  '{
    "field_of_study": {
      "enabled": true,
      "required": true,
      "order": -3,
      "styling": {
        "displayType": "card_grid",
        "gridCols": "2",
        "showIcons": true,
        "showDescriptions": true
      }
    },
    "class_level": {
      "enabled": true,
      "required": true,
      "order": -2,
      "styling": {
        "displayType": "card_grid",
        "gridCols": "2"
      }
    },
    "learning_goals": {
      "enabled": true,
      "required": true,
      "order": -1,
      "styling": {
        "displayType": "card_grid",
        "gridCols": "2"
      }
    }
  }'::jsonb,
  '{
    "background_selection": {
      "title": "Learning Background",
      "description": "Help us personalize your learning experience",
      "order": 0,
      "icon": "GraduationCap"
    },
    "personal_info": {
      "title": "Personal Information", 
      "description": "Basic information about you",
      "order": 1,
      "icon": "User"
    }
  }'::jsonb
WHERE NOT EXISTS (
  SELECT 1 FROM form_configurations WHERE include_background_selection = true
);

-- Add helpful comments
COMMENT ON FUNCTION get_enhanced_form_config IS 'Returns a complete form configuration with background selection fields merged in proper order';
COMMENT ON VIEW enhanced_form_configurations IS 'Enhanced view of form configurations with computed metadata for background selection';

-- Show summary of changes
DO $$
BEGIN
  RAISE NOTICE 'Enhanced form configuration schema updated successfully!';
  RAISE NOTICE 'Added columns: background_selection_config, include_background_selection, form_sections, field_visibility_rules, conditional_logic';
  RAISE NOTICE 'Created function: get_enhanced_form_config() for retrieving complete form configurations';
  RAISE NOTICE 'Created view: enhanced_form_configurations for easier querying';
END $$;