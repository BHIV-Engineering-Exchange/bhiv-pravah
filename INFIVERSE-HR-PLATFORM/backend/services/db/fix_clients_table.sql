-- Fix for clients table missing columns
-- Add missing columns to clients table for authentication features

-- Add missing columns to clients table
ALTER TABLE clients 
ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

-- Update existing records to have default values
UPDATE clients 
SET failed_login_attempts = 0 
WHERE failed_login_attempts IS NULL;

-- Verify the fix
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'clients' 
AND column_name IN ('failed_login_attempts', 'locked_until')
ORDER BY column_name;

-- Show success message
SELECT 'Clients table fixed successfully - added failed_login_attempts and locked_until columns' as status;