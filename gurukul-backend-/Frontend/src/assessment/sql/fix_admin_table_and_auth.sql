-- Fix Admin Table and Authentication
-- Run this in your Supabase SQL Editor

-- First, let's see what columns exist in the admins table
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'admins';

-- Drop the existing admins table and recreate it with the correct structure
DROP TABLE IF EXISTS admins CASCADE;

-- Create admins table with password column for your current auth system
CREATE TABLE admins (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  email TEXT UNIQUE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);
CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);

-- Enable RLS
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Allow all operations for development" ON admins
    FOR ALL TO PUBLIC USING (true);

-- Create trigger for updated_at
CREATE TRIGGER update_admins_updated_at 
    BEFORE UPDATE ON admins 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert your admin credentials
INSERT INTO admins (username, password, email, is_active, created_at, updated_at)
VALUES (
  'admin',
  'admin234', 
  'admin@example.com',
  true,
  NOW(),
  NOW()
);

-- Verify the admin was created
SELECT username, email, is_active, created_at FROM admins WHERE username = 'admin';

-- Success message
SELECT 'Admin table fixed and admin access restored! Login with username: admin, password: admin234' as status;