-- ==========================================
-- PRECISIONFIT 3D | FINAL SUPABASE SCHEMA
-- ==========================================
-- Run this in your Supabase SQL Editor to initialize
-- all tables, security, and profile logic.

-- 1. USER PROFILES TABLE
-- Stores the metadata captured during the luxury onboarding flow.
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT,
  company_name TEXT,
  industry TEXT,
  monthly_volume TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. API KEYS TABLE
-- Stores the keys issued to merchants for their own apps.
CREATE TABLE IF NOT EXISTS public.api_keys (
    key TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    tier TEXT NOT NULL DEFAULT 'tailor_basic',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. USAGE LOGS TABLE
-- Tracks real-time scans and monthly quotas.
CREATE TABLE IF NOT EXISTS public.usage_logs (
    api_key TEXT PRIMARY KEY REFERENCES public.api_keys(key) ON DELETE CASCADE,
    total_count INTEGER DEFAULT 0,
    monthly_usage JSONB DEFAULT '{}'::jsonb,
    daily_usage JSONB DEFAULT '{}'::jsonb,
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. SECURITY (Row Level Security)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;

-- 5. POLICIES (Allow users to see only THEIR own data)

-- Profiles: Users can view/update their own profile
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- API Keys: Users can manage their own keys
CREATE POLICY "Users can view own keys" ON public.api_keys FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own keys" ON public.api_keys FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Usage Logs: Users can view their own stats
CREATE POLICY "Users can view own usage" ON public.usage_logs FOR SELECT
USING (EXISTS (SELECT 1 FROM public.api_keys WHERE api_keys.key = usage_logs.api_key AND api_keys.user_id = auth.uid()));

-- 6. AUTOMATED PROFILE CREATION
-- Automatically creates a entry in 'profiles' whenever a new user signs up.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, company_name, industry, monthly_volume)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'company_name',
    NEW.raw_user_meta_data->>'industry',
    NEW.raw_user_meta_data->>'monthly_volume'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to run the function on signup
CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 7. TEST DATA (Optional)
-- Uncomment below if you want a system-wide test key
-- INSERT INTO public.api_keys (key, user_id, tier) VALUES ('test_key_precision_3d_001', 'YOUR_USER_ID_HERE', 'tailor_elite');
