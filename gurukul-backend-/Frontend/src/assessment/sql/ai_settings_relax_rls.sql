-- =============================================================
-- Relax RLS for ai_settings only for the single global toggle row
-- Use this if client-side writes are failing with 401/RLS (Clerk-only auth)
-- =============================================================

-- Ensure table exists
CREATE TABLE IF NOT EXISTS public.ai_settings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  setting_key text UNIQUE NOT NULL,
  ai_enabled boolean NOT NULL DEFAULT true,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.ai_settings ENABLE ROW LEVEL SECURITY;

-- Base read policy
DROP POLICY IF EXISTS "ai_settings_select" ON public.ai_settings;
CREATE POLICY "ai_settings_select" ON public.ai_settings
  FOR SELECT TO public
  USING (true);

-- Scoped upsert policies for ONLY the global toggle row
DROP POLICY IF EXISTS "ai_settings_insert_global_toggle_public" ON public.ai_settings;
CREATE POLICY "ai_settings_insert_global_toggle_public" ON public.ai_settings
  FOR INSERT TO public
  WITH CHECK (setting_key = 'global_question_generation');

DROP POLICY IF EXISTS "ai_settings_update_global_toggle_public" ON public.ai_settings;
CREATE POLICY "ai_settings_update_global_toggle_public" ON public.ai_settings
  FOR UPDATE TO public
  USING (setting_key = 'global_question_generation')
  WITH CHECK (setting_key = 'global_question_generation');

-- Seed/Upsert row
INSERT INTO public.ai_settings (setting_key, ai_enabled, description)
VALUES ('global_question_generation', true, 'Global toggle for AI question generation in assignments')
ON CONFLICT (setting_key) DO UPDATE
SET ai_enabled = EXCLUDED.ai_enabled,
    description = EXCLUDED.description,
    updated_at = now();

-- Verify
SELECT setting_key, ai_enabled, updated_at
FROM public.ai_settings
WHERE setting_key = 'global_question_generation';
