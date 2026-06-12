-- KORRA | GLOBAL IDENTITY & PASSPORT INFRASTRUCTURE (PHASE 26-30)
-- ==============================================================
-- Objective: Transition from silod Merchant data to a Global Fit Network.
-- This schema establishes the "Client" as a first-class citizen who owns their data.

-- 1. ENUM FOR USER ROLES
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('ARTISAN', 'INDIVIDUAL', 'ADMIN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. ENHANCE PROFILES FOR IDENTITY DIFFERENTIATION
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS user_type user_role DEFAULT 'INDIVIDUAL',
ADD COLUMN IF NOT EXISTS passport_id TEXT UNIQUE DEFAULT 'PF-' || upper(substring(gen_random_uuid()::text from 1 for 8));

-- 3. THE GLOBAL SIZE PASSPORT TABLE
-- This acts as the "Authority" for a user's current biometric state.
CREATE TABLE IF NOT EXISTS public.size_passports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL UNIQUE,
  current_biometrics JSONB DEFAULT '{}'::jsonb,
  body_shape TEXT,
  size_recommendation TEXT,
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  visibility TEXT DEFAULT 'private', -- 'private', 'shared', 'public'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. UPDATE MEASUREMENTS FOR DUAL-OWNERSHIP
-- A measurement is performed BY a Professional FOR a Client.
ALTER TABLE public.measurements
ADD COLUMN IF NOT EXISTS merchant_id UUID REFERENCES public.profiles(id),
ADD COLUMN IF NOT EXISTS client_id UUID REFERENCES public.profiles(id);

-- 5. ACCESS PERMISSIONS (The "Handshake" logic)
-- Allows a Client to grant a Professional access to their Passport.
CREATE TABLE IF NOT EXISTS public.passport_shares (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
  merchant_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
  status TEXT DEFAULT 'active', -- 'active', 'revoked'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(client_id, merchant_id)
);

-- 6. ATOMIC ONBOARDING TRIGGER (Updated)
-- Differentiates metadata based on signup context.
CREATE OR REPLACE FUNCTION public.korra_master_identity_handler()
RETURNS TRIGGER AS $$
DECLARE
    context_type TEXT;
BEGIN
  -- Determine role from metadata (Passed via signup.html)
  context_type := COALESCE(NEW.raw_user_meta_data->>'user_type', 'INDIVIDUAL');

  -- 1. Create Core Profile
  INSERT INTO public.profiles (id, full_name, company_name, industry, user_type, credits)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
    NEW.raw_user_meta_data->>'company_name',
    NEW.raw_user_meta_data->>'industry',
    context_type::user_role,
    CASE WHEN context_type = 'ARTISAN' THEN 0 ELSE NULL END
  );

  -- 2. If Individual, create their Size Passport (The Vault)
  IF context_type = 'INDIVIDUAL' THEN
      INSERT INTO public.size_passports (user_id)
      VALUES (NEW.id);
  END IF;

  -- 3. Standard Subscription (For Merchants only)
  IF context_type = 'ARTISAN' THEN
      INSERT INTO public.subscriptions (user_id, plan_id, status)
      VALUES (NEW.id, 'basic', 'active')
      ON CONFLICT (user_id) DO NOTHING;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Re-attach handler
DROP TRIGGER IF EXISTS on_auth_user_created_production ON auth.users;
CREATE TRIGGER on_auth_user_created_identity
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.korra_master_identity_handler();

-- 7. RLS POLICIES FOR PRIVACY
ALTER TABLE public.size_passports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.passport_shares ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Clients own passports" ON public.size_passports FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Clients manage shares" ON public.passport_shares FOR ALL USING (auth.uid() = client_id);
CREATE POLICY "Merchants view shared passports" ON public.size_passports FOR SELECT
USING (EXISTS (SELECT 1 FROM public.passport_shares WHERE passport_shares.client_id = size_passports.user_id AND passport_shares.merchant_id = auth.uid()));

-- 8. INDEXING FOR HIGH-VELOCITY NETWORKING
CREATE INDEX IF NOT EXISTS idx_passport_user ON public.size_passports(user_id);
CREATE INDEX IF NOT EXISTS idx_shares_merchant ON public.passport_shares(merchant_id);
