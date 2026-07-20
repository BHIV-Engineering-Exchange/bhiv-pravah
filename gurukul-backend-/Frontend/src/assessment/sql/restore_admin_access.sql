-- Restore Admin Access
-- Run this in your Supabase SQL Editor to restore your admin login

-- Create admin record with your credentials
INSERT INTO admins (username, password, email, is_active, created_at, updated_at)
VALUES (
  'admin',
  'admin234', 
  'admin@example.com',
  true,
  NOW(),
  NOW()
) ON CONFLICT (username) DO UPDATE SET
  password = EXCLUDED.password,
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

-- Verify the admin was created
SELECT username, email, is_active, created_at FROM admins WHERE username = 'admin';

-- Success message
SELECT 'Admin access restored! You can now login with username: admin, password: admin234' as status;