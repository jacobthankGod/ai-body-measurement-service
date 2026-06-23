-- ==========================================
-- BILLING 100% IMPLEMENTATION - Database Schema
-- ==========================================
-- Run this in your Supabase SQL Editor to add missing
-- billing infrastructure for global commercial readiness.

-- 1. LOCALIZED PRICING TABLE
-- Regional credit price matrix with VAT rates
CREATE TABLE IF NOT EXISTS public.localized_pricing (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  country_code TEXT NOT NULL,
  country_name TEXT NOT NULL,
  currency TEXT NOT NULL,
  currency_symbol TEXT NOT NULL,
  credits_per_scan INTEGER NOT NULL,
  unit_price_smallest INTEGER NOT NULL, -- Price in smallest currency unit (kobo, cents, etc.)
  vat_rate REAL DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  effective_from TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(country_code)
);

-- Insert regional pricing data
INSERT INTO public.localized_pricing (country_code, country_name, currency, currency_symbol, credits_per_scan, unit_price_smallest, vat_rate) VALUES
  ('NG', 'Nigeria', 'NGN', '₦', 1, 500, 0.075),
  ('GH', 'Ghana', 'GHS', '₵', 1, 8, 0.15),
  ('KE', 'Kenya', 'KES', 'KSh', 1, 150, 0.16),
  ('US', 'United States', 'USD', '$', 5, 50, 0.0),
  ('UK', 'United Kingdom', 'GBP', '£', 5, 40, 0.20),
  ('DE', 'Germany', 'EUR', '€', 5, 45, 0.19),
  ('FR', 'France', 'EUR', '€', 5, 45, 0.20),
  ('IT', 'Italy', 'EUR', '€', 5, 45, 0.22),
  ('ES', 'Spain', 'EUR', '€', 5, 45, 0.21),
  ('NL', 'Netherlands', 'EUR', '€', 5, 45, 0.21),
  ('CA', 'Canada', 'CAD', 'C$', 5, 65, 0.13),
  ('AU', 'Australia', 'AUD', 'A$', 5, 75, 0.10),
  ('IN', 'India', 'INR', '₹', 1, 42, 0.18)
ON CONFLICT (country_code) DO UPDATE SET
  unit_price_smallest = EXCLUDED.unit_price_smallest,
  vat_rate = EXCLUDED.vat_rate;

-- 2. EXPAND INVOICES TABLE WITH TAX FIELDS
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS subtotal INTEGER;
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS tax_amount INTEGER;
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS tax_rate REAL;
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS credits_purchased INTEGER;
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS credits_price_per_unit INTEGER;
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS paystack_customer_code TEXT;
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS invoice_pdf_url TEXT;
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS line_items JSONB;
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS billing_country TEXT;
ALTER TABLE public.invoices ADD COLUMN IF NOT EXISTS receipt_generated_at TIMESTAMPTZ;

-- 3. SUBSCRIPTIONS ENHANCEMENTS
ALTER TABLE public.subscriptions ADD COLUMN IF NOT EXISTS billing_country TEXT;
ALTER TABLE public.subscriptions ADD COLUMN IF NOT EXISTS billing_address JSONB;
ALTER TABLE public.subscriptions ADD COLUMN IF NOT EXISTS cancel_at_period_end BOOLEAN DEFAULT false;
ALTER TABLE public.subscriptions ADD COLUMN IF NOT EXISTS canceled_at TIMESTAMPTZ;
ALTER TABLE public.subscriptions ADD COLUMN IF NOT EXISTS previous_plan_id TEXT;
ALTER TABLE public.subscriptions ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN DEFAULT true;

-- 4. PROFILE TAX FIELDS
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS tax_id TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS billing_address JSONB;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTSvat_number TEXT;

-- 5. ADD INDEXES FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON public.invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON public.invoices(paid_at DESC);
CREATE INDEX IF NOT EXISTS idx_invoices_paystack_ref ON public.invoices(paystack_reference);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);

-- 6. ENABLE RLS ON NEW TABLES
ALTER TABLE public.localized_pricing ENABLE ROW LEVEL SECURITY;

-- Localized pricing: Public can read, only admins can write
CREATE POLICY "Public pricing viewable by everyone" ON public.localized_pricing FOR SELECT USING (true);
CREATE POLICY "Admins can manage pricing" ON public.localized_pranapricing FOR ALL
  USING (auth.uid() IN (SELECT id FROM auth.users WHERE email LIKE '%@korra%'));

-- 7. UPDATE EXISTING INVOICES WITH TAX DATA (Migration)
UPDATE public.invoices 
SET 
  subtotal = amount_paid,
  tax_rate = 0.075,
  tax_amount = (amount_paid * 0.075 / 1.075)::integer,
  line_items = jsonb_build_array(
    jsonb_build_object('description', 'Scan Credits', 'amount', (amount_paid - (amount_paid * 0.075 / 1.075)::integer)),
    jsonb_build_object('description', 'VAT (7.5%)', 'amount', (amount_paid * 0.075 / 1.075)::integer)
  )
WHERE subtotal IS NULL AND amount_paid > 0;

-- 8. CREATE FUNCTION FOR PRICE CALCULATION
CREATE OR REPLACE FUNCTION public.calculate_final_price(
  p_credits INTEGER,
  p_country_code TEXT
)
RETURNS TABLE(
  subtotal INTEGER,
  tax_rate REAL,
  tax_amount INTEGER,
  total INTEGER,
  currency TEXT,
  credits_per_scan INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    lp.unit_price_smallest * p_credits AS subtotal,
    lp.vat_rate AS tax_rate,
    (lp.unit_price_smallest * p_credits * lp.vat_rate)::integer AS tax_amount,
    (lp.unit_price_smallest * p_credits * (1 + lp.vat_rate))::integer AS total,
    lp.currency AS currency,
    lp.credits_per_scan AS credits_per_scan
  FROM public.localized_pricing lp
  WHERE lp.country_code = p_country_code AND lp.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 9. SEED DATA FOR SUBSCRIPTIONS (If needed)
-- Ensure all existing users have subscriptions
INSERT INTO public.subscriptions (user_id, plan_id, status)
SELECT 
  id, 
  'basic', 
  'active'
FROM auth.users
WHERE id NOT IN (SELECT user_id FROM public.subscriptions)
ON CONFLICT (user_id) DO NOTHING;

-- 10. VERIFY SETUP
SELECT 
  'localized_pricing' as table_name,
  count(*) as record_count
FROM public.localized_pricing
GROUP BY table_name
UNION ALL
SELECT 
  'invoices',
  count(*)
FROM public.invoices
UNION ALL
SELECT 
  'subscriptions', 
  count(*)
FROM public.subscriptions;
