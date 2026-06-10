-- KORRA | INTELLIGENCE & GROWTH SYNC (PHASE 16-25)
-- ================================================

-- 1. EXPAND PROFILES FOR COMMERCIAL CONTROL
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS low_credit_threshold INTEGER DEFAULT 10,
ADD COLUMN IF NOT EXISTS custom_client_price FLOAT DEFAULT 0.50,
ADD COLUMN IF NOT EXISTS billing_currency TEXT DEFAULT 'USD';

-- 2. TRANSACTION LEDGER (Phase 19)
CREATE TABLE IF NOT EXISTS public.transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
  amount FLOAT NOT NULL,
  currency TEXT DEFAULT 'USD',
  type TEXT NOT NULL, -- 'bundle_purchase', 'single_scan_payment'
  credits_added INTEGER DEFAULT 0,
  reference TEXT UNIQUE,
  status TEXT DEFAULT 'success',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. PROMO CODES (Phase 18)
CREATE TABLE IF NOT EXISTS public.promo_codes (
  code TEXT PRIMARY KEY,
  discount_percent INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  expires_at TIMESTAMPTZ
);

-- 4. SECURITY (RLS)
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Own Transactions" ON public.transactions FOR SELECT USING (auth.uid() = user_id);

-- 5. UPGRADE MEASUREMENTS FOR INTELLIGENCE (Phase 23)
ALTER TABLE public.measurements
ADD COLUMN IF NOT EXISTS body_shape TEXT,
ADD COLUMN IF NOT EXISTS size_recommendation TEXT;
