-- Fix Form Field Repetition Issues
-- This script ensures no duplicate fields exist in form configurations
-- and updates the database structure to reflect the new integrated background selection

-- First, let's check current form configurations
SELECT id, name, 
       jsonb_array_length(fields) as field_count,
       jsonb_path_query_array(fields, '$[*].id') as field_ids
FROM form_configurations 
WHERE is_active = true;

-- Remove duplicate field_of_study and education_level fields from existing configurations
UPDATE form_configurations 
SET fields = (
    SELECT jsonb_agg(field)
    FROM (
        SELECT DISTINCT ON (field->>'id') field
        FROM jsonb_array_elements(fields) as field
        WHERE field->>'id' NOT IN ('field_of_study', 'education_level')
        ORDER BY field->>'id', (field->>'order')::int
    ) as unique_fields
),
updated_at = now()
WHERE jsonb_path_exists(fields, '$[*] ? (@.id == "field_of_study" || @.id == "education_level")');

-- Add proper sections to existing fields if they don't have them
UPDATE form_configurations 
SET fields = (
    SELECT jsonb_agg(
        CASE 
            WHEN field->>'id' IN ('name', 'age', 'email', 'phone') 
            THEN jsonb_set(field, '{section}', '"personal_info"')
            
            WHEN field->>'id' IN ('current_skills', 'interests', 'goals') 
            THEN jsonb_set(field, '{section}', '"academic_info"')
            
            WHEN field->>'id' IN ('preferred_learning_style', 'availability_per_week_hours', 'experience_years') 
            THEN jsonb_set(field, '{section}', '"preferences"')
            
            ELSE COALESCE(
                field,
                jsonb_set(field, '{section}', '"general"')
            )
        END
    )
    FROM jsonb_array_elements(fields) as field
),
updated_at = now()
WHERE EXISTS (
    SELECT 1 
    FROM jsonb_array_elements(fields) as field_elem
    WHERE field_elem ? 'section' = false
);

-- Create enhanced form configurations table if it doesn't exist
CREATE TABLE IF NOT EXISTS enhanced_form_configurations (
    id SERIAL PRIMARY KEY,
    base_config_id TEXT REFERENCES form_configurations(id),
    background_selection_config JSONB DEFAULT '{}',
    include_background_selection BOOLEAN DEFAULT true,
    field_specific_configs JSONB DEFAULT '{}',
    form_sections JSONB DEFAULT '{
        "background_selection": {
            "title": "Background Selection",
            "description": "Tell us about your academic background and goals",
            "icon": "GraduationCap",
            "order": -3
        },
        "personal_info": {
            "title": "Personal Information", 
            "description": "Basic information about you",
            "icon": "User",
            "order": 0
        },
        "academic_info": {
            "title": "Academic Details",
            "description": "Your educational background and preferences", 
            "icon": "BookOpen",
            "order": 1
        },
        "preferences": {
            "title": "Learning Preferences",
            "description": "How you prefer to learn",
            "icon": "Settings", 
            "order": 2
        },
        "general": {
            "title": "Additional Information",
            "description": "Other relevant details",
            "icon": "Settings",
            "order": 3
        }
    }',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    is_active BOOLEAN DEFAULT true
);

-- Create background selection configuration if it doesn't exist
INSERT INTO enhanced_form_configurations (
    base_config_id,
    background_selection_config,
    include_background_selection
)
SELECT 
    id as base_config_id,
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
    }' as background_selection_config,
    true as include_background_selection
FROM form_configurations 
WHERE is_active = true
  AND NOT EXISTS (
    SELECT 1 FROM enhanced_form_configurations 
    WHERE base_config_id = form_configurations.id
  );

-- Update RLS policies for enhanced_form_configurations
DROP POLICY IF EXISTS "enhanced_form_configurations_select_policy" ON enhanced_form_configurations;
DROP POLICY IF EXISTS "enhanced_form_configurations_insert_policy" ON enhanced_form_configurations;
DROP POLICY IF EXISTS "enhanced_form_configurations_update_policy" ON enhanced_form_configurations;
DROP POLICY IF EXISTS "enhanced_form_configurations_delete_policy" ON enhanced_form_configurations;

CREATE POLICY "enhanced_form_configurations_select_policy" ON enhanced_form_configurations FOR SELECT USING (true);
CREATE POLICY "enhanced_form_configurations_insert_policy" ON enhanced_form_configurations FOR INSERT WITH CHECK (true);
CREATE POLICY "enhanced_form_configurations_update_policy" ON enhanced_form_configurations FOR UPDATE USING (true);
CREATE POLICY "enhanced_form_configurations_delete_policy" ON enhanced_form_configurations FOR DELETE USING (true);

-- Enable RLS
ALTER TABLE enhanced_form_configurations ENABLE ROW LEVEL SECURITY;

-- Create helper function to get enhanced form configuration (replace if exists)
DROP FUNCTION IF EXISTS get_enhanced_form_config(TEXT);
CREATE OR REPLACE FUNCTION get_enhanced_form_config(config_id TEXT DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    base_config JSONB;
    enhanced_config JSONB;
BEGIN
    -- Get base configuration
    SELECT row_to_json(fc.*) INTO base_config
    FROM form_configurations fc
    WHERE fc.is_active = true
    AND (config_id IS NULL OR fc.id = config_id)
    ORDER BY fc.updated_at DESC
    LIMIT 1;
    
    -- Get enhanced configuration
    SELECT row_to_json(efc.*) INTO enhanced_config
    FROM enhanced_form_configurations efc
    WHERE efc.is_active = true
    AND (config_id IS NULL OR efc.base_config_id = config_id)
    ORDER BY efc.updated_at DESC
    LIMIT 1;
    
    -- Combine configurations
    result := jsonb_build_object(
        'base_config', base_config,
        'enhanced_config', enhanced_config,
        'has_background_selection', COALESCE(enhanced_config->>'include_background_selection', 'true')::boolean
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create helper function to prevent field duplication (handle dependencies correctly)
-- First drop constraint that depends on the function
ALTER TABLE form_configurations 
DROP CONSTRAINT IF EXISTS check_unique_field_ids;

-- Now we can safely drop and recreate the function
DROP FUNCTION IF EXISTS validate_form_fields(JSONB);
CREATE OR REPLACE FUNCTION validate_form_fields(fields JSONB)
RETURNS BOOLEAN AS $$
DECLARE
    field_ids TEXT[];
    unique_count INTEGER;
    total_count INTEGER;
BEGIN
    -- Extract all field IDs
    SELECT array_agg(field_value->>'id') INTO field_ids
    FROM jsonb_array_elements(fields) as field_value;
    
    -- Count unique vs total
    SELECT array_length(array(SELECT DISTINCT unnest(field_ids)), 1) INTO unique_count;
    SELECT array_length(field_ids, 1) INTO total_count;
    
    -- Return false if duplicates found
    IF unique_count != total_count THEN
        RAISE NOTICE 'Duplicate field IDs detected in form configuration';
        RETURN false;
    END IF;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Now add the constraint that uses the function
ALTER TABLE form_configurations 
ADD CONSTRAINT check_unique_field_ids 
CHECK (validate_form_fields(fields));

-- Final verification query
SELECT 
    'Form configurations updated successfully' as status,
    COUNT(*) as total_configs,
    COUNT(CASE WHEN EXISTS(
        SELECT 1 FROM jsonb_array_elements(fields) as f 
        WHERE f->>'id' = 'field_of_study'
    ) THEN 1 END) as configs_with_field_of_study,
    COUNT(CASE WHEN EXISTS(
        SELECT 1 FROM jsonb_array_elements(fields) as f 
        WHERE f->>'id' = 'education_level'
    ) THEN 1 END) as configs_with_education_level
FROM form_configurations 
WHERE is_active = true;