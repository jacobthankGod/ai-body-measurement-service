-- ==========================================
-- KORRA | UNIVERSAL MASTER SYNC (PRODUCTION)
-- ==========================================
-- Objective: Wipe conflicts, unify table names, and fix signup crash.
-- Version: 3.0.0 (Mauritius-Level Hardening)

-- 1. NUCLEAR CLEANUP (Wipe old triggers/functions to prevent 500 errors)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS on_auth_user_created_v2 ON auth.users;
DROP TRIGGER IF EXISTS on_auth_user_created_production ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS public.initialize_merchant_ecosystem();
DROP FUNCTION IF EXISTS public.korra_master_onboarding();

-- 2. CORE TABLES (Ensuring everything is aligned for industrial use)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT,
  company_name TEXT,
  industry TEXT,
  monthly_volume TEXT,
  credits INTEGER DEFAULT 10,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure measurements table exists (Match Dashboard name)
CREATE TABLE IF NOT EXISTS public.measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    client_name TEXT,
    height FLOAT,
    gender TEXT DEFAULT 'male',
    biometrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. THE ATOMIC MASTER TRIGGER (Captures full metadata from Signup page)
CREATE OR REPLACE FUNCTION public.korra_master_onboarding()
RETURNS TRIGGER AS $$
BEGIN
  -- Create Profile with full metadata capture from signup.html
  INSERT INTO public.profiles (id, full_name, company_name, industry, monthly_volume, credits)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'Artisan User'),
    COALESCE(NEW.raw_user_meta_data->>'company_name', 'Independent Brand'),
    COALESCE(NEW.raw_user_meta_data->>'industry', 'luxury_mtm'),
    COALESCE(NEW.raw_user_meta_data->>'monthly_volume', '0-50'),
    10 -- Initial scan gift
  );

  -- Initialize Subscription record
  -- Note: table 'subscriptions' and 'subscription_plans' must exist from previous setup
  INSERT INTO public.subscriptions (user_id, plan_id, status)
  VALUES (NEW.id, 'basic', 'active')
  ON CONFLICT (user_id) DO NOTHING;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. RE-ATTACH ATOMIC TRIGGER
CREATE TRIGGER on_auth_user_created_production
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.korra_master_onboarding();

-- 5. RE-FIX THE SECURITY VIEW (Type-Safe & RLS Compliant)
DROP VIEW IF EXISTS public.merchant_usage_summary;
CREATE VIEW public.merchant_usage_summary
WITH (security_invoker = true) AS
SELECT
  s.user_id,
  p.name as plan_name,
  p.monthly_scan_limit,
  (SELECT count(*) FROM public.measurements m
   WHERE m.user_id::TEXT = s.user_id::TEXT
   AND m.created_at >= date_trunc('month', now())) as scans_this_month
FROM public.subscriptions s
JOIN public.subscription_plans p ON s.plan_id::TEXT = p.id::TEXT;

-- 6. SECURITY LOCKDOWN (RLS Policies)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.measurements ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Own Profile" ON public.profiles;
CREATE POLICY "Own Profile" ON public.profiles FOR ALL USING (auth.uid() = id);

DROP POLICY IF EXISTS "Own Measurements" ON public.measurements;
CREATE POLICY "Own Measurements" ON public.measurements FOR ALL USING (auth.uid() = user_id);

-- 7. VERIFICATION COMMENT
COMMENT ON FUNCTION public.korra_master_onboarding IS 'Industrial-grade onboarding trigger. Handles profile, credits, and subscriptions.';
