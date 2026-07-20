-- =============================================================
-- AI Settings Table, RLS Policies, and Seed Row (No DO blocks)
-- Run this in your Supabase SQL editor (or psql) once.
-- Safe to re-run due to IF EXISTS / IF NOT EXISTS usage
-- =============================================================

-- 1) Create table (id as UUID with default), if not exists
CREATE TABLE IF NOT EXISTS public.ai_settings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  setting_key text UNIQUE NOT NULL,
  ai_enabled boolean NOT NULL DEFAULT true,
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 2) Create/replace trigger function to auto-update updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3) Recreate trigger for updated_at on ai_settings (idempotent)
DROP TRIGGER IF EXISTS trg_ai_settings_updated_at ON public.ai_settings;
CREATE TRIGGER trg_ai_settings_updated_at
BEFORE UPDATE ON public.ai_settings
FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 4) Enable Row Level Security
ALTER TABLE public.ai_settings ENABLE ROW LEVEL SECURITY;

-- 5) RLS Policies (idempotent via DROP IF EXISTS)
DROP POLICY IF EXISTS "ai_settings_select" ON public.ai_settings;
CREATE POLICY "ai_settings_select" ON public.ai_settings
  FOR SELECT TO public
  USING (true);

DROP POLICY IF EXISTS "ai_settings_insert" ON public.ai_settings;
CREATE POLICY "ai_settings_insert" ON public.ai_settings
  FOR INSERT TO authenticated
  WITH CHECK (true);

DROP POLICY IF EXISTS "ai_settings_update" ON public.ai_settings;
CREATE POLICY "ai_settings_update" ON public.ai_settings
  FOR UPDATE TO authenticated
  USING (true)
  WITH CHECK (true);

-- 6) Seed/Upsert the global setting row
INSERT INTO public.ai_settings (setting_key, ai_enabled, description)
VALUES (
  'global_question_generation',
  true,
  'Global toggle for AI question generation in assignments'
)
ON CONFLICT (setting_key) DO UPDATE
SET ai_enabled = EXCLUDED.ai_enabled,
    description = EXCLUDED.description,
    updated_at = now();

-- 7) Verify
SELECT setting_key, ai_enabled, created_at, updated_at
FROM public.ai_settings
WHERE setting_key = 'global_question_generation';
