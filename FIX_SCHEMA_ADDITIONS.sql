-- KORRA | SCHEMA FIXES & ADDITIONS
-- ===============================

-- 1. INTEREST LEADS TABLE (Fixes 404 in Dashboard)
CREATE TABLE IF NOT EXISTS public.interest_leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT NOT NULL,
    context TEXT,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.interest_leads ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public insert for interest_leads" ON public.interest_leads FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow admin read for interest_leads" ON public.interest_leads FOR SELECT USING (auth.jwt() ->> 'email' IN ('springbionics@gmail.com', 'admin@korra.work'));

-- 2. ENSURE PROFILE ACCOUNT TYPE CHECK CONSTRAINT MATCHES PLAN
-- First, drop the old constraint if it exists (Supabase naming convention varies, but we'll try to be safe)
DO $$
BEGIN
    ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_account_type_check;
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

ALTER TABLE public.profiles
ADD CONSTRAINT profiles_account_type_check
CHECK (account_type IN ('individual', 'artisan', 'merchant', 'enterprise'));

-- 3. PERMISSIONS FOR ONBOARDING TABLES
GRANT ALL ON TABLE public.interest_leads TO anon, authenticated, service_role;
GRANT SELECT ON TABLE public.countries_reference TO anon, authenticated;
GRANT SELECT ON TABLE public.industry_verticals TO anon, authenticated;
GRANT SELECT ON TABLE public.vertical_products TO anon, authenticated;
GRANT SELECT ON TABLE public.vertical_country_context TO anon, authenticated;
GRANT SELECT ON TABLE public.cultural_attire TO anon, authenticated;
