-- KORRA | GLOBAL USER ONBOARDING INFRASTRUCTURE
-- ===========================================
-- Objective: Comprehensive international support for all countries and industries.

-- 1. COUNTRIES REFERENCE TABLE (GLOBAL AUTHORITY)
CREATE TABLE IF NOT EXISTS public.countries_reference (
    code TEXT PRIMARY KEY, -- ISO 2-letter code
    name TEXT NOT NULL,
    region_supported TEXT, -- Continent/Region
    default_currency TEXT DEFAULT 'USD',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed Comprehensive Country List
INSERT INTO public.countries_reference (code, name, region_supported, default_currency) VALUES
('AF', 'Afghanistan', 'Asia', 'AFN'), ('AL', 'Albania', 'Europe', 'ALL'), ('DZ', 'Algeria', 'Africa', 'DZD'),
('AD', 'Andorra', 'Europe', 'EUR'), ('AO', 'Angola', 'Africa', 'AOA'), ('AG', 'Antigua and Barbuda', 'North America', 'XCD'),
('AR', 'Argentina', 'South America', 'ARS'), ('AM', 'Armenia', 'Asia', 'AMD'), ('AU', 'Australia', 'Oceania', 'AUD'),
('AT', 'Austria', 'Europe', 'EUR'), ('AZ', 'Azerbaijan', 'Asia', 'AZN'), ('BS', 'Bahamas', 'North America', 'BSD'),
('BH', 'Bahrain', 'Middle East', 'BHD'), ('BD', 'Bangladesh', 'Asia', 'BDT'), ('BB', 'Barbados', 'North America', 'BBD'),
('BY', 'Belarus', 'Europe', 'BYN'), ('BE', 'Belgium', 'Europe', 'EUR'), ('BZ', 'Belize', 'North America', 'BZD'),
('BJ', 'Benin', 'Africa', 'XOF'), ('BT', 'Bhutan', 'Asia', 'BTN'), ('BO', 'Bolivia', 'South America', 'BOB'),
('BA', 'Bosnia and Herzegovina', 'Europe', 'BAM'), ('BW', 'Botswana', 'Africa', 'BWP'), ('BR', 'Brazil', 'South America', 'BRL'),
('BN', 'Brunei', 'Asia', 'BND'), ('BG', 'Bulgaria', 'Europe', 'BGN'), ('BF', 'Burkina Faso', 'Africa', 'XOF'),
('BI', 'Burundi', 'Africa', 'BIF'), ('KH', 'Cambodia', 'Asia', 'KHR'), ('CM', 'Cameroon', 'Africa', 'XAF'),
('CA', 'Canada', 'North America', 'CAD'), ('CV', 'Cape Verde', 'Africa', 'CVE'), ('CF', 'Central African Republic', 'Africa', 'XAF'),
('TD', 'Chad', 'Africa', 'XAF'), ('CL', 'Chile', 'South America', 'CLP'), ('CN', 'China', 'Asia', 'CNY'),
('CO', 'Colombia', 'South America', 'COP'), ('KM', 'Comoros', 'Africa', 'KMF'), ('CG', 'Congo', 'Africa', 'XAF'),
('CR', 'Costa Rica', 'North America', 'CRC'), ('HR', 'Croatia', 'Europe', 'EUR'), ('CU', 'Cuba', 'North America', 'CUP'),
('CY', 'Cyprus', 'Europe', 'EUR'), ('CZ', 'Czech Republic', 'Europe', 'CZK'), ('DK', 'Denmark', 'Europe', 'DKK'),
('DJ', 'Djibouti', 'Africa', 'DJF'), ('DM', 'Dominica', 'North America', 'XCD'), ('DO', 'Dominican Republic', 'North America', 'DOP'),
('EC', 'Ecuador', 'South America', 'USD'), ('EG', 'Egypt', 'Africa', 'EGP'), ('SV', 'El Salvador', 'North America', 'USD'),
('GQ', 'Equatorial Guinea', 'Africa', 'XAF'), ('ER', 'Eritrea', 'Africa', 'ERN'), ('EE', 'Estonia', 'Europe', 'EUR'),
('ET', 'Ethiopia', 'Africa', 'ETB'), ('FJ', 'Fiji', 'Oceania', 'FJD'), ('FI', 'Finland', 'Europe', 'EUR'),
('FR', 'France', 'Europe', 'EUR'), ('GA', 'Gabon', 'Africa', 'XAF'), ('GM', 'Gambia', 'Africa', 'GMD'),
('GE', 'Georgia', 'Asia', 'GEL'), ('DE', 'Germany', 'Europe', 'EUR'), ('GH', 'Ghana', 'Africa', 'GHS'),
('GR', 'Greece', 'Europe', 'EUR'), ('GD', 'Grenada', 'North America', 'XCD'), ('GT', 'Guatemala', 'North America', 'GTQ'),
('GN', 'Guinea', 'Africa', 'GNF'), ('GW', 'Guinea-Bissau', 'Africa', 'XOF'), ('GY', 'Guyana', 'South America', 'GYD'),
('HT', 'Haiti', 'North America', 'HTG'), ('HN', 'Honduras', 'North America', 'HNL'), ('HU', 'Hungary', 'Europe', 'HUF'),
('IS', 'Iceland', 'Europe', 'ISK'), ('IN', 'India', 'Asia', 'INR'), ('ID', 'Indonesia', 'Asia', 'IDR'),
('IR', 'Iran', 'Middle East', 'IRR'), ('IQ', 'Iraq', 'Middle East', 'IQD'), ('IE', 'Ireland', 'Europe', 'EUR'),
('IL', 'Israel', 'Middle East', 'ILS'), ('IT', 'Italy', 'Europe', 'EUR'), ('JM', 'Jamaica', 'North America', 'JMD'),
('JP', 'Japan', 'Asia', 'JPY'), ('JO', 'Jordan', 'Middle East', 'JOD'), ('KZ', 'Kazakhstan', 'Asia', 'KZT'),
('KE', 'Kenya', 'Africa', 'KES'), ('KI', 'Kiribati', 'Oceania', 'AUD'), ('KP', 'North Korea', 'Asia', 'KPW'),
('KR', 'South Korea', 'Asia', 'KRW'), ('KW', 'Kuwait', 'Middle East', 'KWD'), ('KG', 'Kyrgyzstan', 'Asia', 'KGS'),
('LA', 'Laos', 'Asia', 'LAK'), ('LV', 'Latvia', 'Europe', 'EUR'), ('LB', 'Lebanon', 'Middle East', 'LBP'),
('LS', 'Lesotho', 'Africa', 'LSL'), ('LR', 'Liberia', 'Africa', 'LRD'), ('LY', 'Libya', 'Africa', 'LYD'),
('LI', 'Liechtenstein', 'Europe', 'CHF'), ('LT', 'Lithuania', 'Europe', 'EUR'), ('LU', 'Luxembourg', 'Europe', 'EUR'),
('MK', 'North Macedonia', 'Europe', 'MKD'), ('MG', 'Madagascar', 'Africa', 'MGA'), ('MW', 'Malawi', 'Africa', 'MWK'),
('MY', 'Malaysia', 'Asia', 'MYR'), ('MV', 'Maldives', 'Asia', 'MVR'), ('ML', 'Mali', 'Africa', 'XOF'),
('MT', 'Malta', 'Europe', 'EUR'), ('MH', 'Marshall Islands', 'Oceania', 'USD'), ('MR', 'Mauritania', 'Africa', 'MRU'),
('MU', 'Mauritius', 'Africa', 'MUR'), ('MX', 'Mexico', 'North America', 'MXN'), ('FM', 'Micronesia', 'Oceania', 'USD'),
('MD', 'Moldova', 'Europe', 'MDL'), ('MC', 'Monaco', 'Europe', 'EUR'), ('MN', 'Mongolia', 'Asia', 'MNT'),
('ME', 'Montenegro', 'Europe', 'EUR'), ('MA', 'Morocco', 'Africa', 'MAD'), ('MZ', 'Mozambique', 'Africa', 'MZN'),
('MM', 'Myanmar', 'Asia', 'MMK'), ('NA', 'Namibia', 'Africa', 'NAD'), ('NR', 'Nauru', 'Oceania', 'AUD'),
('NP', 'Nepal', 'Asia', 'NPR'), ('NL', 'Netherlands', 'Europe', 'EUR'), ('NZ', 'New Zealand', 'Oceania', 'NZD'),
('NI', 'Nicaragua', 'North America', 'NIO'), ('NE', 'Niger', 'Africa', 'XOF'), ('NG', 'Nigeria', 'Africa', 'NGN'),
('NO', 'Norway', 'Europe', 'NOK'), ('OM', 'Oman', 'Middle East', 'OMR'), ('PK', 'Pakistan', 'Asia', 'PKR'),
('PW', 'Palau', 'Oceania', 'USD'), ('PA', 'Panama', 'North America', 'PAB'), ('PG', 'Papua New Guinea', 'Oceania', 'PGK'),
('PY', 'Paraguay', 'South America', 'PYG'), ('PE', 'Peru', 'South America', 'PEN'), ('PH', 'Philippines', 'Asia', 'PHP'),
('PL', 'Poland', 'Europe', 'PLN'), ('PT', 'Portugal', 'Europe', 'EUR'), ('QA', 'Qatar', 'Middle East', 'QAR'),
('RO', 'Romania', 'Europe', 'RON'), ('RU', 'Russia', 'Europe', 'RUB'), ('RW', 'Rwanda', 'Africa', 'RWF'),
('KN', 'Saint Kitts and Nevis', 'North America', 'XCD'), ('LC', 'Saint Lucia', 'North America', 'XCD'),
('VC', 'Saint Vincent and the Grenadines', 'North America', 'XCD'), ('WS', 'Samoa', 'Oceania', 'WST'),
('SM', 'San Marino', 'Europe', 'EUR'), ('ST', 'Sao Tome and Principe', 'Africa', 'STN'), ('SA', 'Saudi Arabia', 'Middle East', 'SAR'),
('SN', 'Senegal', 'Africa', 'XOF'), ('RS', 'Serbia', 'Europe', 'RSD'), ('SC', 'Seychelles', 'Africa', 'SCR'),
('SL', 'Sierra Leone', 'Africa', 'SLL'), ('SG', 'Singapore', 'Asia', 'SGD'), ('SK', 'Slovakia', 'Europe', 'EUR'),
('SI', 'Slovenia', 'Europe', 'EUR'), ('SB', 'Solomon Islands', 'Oceania', 'SBD'), ('SO', 'Somalia', 'Africa', 'SOS'),
('ZA', 'South Africa', 'Africa', 'ZAR'), ('SS', 'South Sudan', 'Africa', 'SSP'), ('ES', 'Spain', 'Europe', 'EUR'),
('LK', 'Sri Lanka', 'Asia', 'LKR'), ('SD', 'Sudan', 'Africa', 'SDG'), ('SR', 'Suriname', 'South America', 'SRD'),
('SZ', 'Swaziland', 'Africa', 'SZL'), ('SE', 'Sweden', 'Europe', 'SEK'), ('CH', 'Switzerland', 'Europe', 'CHF'),
('SY', 'Syria', 'Middle East', 'SYP'), ('TW', 'Taiwan', 'Asia', 'TWD'), ('TJ', 'Tajikistan', 'Asia', 'TJS'),
('TZ', 'Tanzania', 'Africa', 'TZS'), ('TH', 'Thailand', 'Asia', 'THB'), ('TG', 'Togo', 'Africa', 'XOF'),
('TO', 'Tonga', 'Oceania', 'TOP'), ('TT', 'Trinidad and Tobago', 'North America', 'TTD'), ('TN', 'Tunisia', 'Africa', 'TND'),
('TR', 'Turkey', 'Europe', 'TRY'), ('TM', 'Turkmenistan', 'Asia', 'TMT'), ('TV', 'Tuvalu', 'Oceania', 'AUD'),
('UG', 'Uganda', 'Africa', 'UGX'), ('UA', 'Ukraine', 'Europe', 'UAH'), ('AE', 'United Arab Emirates', 'Middle East', 'AED'),
('GB', 'United Kingdom', 'Europe', 'GBP'), ('US', 'United States', 'North America', 'USD'), ('UY', 'Uruguay', 'South America', 'UYU'),
('UZ', 'Uzbekistan', 'Asia', 'UZS'), ('VU', 'Vanuatu', 'Oceania', 'VUV'), ('VA', 'Vatican City', 'Europe', 'EUR'),
('VE', 'Venezuela', 'South America', 'VES'), ('VN', 'Vietnam', 'Asia', 'VND'), ('YE', 'Yemen', 'Middle East', 'YER'),
('ZM', 'Zambia', 'Africa', 'ZMW'), ('ZW', 'Zimbabwe', 'Africa', 'ZWL')
ON CONFLICT (code) DO NOTHING;

-- 2A. PRODUCTION METHODS REFERENCE (Industry Standard: RTW, MTM, Custom)
CREATE TABLE IF NOT EXISTS public.production_methods (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.production_methods (id, name, description) VALUES
('rtw', 'Ready-To-Wear', 'Off-the-shelf standard sizing'),
('mtm', 'Made-To-Measure', 'Custom-made to individual measurements'),
('custom', 'Custom Apparel', 'Team/specialty customization')
ON CONFLICT (id) DO NOTHING;

-- 2B. PRODUCT CATEGORIES REFERENCE
CREATE TABLE IF NOT EXISTS public.product_categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.product_categories (id, name, parent_category) VALUES
('casual', 'Casual Wear', NULL),
('sportswear', 'Sportswear & Athleisure', NULL),
('denim', 'Denim & Indigo', NULL),
('kidswear', 'Kidswear', NULL),
('modest', 'Modest Fashion', NULL),
('sustainable', 'Sustainable Fashion', NULL),
('corporate', 'Corporate Attire', NULL),
('bridal', 'Bridal & Tuxedo', NULL),
('outerwear', 'Outerwear & Jackets', NULL),
('workwear', 'Workwear & Industrial', NULL),
('healthcare', 'Healthcare & Fitness', NULL),
('uniforms', 'Uniforms', NULL),
('fashion_tech', 'Fashion Technology', NULL),
('theatrical', 'Theatrical Costuming', NULL)
ON CONFLICT (id) DO NOTHING;

-- 2C. CULTURAL ATTIRE REFERENCE (MTM country-specific)
CREATE TABLE IF NOT EXISTS public.cultural_attire (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country_code TEXT REFERENCES public.countries_reference(code),
    region TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.cultural_attire (id, name, country_code, region, description) VALUES
('bespoke_eu', 'Bespoke Suits', 'IT', 'Europe', 'Italian/European bespoke tailoring'),
('savile_row', 'Savile Row Bespoke', 'GB', 'Europe', 'British bespoke tailoring'),
('haute_couture', 'Haute Couture', 'FR', 'Europe', 'French high fashion'),
('cheongsam', 'Cheongsam/Qipao', 'CN', 'Asia', 'Chinese traditional'),
('kimono', 'Kimono', 'JP', 'Asia', 'Japanese traditional'),
('shervani', 'Shervani/Lehenga', 'IN', 'Asia', 'Indian formal wear'),
('hanbok', 'Hanbok', 'KR', 'Asia', 'Korean traditional'),
('agbada', 'Agbada/Dashiki', 'NG', 'Africa', 'Nigerian formal'),
('kente', 'Kente', 'GH', 'Africa', 'G Ghanaian traditional'),
('kilt', 'Kilt', 'GB', 'Europe', 'Scottish formal'),
('thobe', 'Thobe/Kandura', 'AE', 'Middle East', 'Middle Eastern formal'),
('shalwar', 'Shalwar Kameez', 'PK', 'Asia', 'South Asian'),
('batik', 'Batik/Kebaya', 'ID', 'Asia', 'Indonesian traditional'),
('sari', 'Sari', 'IN', 'Asia', 'Indian drape')
ON CONFLICT (id) DO NOTHING;

-- 2D. VERTICAL CATEGORIES (simplified)
CREATE TABLE IF NOT EXISTS public.industry_verticals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category_type TEXT CHECK (category_type IN ('production', 'product', 'tech')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.industry_verticals (id, name, category_type) VALUES
('rtw', 'Ready-To-Wear', 'production'),
('mtm', 'Made-To-Measure', 'production'),
('custom', 'Custom Apparel', 'production'),
('bridal', 'Bridal & Tuxedo', 'product'),
('outerwear', 'Outerwear & Jackets', 'product'),
('workwear', 'Workwear & Industrial', 'product'),
('fashion_tech', 'Fashion Technology', 'tech')
ON CONFLICT (id) DO NOTHING;

-- 2E. VERTICAL-PRODUCT MAPPING (junction table)
CREATE TABLE IF NOT EXISTS public.vertical_products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    vertical_id TEXT REFERENCES public.industry_verticals(id),
    product_category_id TEXT REFERENCES public.product_categories(id),
    UNIQUE (vertical_id, product_category_id)
);

INSERT INTO public.vertical_products (vertical_id, product_category_id) VALUES
('rtw', 'casual'), ('rtw', 'sportswear'), ('rtw', 'denim'), ('rtw', 'kidswear'),
('rtw', 'modest'), ('rtw', 'sustainable'), ('rtw', 'corporate'),
('mtm', 'casual'), ('mtm', 'corporate'),
('custom', 'uniforms'), ('custom', 'theatrical'),
('bridal', 'bridal'),
('outerwear', 'outerwear'),
('workwear', 'workwear'), ('workwear', 'healthcare'), ('workwear', 'uniforms'),
('fashion_tech', 'fashion_tech')
ON CONFLICT DO NOTHING;

-- 2F. VERTICAL-COUNTRY CONTEXT (junction table for MTM)
CREATE TABLE IF NOT EXISTS public.vertical_country_context (
    vertical_id TEXT REFERENCES public.industry_verticals(id),
    country_code TEXT REFERENCES public.countries_reference(code),
    cultural_attire_id TEXT REFERENCES public.cultural_attire(id),
    is_primary BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (vertical_id, country_code)
);

INSERT INTO public.vertical_country_context (vertical_id, country_code, cultural_attire_id, is_primary) VALUES
('mtm', 'IT', 'bespoke_eu', TRUE),
('mtm', 'GB', 'savile_row', TRUE),
('mtm', 'FR', 'haute_couture', TRUE),
('mtm', 'CN', 'cheongsam', TRUE),
('mtm', 'JP', 'kimono', TRUE),
('mtm', 'IN', 'shervani', TRUE),
('mtm', 'KR', 'hanbok', TRUE),
('mtm', 'NG', 'agbada', TRUE),
('mtm', 'GH', 'kente', TRUE),
('mtm', 'AE', 'thobe', TRUE),
('mtm', 'PK', 'shalwar', TRUE),
('mtm', 'ID', 'batik', TRUE),
('bridal', 'IN', 'sari', FALSE),
('bridal', 'CN', 'cheongsam', FALSE),
('bridal', 'JP', 'kimono', FALSE),
('bridal', 'NG', 'agbada', FALSE)
ON CONFLICT (id) DO NOTHING;

-- 3. EXPAND PROFILES FOR COMPREHENSIVE ONBOARDING DATA (Phase 2-8)
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS account_type TEXT CHECK (account_type IN ('individual', 'artisan', 'merchant', 'enterprise')),
ADD COLUMN IF NOT EXISTS country_code TEXT REFERENCES public.countries_reference(code),
ADD COLUMN IF NOT EXISTS region TEXT,
ADD COLUMN IF NOT EXISTS currency TEXT DEFAULT 'USD',
ADD COLUMN IF NOT EXISTS company_name TEXT,
ADD COLUMN IF NOT EXISTS business_type TEXT CHECK (business_type IN ('retail', 'wholesale', 'manufacturing')),
ADD COLUMN IF NOT EXISTS business_address TEXT,
ADD COLUMN IF NOT EXISTS industry_vertical_id TEXT REFERENCES public.industry_verticals(id),
ADD COLUMN IF NOT EXISTS selected_sub_specialties JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS unit_preference TEXT DEFAULT 'metric' CHECK (unit_preference IN ('metric', 'imperial')),
ADD COLUMN IF NOT EXISTS measurement_standard TEXT DEFAULT 'standard',
ADD COLUMN IF NOT EXISTS selected_plan TEXT DEFAULT 'starter',
ADD COLUMN IF NOT EXISTS onboarding_phase INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS gender TEXT,
ADD COLUMN IF NOT EXISTS age_group TEXT;

-- 4. SECURITY (RLS)
ALTER TABLE public.countries_reference ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.industry_verticals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.production_methods ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cultural_attire ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vertical_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vertical_country_context ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read for reference tables" ON public.countries_reference FOR SELECT USING (true);
CREATE POLICY "Allow public read for industry verticals" ON public.industry_verticals FOR SELECT USING (true);
CREATE POLICY "Allow public read for production methods" ON public.production_methods FOR SELECT USING (true);
CREATE POLICY "Allow public read for product categories" ON public.product_categories FOR SELECT USING (true);
CREATE POLICY "Allow public read for cultural attire" ON public.cultural_attire FOR SELECT USING (true);

-- 5. INDEXING FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_profile_onboarding_phase ON public.profiles(onboarding_phase);
CREATE INDEX IF NOT EXISTS idx_profile_country ON public.profiles(country_code);
CREATE INDEX IF NOT EXISTS idx_cultural_attire_country ON public.cultural_attire(country_code);
CREATE INDEX IF NOT EXISTS idx_vertical_country ON public.vertical_country_context(country_code);

-- 6. VERIFICATION COMMENT
COMMENT ON TABLE public.countries_reference IS 'Mandatory reference table for geographic context in onboarding.';
COMMENT ON TABLE public.industry_verticals IS 'Reference table for 7 core verticals with production/product/tech types.';
COMMENT ON TABLE public.production_methods IS 'Production method reference: RTW, MTM, Custom.';
COMMENT ON TABLE public.cultural_attire IS 'Cultural attire reference for country-specific MTM context.';
