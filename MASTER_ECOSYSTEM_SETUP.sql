-- ==========================================
-- PRECISIONFIT 3D | MASTER ECOSYSTEM SCHEMA
-- ==========================================
-- Version: 2.1.0 (Enterprise Grade)
-- Run this in your Supabase SQL Editor to initialize
-- the complete subscription and biometric engine.

-- 1. SUBSCRIPTION PLANS REFERENCE (Immutable Tiers)
-- Defines the business logic for each plan level.
CREATE TABLE IF NOT EXISTS public.subscription_plans (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  monthly_scan_limit INTEGER NOT NULL,
  data_depth_level TEXT NOT NULL, -- basic, advanced, clinical
  price_ngn INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.subscription_plans (id, name, monthly_scan_limit, data_depth_level, price_ngn)
VALUES
  ('basic', 'Solo Tailor', 5, 'basic', 0),
  ('pro', 'Boutique Shop', 50, 'advanced', 299900),
  ('elite', 'Luxury Atelier', 250, 'clinical', 749900),
  ('enterprise', 'Global Brand', 999999, 'clinical', 0)
ON CONFLICT (id) DO UPDATE SET
  monthly_scan_limit = EXCLUDED.monthly_scan_limit,
  price_ngn = EXCLUDED.price_ngn;

-- 2. SUBSCRIPTIONS TABLE (The Paystack Bridge)
-- Tracks the live status of every merchant's plan.
CREATE TABLE IF NOT EXISTS public.subscriptions (
  user_id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  plan_id TEXT REFERENCES public.subscription_plans(id) DEFAULT 'basic',
  status TEXT DEFAULT 'active', -- active, past_due, canceled, trialing
  paystack_customer_code TEXT,
  paystack_subscription_code TEXT,
  current_period_end TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. BODY SCANS VAULT (The 104+ Biometric Vault)
-- Secure storage for client measurements and 3D digital twins.
CREATE TABLE IF NOT EXISTS public.body_scans (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  tailor_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
  client_name TEXT NOT NULL,
  client_gender TEXT NOT NULL,
  measurements JSONB NOT NULL, -- Storing 104+ metrics (circumferences, lengths, angles)
  digital_twin_vertices JSONB, -- The 3D mesh coordinate map
  front_image_url TEXT,
  side_image_url TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. INVOICES LEDGER
-- Historical payment record for merchant accounting.
CREATE TABLE IF NOT EXISTS public.invoices (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
  amount_paid INTEGER NOT NULL,
  currency TEXT DEFAULT 'NGN',
  paystack_reference TEXT UNIQUE,
  plan_id TEXT REFERENCES public.subscription_plans(id),
  paid_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. SECURITY (Row Level Security - RLS)
ALTER TABLE public.subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.body_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;

-- 5.1 Policies: Visibility rules
-- Plans: Everyone can see what plans are available
CREATE POLICY "Public plans are viewable by everyone" ON public.subscription_plans FOR SELECT USING (true);

-- Subscriptions: Users see only their own subscription status
CREATE POLICY "Users can view own subscription" ON public.subscriptions FOR SELECT USING (auth.uid() = user_id);

-- Body Scans: STRICT ISOLATION - Tailors only see their own clients
CREATE POLICY "Tailors can manage own body scans" ON public.body_scans
  FOR ALL USING (auth.uid() = tailor_id) WITH CHECK (auth.uid() = tailor_id);

-- Invoices: Users see only their own payment history
CREATE POLICY "Users can view own invoices" ON public.invoices FOR SELECT USING (auth.uid() = user_id);

-- 6. AUTOMATED ECOSYSTEM TRIGGERS
-- Ensures every new user has a basic subscription entry immediately.
CREATE OR REPLACE FUNCTION public.initialize_merchant_ecosystem()
RETURNS TRIGGER AS $$
BEGIN
  -- 1. Create Profile (handled by previous script, but kept here for safety)
  INSERT INTO public.profiles (id, full_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name')
  ON CONFLICT (id) DO NOTHING;

  -- 2. Initialize Basic Subscription
  INSERT INTO public.subscriptions (user_id, plan_id, status)
  VALUES (NEW.id, 'basic', 'active')
  ON CONFLICT (user_id) DO NOTHING;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Re-link trigger to ensure it handles the full ecosystem
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.initialize_merchant_ecosystem();

-- 7. HELPER VIEWS
-- For the Workbench Dashboard: Quickly see remaining scans
CREATE OR REPLACE VIEW public.merchant_usage_summary AS
SELECT
  s.user_id,
  p.name as plan_name,
  p.monthly_scan_limit,
  (SELECT count(*) FROM public.body_scans b
   WHERE b.tailor_id = s.user_id
   AND b.created_at >= date_trunc('month', now())) as scans_this_month
FROM public.subscriptions s
JOIN public.subscription_plans p ON s.plan_id = p.id;
