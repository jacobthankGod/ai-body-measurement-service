-- 006_expert_mode_migration.sql
-- Collaborative Accuracy: The "Expert Mode" Feedback Loop
-- Applied: 2026-07-01

-- 1. Add algorithm contributor flag to profiles
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS is_algorithm_contributor BOOLEAN DEFAULT FALSE;

-- 2. Index for admin lookups
CREATE INDEX IF NOT EXISTS idx_profiles_is_algorithm_contributor
ON public.profiles (is_algorithm_contributor)
WHERE is_algorithm_contributor IS TRUE;

-- 3. Update RLS (Ensure only admins or self can update, but everyone can read if needed)
-- Note: Profiles already have existing RLS.
-- Standard policy: "Users can update own profile" and "Service role can do everything"

COMMENT ON COLUMN public.profiles.is_algorithm_contributor IS 'If true, user can edit measurements to feed the back-calculation engine.';
