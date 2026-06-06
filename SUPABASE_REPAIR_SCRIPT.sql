-- ==========================================
-- KORRA | MASTER DATABASE REPAIR SCRIPT
-- ==========================================
-- Objective: Resolve "500 Internal Server Error" during signup by hardening
-- the profile creation trigger and ensuring all columns exist.

-- 1. CLEANUP (Removing old triggers to prevent conflicts)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- 2. HARDEN PROFILES TABLE
-- We ensure the 'credits' column exists for the $0.50/scan model.
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT,
  company_name TEXT,
  industry TEXT,
  monthly_volume TEXT,
  credits INTEGER DEFAULT 10, -- Default credits for new merchants
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure 'credits' column exists if the table was created previously without it
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='profiles' AND column_name='credits') THEN
    ALTER TABLE public.profiles ADD COLUMN credits INTEGER DEFAULT 10;
  END IF;
END $$;

-- 3. RE-IMPLEMENT TRIGGER FUNCTION
-- This function runs as SECURITY DEFINER to bypass RLS during signup.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, company_name, industry, monthly_volume, credits)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'Artisan User'),
    COALESCE(NEW.raw_user_meta_data->>'company_name', 'Independent Studio'),
    COALESCE(NEW.raw_user_meta_data->>'industry', 'custom_apparel'),
    COALESCE(NEW.raw_user_meta_data->>'monthly_volume', '0-50'),
    10 -- Initial credit gift
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. RE-ATTACH TRIGGER
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 5. API KEYS TABLE (Verification)
CREATE TABLE IF NOT EXISTS public.api_keys (
    key TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    tier TEXT NOT NULL DEFAULT 'tailor_pro',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. MEASUREMENTS TABLE (The Vault)
CREATE TABLE IF NOT EXISTS public.measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    client_name TEXT,
    height FLOAT,
    gender TEXT,
    biometrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. ENABLE RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.measurements ENABLE ROW LEVEL SECURITY;

-- 8. POLICIES (Users see only THEIR data)
DROP POLICY IF EXISTS "Own Profile" ON public.profiles;
CREATE POLICY "Own Profile" ON public.profiles FOR ALL USING (auth.uid() = id);

DROP POLICY IF EXISTS "Own API Keys" ON public.api_keys;
CREATE POLICY "Own API Keys" ON public.api_keys FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Own Vault" ON public.measurements;
CREATE POLICY "Own Vault" ON public.measurements FOR ALL USING (auth.uid() = user_id);
