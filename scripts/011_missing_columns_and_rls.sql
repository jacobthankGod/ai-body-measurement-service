-- 011_missing_columns_and_rls.sql
-- Adds missing columns and RLS policies identified by deep audit
-- Safe to run multiple times (all IF NOT EXISTS)

-- 1. ADD MISSING COLUMNS TO profiles
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';

-- 2. ADD MISSING COLUMNS TO measurements
ALTER TABLE public.measurements ADD COLUMN IF NOT EXISTS client_user_id UUID;
ALTER TABLE public.measurements ADD COLUMN IF NOT EXISTS notes TEXT;

-- 3. ADD MISSING INDEXES
CREATE INDEX IF NOT EXISTS idx_measurements_user_id ON public.measurements(user_id);
CREATE INDEX IF NOT EXISTS idx_measurements_client_user_id ON public.measurements(client_user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON public.transactions(user_id);

-- 4. RLS FOR training_runs (currently exposed)
ALTER TABLE public.training_runs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "training_runs_service_select" ON public.training_runs;
CREATE POLICY "training_runs_service_select" ON public.training_runs
  FOR SELECT USING (
    auth.role() = 'service_role'
  );

DROP POLICY IF EXISTS "training_runs_service_insert" ON public.training_runs;
CREATE POLICY "training_runs_service_insert" ON public.training_runs
  FOR INSERT WITH CHECK (
    auth.role() = 'service_role'
  );

DROP POLICY IF EXISTS "training_runs_service_update" ON public.training_runs;
CREATE POLICY "training_runs_service_update" ON public.training_runs
  FOR UPDATE USING (
    auth.role() = 'service_role'
  );

-- 5. RLS FOR training_run_scans (currently exposed)
ALTER TABLE public.training_run_scans ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "training_run_scans_owner_select" ON public.training_run_scans;
CREATE POLICY "training_run_scans_owner_select" ON public.training_run_scans
  FOR SELECT USING (
    auth.role() = 'service_role'
  );

DROP POLICY IF EXISTS "training_run_scans_service_insert" ON public.training_run_scans;
CREATE POLICY "training_run_scans_service_insert" ON public.training_run_scans
  FOR INSERT WITH CHECK (
    auth.role() = 'service_role'
  );

-- 6. RLS FOR promo_codes (currently exposed)
ALTER TABLE public.promo_codes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "promo_codes_public_read" ON public.promo_codes;
CREATE POLICY "promo_codes_public_read" ON public.promo_codes
  FOR SELECT USING (true);

DROP POLICY IF EXISTS "promo_codes_service_manage" ON public.promo_codes;
CREATE POLICY "promo_codes_service_manage" ON public.promo_codes
  FOR ALL USING (
    auth.role() = 'service_role'
  );

-- 7. Verify
SELECT 'profiles.role column added' AS status
  WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'profiles' AND column_name = 'role')
UNION ALL
SELECT 'measurements.client_user_id added'
  WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'measurements' AND column_name = 'client_user_id')
UNION ALL
SELECT 'measurements.notes added'
  WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'measurements' AND column_name = 'notes');
