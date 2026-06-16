-- KORRA | USER ONBOARDING INFRASTRUCTURE (8 PHASES)
-- ===============================================

-- 1. COUNTRIES REFERENCE TABLE (MANDATORY)
CREATE TABLE IF NOT EXISTS public.countries_reference (
    code TEXT PRIMARY KEY, -- ISO 2-letter code
    name TEXT NOT NULL,
    region_supported TEXT, -- Continent/Region
    default_currency TEXT DEFAULT 'USD',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed Initial Countries (Expand as needed)
INSERT INTO public.countries_reference (code, name, region_supported, default_currency) VALUES
('US', 'United States', 'North America', 'USD'),
('GB', 'United Kingdom', 'Europe', 'GBP'),
('NG', 'Nigeria', 'Africa', 'NGN'),
('IT', 'Italy', 'Europe', 'EUR'),
('FR', 'France', 'Europe', 'EUR'),
('CN', 'China', 'Asia', 'CNY'),
('JP', 'Japan', 'Asia', 'JPY'),
('IN', 'India', 'Asia', 'INR'),
('AE', 'United Arab Emirates', 'Middle East', 'AED')
ON CONFLICT (code) DO NOTHING;

-- 2. INDUSTRY VERTICALS REFERENCE TABLE
CREATE TABLE IF NOT EXISTS public.industry_verticals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sub_specialties JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed Industry Verticals from Reference
INSERT INTO public.industry_verticals (id, name, sub_specialties) VALUES
('luxury_mtm', 'Luxury Made-To-Measure', '["Bespoke suits", "Hand-stitched leather", "Custom shirts", "Overcoats"]'),
('bridal', 'Bridal & Tuxedo', '["Wedding gowns", "Bridesmaid dresses", "Groom formal wear", "Cultural attire"]'),
('rtw', 'Ready-To-Wear', '["Casual wear", "Sportswear", "Corporate attire", "Kidswear", "Sustainable fashion"]'),
('manufacturing', 'On-Demand Manufacturing', '["Mass production", "Technical textiles", "Workwear", "PPE"]'),
('custom_apparel', 'Custom Apparel', '["Sports teams", "Theatrical costuming", "Dance costumes", "Military uniforms"]'),
('healthcare', 'Healthcare & Fitness', '["Surgical gowns", "Medical scrubs", "Activewear", "Yoga gear"]'),
('fashion_tech', 'Fashion Technology', '["3D body scanning", "Virtual try-on", "Smart textiles", "Digital fashion"]')
ON CONFLICT (id) DO NOTHING;

-- 3. EXPAND PROFILES FOR ONBOARDING DATA (Phase 2-8)
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS account_type TEXT CHECK (account_type IN ('individual', 'artisan', 'merchant', 'enterprise')),
ADD COLUMN IF NOT EXISTS country_code TEXT REFERENCES public.countries_reference(code),
ADD COLUMN IF NOT EXISTS region TEXT,
ADD COLUMN IF NOT EXISTS currency TEXT DEFAULT 'USD',
ADD COLUMN IF NOT EXISTS business_type TEXT CHECK (business_type IN ('retail', 'wholesale', 'manufacturing')),
ADD COLUMN IF NOT EXISTS business_address TEXT,
ADD COLUMN IF NOT EXISTS industry_vertical_id TEXT REFERENCES public.industry_verticals(id),
ADD COLUMN IF NOT EXISTS selected_sub_specialties JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS unit_preference TEXT DEFAULT 'metric' CHECK (unit_preference IN ('metric', 'imperial')),
ADD COLUMN IF NOT EXISTS measurement_standard TEXT DEFAULT 'standard',
ADD COLUMN IF NOT EXISTS selected_plan TEXT DEFAULT 'starter',
ADD COLUMN IF NOT EXISTS onboarding_phase INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ;

-- 4. SECURITY (RLS)
ALTER TABLE public.countries_reference ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.industry_verticals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read for reference tables" ON public.countries_reference FOR SELECT USING (true);
CREATE POLICY "Allow public read for industry verticals" ON public.industry_verticals FOR SELECT USING (true);

-- 5. INDEXING FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_profile_onboarding_phase ON public.profiles(onboarding_phase);
CREATE INDEX IF NOT EXISTS idx_profile_country ON public.profiles(country_code);

-- 6. VERIFICATION COMMENT
COMMENT ON TABLE public.countries_reference IS 'Mandatory reference table for geographic context in onboarding.';
