
-- Create specs table
CREATE TABLE IF NOT EXISTS specs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt TEXT NOT NULL,
  json_spec JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

  -- JSON schema validation constraint
  CONSTRAINT json_spec_structure_check CHECK (
    jsonb_typeof(json_spec) = 'object' AND
    json_spec ? 'key'
  )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_specs_user_id ON specs(user_id);
CREATE INDEX IF NOT EXISTS idx_specs_created_at ON specs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_specs_json_spec ON specs USING gin(json_spec);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_specs_updated_at ON specs;
CREATE TRIGGER update_specs_updated_at
    BEFORE UPDATE ON specs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security
ALTER TABLE specs ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Users can view their own specs" ON specs;
CREATE POLICY "Users can view their own specs" ON specs
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own specs" ON specs;
CREATE POLICY "Users can insert their own specs" ON specs
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own specs" ON specs;
CREATE POLICY "Users can update their own specs" ON specs
  FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own specs" ON specs;
CREATE POLICY "Users can delete their own specs" ON specs
  FOR DELETE USING (auth.uid() = user_id);
