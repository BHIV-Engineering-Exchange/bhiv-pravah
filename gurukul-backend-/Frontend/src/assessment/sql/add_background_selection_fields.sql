-- Create background_selections table for storing student background information
CREATE TABLE IF NOT EXISTS background_selections (
  id SERIAL PRIMARY KEY,
  user_id TEXT UNIQUE NOT NULL,
  field_of_study VARCHAR(255) NOT NULL,
  class_level VARCHAR(255) NOT NULL,
  learning_goals VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_background_selections_user_id ON background_selections(user_id);

-- Enable RLS (Row Level Security)
ALTER TABLE background_selections ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for authenticated users
CREATE POLICY "Allow all operations for authenticated users on background_selections" ON background_selections
  FOR ALL USING (true);

-- Add trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_background_selections_updated_at BEFORE UPDATE
    ON background_selections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();