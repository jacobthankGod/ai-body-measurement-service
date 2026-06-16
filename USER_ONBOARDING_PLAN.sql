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

-- 2. INDUSTRY VERTICALS REFERENCE TABLE
CREATE TABLE IF NOT EXISTS public.industry_verticals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sub_specialties JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed All 20 Industry Verticals from Reference Plan
INSERT INTO public.industry_verticals (id, name, sub_specialties) VALUES
('luxury_mtm', 'Luxury Made-To-Measure (MTM)', '["Bespoke suits & jackets", "Hand-stitched leather goods", "Custom shirts (Shirtmaking)", "Made-to-measure overcoats", "Personalized lining selection", "Monogram customization"]'),
('bridal', 'Bridal & Tuxedo', '["Wedding gowns", "Bridesmaid dresses", "Groom''s formal wear", "Tuxedo rentals & sales", "Flower girl / page boy outfits", "Cultural wedding attire"]'),
('rtw', 'Ready-To-Wear (RTW)', '["Casual wear (denim, t-shirts)", "Sportswear & athleisure", "Corporate attire", "Kidswear", "Maternity wear", "Petite & plus sizing", "Sustainable fashion"]'),
('manufacturing', 'Manufacturing', '["Mass production", "Technical textiles", "Workwear & uniforms", "Protective equipment (PPE)", "Medical textiles", "Automotive textiles", "Sustainable manufacturing"]'),
('custom_apparel', 'Custom Apparel', '["Sports team uniforms", "Corporate uniforms", "School uniforms", "Theatrical costuming", "Dance costumes", "Performance wear", "Military uniforms"]'),
('healthcare_fitness', 'Healthcare & Fitness', '["Surgical gowns & drapes", "Medical scrubs", "Patient wear", "Compression garments", "Orthopedic supports", "Activewear", "Swimwear", "Yoga wear"]'),
('textiles_fabrics', 'Textiles & Fabrics', '["Natural fibers (cotton, wool, silk, linen)", "Technical fabrics", "Performance textiles", "Sustainable fabrics", "Denim & indigo", "Lace & embroidery"]'),
('retail_ecommerce', 'Retail & E-commerce', '["Online fit guides", "Virtual try-on", "Size recommendation engines", "Made-to-order production", "Print-on-demand", "Customization platforms"]'),
('footwear', 'Footwear', '["Formal shoes", "Casual shoes", "Athletic footwear", "Orthopedic footwear", "Safety footwear", "Luxury bespoke"]'),
('outerwear_jackets', 'Outerwear & Jackets', '["Coats & overcoats", "Leather jackets", "Puffer jackets", "Raincoats", "Military outerwear", "Winter sports outerwear"]'),
('sportswear_athleisure', 'Sportswear & Athleisure', '["Gym & fitness wear", "Running & jogging", "Yoga & pilates", "Cycling apparel", "Swimming & aquatics", "Golf attire", "Tennis apparel"]'),
('uniforms_corporate', 'Uniforms & Corporate Apparel', '["Corporate suits", "Service uniforms", "Hospitality wear", "Front-of-house attire", "Security uniforms", "Delivery & logistics", "Airline & aviation"]'),
('childrens_wear', 'Children''s Wear', '["Newborn & infantwear", "Kids casual wear", "Kids formal wear", "School uniforms", "Baby wear", "Kids activewear"]'),
('modest_fashion', 'Modest Fashion', '["Modest dresses", "Abaya & jilbab", "Hijab fashion", "Modest swimwear", "Modest activewear", "Traditional modest wear"]'),
('sustainable_ethical', 'Sustainable & Ethical Fashion', '["Organic materials", "Recycled textiles", "Circular fashion", "Upcycled fashion", "Vegan materials", "Fair trade apparel"]'),
('workwear_industrial', 'Workwear & Industrial', '["Construction wear", "Mining & extraction", "Industrial uniforms", "Safety footwear", "Flame-resistant (FR)", "High-visibility clothing"]'),
('lingerie_intimates', 'Lingerie & Intimates', '["Bras & bralettes", "Panties & briefs", "Shapewear", "Loungewear", "Sleepwear", "Hosiery"]'),
('hat_accessory', 'Hat & Accessory Design', '["Hats & caps", "Scarves & wraps", "Leather goods", "Belts & small leather", "Ties & pocket squares", "Gloves"]'),
('denim_indigo', 'Denim & Indigo', '["Raw denim", "Selvedge denim", "Distressed denim", "Eco-denim", "Custom Denim", "Jeans customization"]'),
('fashion_tech', 'Fashion Technology', '["3D body scanning", "Virtual try-on", "AR/VR experiences", "Smart textiles", "Wearable tech", "Size recommendation AI", "Digital fashion"]')
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
COMMENT ON TABLE public.industry_verticals IS 'Reference table for all 20 industry verticals and their sub-specialties.';
