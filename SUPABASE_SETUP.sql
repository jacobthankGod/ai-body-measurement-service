-- SQL to set up the Supabase database for PrecisionFit 3D SaaS
-- Run this in the Supabase SQL Editor

-- 1. Create API Keys table
CREATE TABLE IF NOT EXISTS public.api_keys (
    key TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'tailor_basic',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create Usage Logs table
CREATE TABLE IF NOT EXISTS public.usage_logs (
    api_key TEXT PRIMARY KEY REFERENCES public.api_keys(key) ON DELETE CASCADE,
    total_count INTEGER DEFAULT 0,
    monthly_usage JSONB DEFAULT '{}'::jsonb,
    daily_usage JSONB DEFAULT '{}'::jsonb,
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Enable RLS (Row Level Security)
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;

-- 4. Create policies (allowing service role to manage everything)
-- Note: Vercel will use the service_role key to bypass RLS, but we set these for safety
CREATE POLICY "Allow service role full access to api_keys" ON public.api_keys
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow service role full access to usage_logs" ON public.usage_logs
    FOR ALL USING (true) WITH CHECK (true);

-- 5. Insert a test key
INSERT INTO public.api_keys (key, user_id, tier, is_active)
VALUES ('test_key_precision_3d_001', 'test_user', 'tailor_elite', true)
ON CONFLICT (key) DO NOTHING;
