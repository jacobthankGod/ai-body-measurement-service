-- ==========================================
-- KORRA | FINAL INFRASTRUCTURE SYNC
-- ==========================================
-- Objective: Fix 406 Error by ensuring table schemas match frontend code exactly.

-- 1. HARDEN API_KEYS TABLE
-- The 406 error usually means a query is asking for columns that don't exist.
CREATE TABLE IF NOT EXISTS public.api_keys (
    key TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    tier TEXT NOT NULL DEFAULT 'tailor_pro',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- Fix potential column drift
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='api_keys' AND column_name='is_active') THEN
    ALTER TABLE public.api_keys ADD COLUMN is_active BOOLEAN DEFAULT true;
  END IF;
END $$;

-- 2. HARDEN MEASUREMENTS TABLE
CREATE TABLE IF NOT EXISTS public.measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    client_name TEXT,
    height FLOAT,
    gender TEXT DEFAULT 'male',
    biometrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. ENABLE RLS
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.measurements ENABLE ROW LEVEL SECURITY;

-- 4. ATOMIC POLICIES (Users see only THEIR data)
DROP POLICY IF EXISTS "Users can view own keys" ON public.api_keys;
CREATE POLICY "Users can view own keys" ON public.api_keys FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own keys" ON public.api_keys;
CREATE POLICY "Users can create own keys" ON public.api_keys FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own keys" ON public.api_keys;
CREATE POLICY "Users can update own keys" ON public.api_keys FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Own Measurements" ON public.measurements;
CREATE POLICY "Own Measurements" ON public.measurements FOR ALL USING (auth.uid() = user_id);
