-- KORRA | TOLERANCE INTELLIGENCE SCHEMA (PHASES 41-44)
-- ========================================================
-- Objective: Build the persistent infrastructure for 100+ global attire contexts.

-- 1. MASTER ATTIRE PROFILES TABLE
CREATE TABLE IF NOT EXISTS public.attire_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE, -- e.g., 'Agbada', 'Bespoke Suit'
    cultural_context TEXT[], -- Phase 43: ['Tribal', 'Urban', 'Formal']
    gender_sharding TEXT CHECK (gender_sharding IN ('male', 'female', 'unisex')) DEFAULT 'unisex', -- Phase 50
    base_multiplier FLOAT DEFAULT 1.0,
    base_static_offset FLOAT DEFAULT 0.0,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. TOLERANCE MATRICES (Multi-Measurement JSONB)
-- Phase 42: Store JSONB multipliers for each attire + fabric combo.
CREATE TABLE IF NOT EXISTS public.tolerance_matrices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attire_id UUID REFERENCES public.attire_profiles(id) ON DELETE CASCADE,
    material_type TEXT NOT NULL, -- e.g., 'Woven', 'Knit', 'Starch_Bazin'
    multipliers JSONB NOT NULL DEFAULT '{}'::jsonb, -- e.g., {"chest": 1.4, "waist": 1.25}
    static_offsets JSONB NOT NULL DEFAULT '{}'::jsonb, -- e.g., {"chest": 5.0, "waist": 3.0}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(attire_id, material_type)
);

-- 3. MERCHANT PREFERENCE OVERRIDES
-- Phase 44: Map attire profiles to existing merchant_id preferences.
CREATE TABLE IF NOT EXISTS public.merchant_attire_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    attire_id UUID REFERENCES public.attire_profiles(id) ON DELETE CASCADE,
    custom_multipliers JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(merchant_id, attire_id)
);

-- 4. INITIAL DATA SEED (The Pan-African 3)
INSERT INTO public.attire_profiles (name, cultural_context, gender_sharding, base_multiplier)
VALUES
('Agbada', ARRAY['Tribal', 'Formal'], 'male', 1.6),
('Senator', ARRAY['Urban', 'Formal'], 'male', 1.1),
('Kaftan', ARRAY['Tribal', 'Daily'], 'unisex', 1.2),
('Abaya', ARRAY['Middle Eastern', 'Modesty'], 'female', 1.0, 15.0), -- Phase 52: +15cm static offset
('Activewear', ARRAY['Industrial', 'Sports'], 'unisex', 0.9), -- Phase 53: -10% negative ease
('Isi Agu', ARRAY['Tribal', 'Ceremonial'], 'male', 1.15), -- Phase 55: Velvet multiplier
('Etibo', ARRAY['Tribal', 'Regional'], 'male', 1.1, 5.0), -- Phase 56: +5cm wrapper overlap
('Toghu', ARRAY['Tribal', 'Regal'], 'unisex', 1.25) -- Phase 60: Embroidery multiplier
ON CONFLICT (name) DO NOTHING;

-- 5. RLS POLICIES
ALTER TABLE public.attire_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tolerance_matrices ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public attire viewing" ON public.attire_profiles FOR SELECT USING (true);
CREATE POLICY "Public tolerance viewing" ON public.tolerance_matrices FOR SELECT USING (true);
