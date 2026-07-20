-- SQL script to create question banks tables for field-based assessment system

-- Create study_fields table to define available study fields
CREATE TABLE IF NOT EXISTS study_fields (
    field_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    description TEXT,
    subcategories JSONB DEFAULT '[]',
    question_weights JSONB DEFAULT '{}',
    difficulty_distribution JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create question_banks table to store all hardcoded questions
CREATE TABLE IF NOT EXISTS question_banks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question_id TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    question_text TEXT NOT NULL,
    options JSONB NOT NULL DEFAULT '[]',
    correct_answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    vedic_connection TEXT DEFAULT '',
    modern_application TEXT DEFAULT '',
    tags JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create question_field_mapping table to map questions to study fields
CREATE TABLE IF NOT EXISTS question_field_mapping (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question_id TEXT REFERENCES question_banks(question_id) ON DELETE CASCADE,
    field_id TEXT NOT NULL,
    weight INTEGER DEFAULT 1,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create question_usage_stats table to track question performance
CREATE TABLE IF NOT EXISTS question_usage_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question_id TEXT REFERENCES question_banks(question_id) ON DELETE CASCADE,
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    average_time_seconds DECIMAL(6,2) DEFAULT 0,
    difficulty_rating DECIMAL(3,2) DEFAULT 0,
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_question_banks_category ON question_banks(category);
CREATE INDEX IF NOT EXISTS idx_question_banks_difficulty ON question_banks(difficulty);
CREATE INDEX IF NOT EXISTS idx_question_banks_active ON question_banks(is_active);
CREATE INDEX IF NOT EXISTS idx_question_banks_created_by ON question_banks(created_by);
CREATE INDEX IF NOT EXISTS idx_question_field_mapping_question_id ON question_field_mapping(question_id);
CREATE INDEX IF NOT EXISTS idx_question_field_mapping_field_id ON question_field_mapping(field_id);
CREATE INDEX IF NOT EXISTS idx_question_usage_stats_question_id ON question_usage_stats(question_id);

-- Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_question_banks_options ON question_banks USING GIN (options);
CREATE INDEX IF NOT EXISTS idx_question_banks_tags ON question_banks USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_study_fields_subcategories ON study_fields USING GIN (subcategories);
CREATE INDEX IF NOT EXISTS idx_study_fields_question_weights ON study_fields USING GIN (question_weights);

-- Enable Row Level Security
ALTER TABLE study_fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_banks ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_field_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_usage_stats ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for study_fields (read-only for users, full access for admins)
CREATE POLICY "Anyone can view study fields" ON study_fields
    FOR SELECT TO PUBLIC USING (true);

CREATE POLICY "Only admins can modify study fields" ON study_fields
    FOR ALL TO authenticated 
    USING (EXISTS (SELECT 1 FROM admins WHERE user_id = auth.uid()::text));

-- Create RLS policies for question_banks
CREATE POLICY "Anyone can view active questions" ON question_banks
    FOR SELECT TO PUBLIC USING (is_active = true);

CREATE POLICY "Admins can view all questions" ON question_banks
    FOR SELECT TO authenticated 
    USING (EXISTS (SELECT 1 FROM admins WHERE user_id = auth.uid()::text));

CREATE POLICY "Admins can insert questions" ON question_banks
    FOR INSERT TO authenticated 
    WITH CHECK (EXISTS (SELECT 1 FROM admins WHERE user_id = auth.uid()::text));

CREATE POLICY "Admins can update questions" ON question_banks
    FOR UPDATE TO authenticated 
    USING (EXISTS (SELECT 1 FROM admins WHERE user_id = auth.uid()::text));

CREATE POLICY "Admins can delete questions" ON question_banks
    FOR DELETE TO authenticated 
    USING (EXISTS (SELECT 1 FROM admins WHERE user_id = auth.uid()::text));

-- Create RLS policies for question_field_mapping
CREATE POLICY "Anyone can view question field mappings" ON question_field_mapping
    FOR SELECT TO PUBLIC USING (true);

CREATE POLICY "Admins can manage question field mappings" ON question_field_mapping
    FOR ALL TO authenticated 
    USING (EXISTS (SELECT 1 FROM admins WHERE user_id = auth.uid()::text));

-- Create RLS policies for question_usage_stats
CREATE POLICY "Anyone can view question usage stats" ON question_usage_stats
    FOR SELECT TO PUBLIC USING (true);

CREATE POLICY "System can update question usage stats" ON question_usage_stats
    FOR ALL TO authenticated USING (true);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_question_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_study_fields_updated_at 
    BEFORE UPDATE ON study_fields 
    FOR EACH ROW EXECUTE FUNCTION update_question_updated_at_column();

CREATE TRIGGER update_question_banks_updated_at 
    BEFORE UPDATE ON question_banks 
    FOR EACH ROW EXECUTE FUNCTION update_question_updated_at_column();

CREATE TRIGGER update_question_usage_stats_updated_at 
    BEFORE UPDATE ON question_usage_stats 
    FOR EACH ROW EXECUTE FUNCTION update_question_updated_at_column();

-- Create function to update question usage statistics
CREATE OR REPLACE FUNCTION update_question_usage_stats(
    p_question_id TEXT,
    p_is_correct BOOLEAN,
    p_time_seconds INTEGER
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO question_usage_stats (question_id, total_attempts, correct_attempts, average_time_seconds, last_used)
    VALUES (p_question_id, 1, CASE WHEN p_is_correct THEN 1 ELSE 0 END, p_time_seconds, NOW())
    ON CONFLICT (question_id) DO UPDATE SET
        total_attempts = question_usage_stats.total_attempts + 1,
        correct_attempts = question_usage_stats.correct_attempts + CASE WHEN p_is_correct THEN 1 ELSE 0 END,
        average_time_seconds = (question_usage_stats.average_time_seconds * question_usage_stats.total_attempts + p_time_seconds) / (question_usage_stats.total_attempts + 1),
        last_used = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Insert default study fields
INSERT INTO study_fields (field_id, name, short_name, description, subcategories, question_weights, difficulty_distribution, is_active) VALUES
('stem', 'STEM (Science, Technology, Engineering, Mathematics)', 'STEM', 
 'Science, Technology, Engineering, and Mathematics fields including Computer Science, Physics, Chemistry, Biology, Engineering, and Mathematical Sciences',
 '["Computer Science", "Software Engineering", "Data Science", "Cybersecurity", "Artificial Intelligence", "Physics", "Chemistry", "Biology", "Mathematics", "Engineering", "Information Technology"]',
 '{"Coding": 35, "Logic": 25, "Mathematics": 25, "Language": 5, "Culture": 5, "Vedic Knowledge": 3, "Current Affairs": 2}',
 '{"easy": 25, "medium": 50, "hard": 25}'),

('business', 'Business & Economics', 'Business',
 'Business administration, economics, finance, marketing, entrepreneurship, and related commercial fields',
 '["Business Administration", "Economics", "Finance", "Marketing", "Accounting", "Entrepreneurship", "Management", "International Business", "Supply Chain Management", "Human Resources"]',
 '{"Logic": 30, "Current Affairs": 25, "Language": 20, "Mathematics": 10, "Culture": 10, "Coding": 3, "Vedic Knowledge": 2}',
 '{"easy": 30, "medium": 50, "hard": 20}'),

('social_sciences', 'Social Sciences', 'Social Sciences',
 'Psychology, sociology, political science, anthropology, and other social science disciplines',
 '["Psychology", "Sociology", "Political Science", "Anthropology", "International Relations", "Social Work", "Criminology", "Geography", "History", "Philosophy"]',
 '{"Language": 30, "Culture": 25, "Current Affairs": 20, "Logic": 15, "Vedic Knowledge": 5, "Mathematics": 3, "Coding": 2}',
 '{"easy": 35, "medium": 45, "hard": 20}'),

('health_medicine', 'Health & Medicine', 'Health & Medicine',
 'Medicine, nursing, pharmacy, public health, and other healthcare-related fields',
 '["Medicine", "Nursing", "Pharmacy", "Public Health", "Dentistry", "Veterinary Medicine", "Physical Therapy", "Occupational Therapy", "Medical Technology", "Health Administration"]',
 '{"Logic": 30, "Current Affairs": 20, "Language": 20, "Mathematics": 15, "Vedic Knowledge": 8, "Culture": 5, "Coding": 2}',
 '{"easy": 30, "medium": 50, "hard": 20}'),

('creative_arts', 'Creative Arts & Humanities', 'Creative Arts',
 'Fine arts, literature, languages, music, theater, design, and other creative and humanities disciplines',
 '["Fine Arts", "Literature", "Languages", "Music", "Theater", "Film Studies", "Graphic Design", "Creative Writing", "Art History", "Linguistics"]',
 '{"Language": 35, "Culture": 25, "Vedic Knowledge": 15, "Current Affairs": 10, "Logic": 10, "Mathematics": 3, "Coding": 2}',
 '{"easy": 35, "medium": 45, "hard": 20}'),

('other', 'Other Fields', 'Other',
 'Agriculture, environmental studies, sports science, and other specialized fields',
 '["Agriculture", "Environmental Studies", "Sports Science", "Hospitality Management", "Tourism", "Architecture", "Urban Planning", "Library Science", "Education", "Law"]',
 '{"Language": 20, "Logic": 20, "Current Affairs": 20, "Culture": 15, "Mathematics": 10, "Vedic Knowledge": 10, "Coding": 5}',
 '{"easy": 30, "medium": 50, "hard": 20}')

ON CONFLICT (field_id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    description = EXCLUDED.description,
    subcategories = EXCLUDED.subcategories,
    question_weights = EXCLUDED.question_weights,
    difficulty_distribution = EXCLUDED.difficulty_distribution,
    updated_at = NOW();

-- Create views for easier querying
CREATE OR REPLACE VIEW question_bank_summary AS
SELECT 
    category,
    difficulty,
    COUNT(*) as total_questions,
    COUNT(CASE WHEN is_active THEN 1 END) as active_questions,
    AVG(qus.correct_attempts::DECIMAL / NULLIF(qus.total_attempts, 0)) as average_accuracy
FROM question_banks qb
LEFT JOIN question_usage_stats qus ON qb.question_id = qus.question_id
GROUP BY category, difficulty
ORDER BY category, difficulty;

CREATE OR REPLACE VIEW field_question_distribution AS
SELECT 
    sf.field_id as field_id,
    sf.name as field_name,
    qb.category,
    qb.difficulty,
    COUNT(*) as question_count,
    COUNT(CASE WHEN qb.is_active THEN 1 END) as active_questions
FROM study_fields sf
LEFT JOIN question_field_mapping qfm ON sf.field_id = qfm.field_id
LEFT JOIN question_banks qb ON qfm.question_id = qb.question_id
GROUP BY sf.field_id, sf.name, qb.category, qb.difficulty
ORDER BY sf.name, qb.category, qb.difficulty;

-- Comments for documentation
COMMENT ON TABLE study_fields IS 'Defines available study fields with their question distribution weights';
COMMENT ON TABLE question_banks IS 'Stores all hardcoded questions for the assessment system';
COMMENT ON TABLE question_field_mapping IS 'Maps questions to study fields for targeted assessments';
COMMENT ON TABLE question_usage_stats IS 'Tracks question performance and usage statistics';

-- Success message
SELECT 'Question banks tables created successfully!' as status;