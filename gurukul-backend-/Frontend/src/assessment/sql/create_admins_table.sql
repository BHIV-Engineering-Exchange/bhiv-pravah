-- Create admins table
CREATE TABLE IF NOT EXISTS admins (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create RLS policies
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

-- Policy to allow admins to read their own data
CREATE POLICY "Admins can read their own data" ON admins
    FOR SELECT
    USING (auth.uid() = id);

-- Policy to allow inserting new admin (will be restricted through API)
CREATE POLICY "Allow admin creation" ON admins
    FOR INSERT
    WITH CHECK (true);
