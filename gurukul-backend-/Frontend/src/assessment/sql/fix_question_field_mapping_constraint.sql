-- Fix for question_field_mapping unique constraint
-- Run this if you're getting the "no unique or exclusion constraint matching the ON CONFLICT specification" error

-- Add the missing unique constraint to question_field_mapping table
ALTER TABLE question_field_mapping 
ADD CONSTRAINT question_field_mapping_question_id_field_id_key 
UNIQUE (question_id, field_id);

-- Verify the constraint was added
SELECT 
    conname as constraint_name,
    contype as constraint_type
FROM pg_constraint 
WHERE conrelid = 'question_field_mapping'::regclass 
AND contype = 'u';

-- Success message
SELECT 'Unique constraint added successfully to question_field_mapping table!' as status;