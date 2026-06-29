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

-- 4. INITIAL DATA SEED (Phases 41-80)
INSERT INTO public.attire_profiles (name, cultural_context, gender_sharding, base_multiplier, base_static_offset)
VALUES
('Agbada', ARRAY['Tribal', 'Formal'], 'male', 1.6, 0.0),
('Senator', ARRAY['Urban', 'Formal'], 'male', 1.1, 0.0),
('Kaftan', ARRAY['Tribal', 'Daily'], 'unisex', 1.2, 0.0),
('Abaya', ARRAY['Middle Eastern', 'Modesty'], 'female', 1.0, 18.0),
('Activewear', ARRAY['Industrial', 'Sports'], 'unisex', 0.9, 0.0),
('Isi Agu', ARRAY['Tribal', 'Ceremonial'], 'male', 1.15, 0.0),
('Etibo', ARRAY['Tribal', 'Regional'], 'male', 1.1, 5.0),
('Toghu', ARRAY['Tribal', 'Regal'], 'unisex', 1.25, 0.0),
('Hanbok', ARRAY['Asian', 'Traditional'], 'female', 1.1, 10.0),
('Ao Dai', ARRAY['Asian', 'Elegant'], 'female', 1.02, 0.0),
('Kimono', ARRAY['Asian', 'Formal'], 'unisex', 1.0, 20.0),
('Yukata', ARRAY['Asian', 'Casual'], 'unisex', 1.05, 5.0),
('Gho', ARRAY['Asian', 'Regal'], 'male', 1.3, 0.0),
('Takshita', ARRAY['North African', 'Formal'], 'female', 1.15, 0.0),
('Djellaba', ARRAY['North African', 'Arid'], 'unisex', 1.25, 0.0),
('Karakou', ARRAY['North African', 'Fitted'], 'female', 1.05, 0.0),
('Jalabiya', ARRAY['Middle Eastern', 'Arid'], 'unisex', 1.35, 0.0),
('Burnous', ARRAY['North African', 'Cloak'], 'male', 1.0, 30.0),
('Melhfa', ARRAY['North African', 'Draped'], 'female', 1.0, 40.0),    -- Phase 71
('Umbhaco', ARRAY['Southern African', 'Braided'], 'female', 1.1, 0.0), -- Phase 72
('Herero', ARRAY['Southern African', 'Victorian'], 'female', 1.4, 15.0),-- Phase 73
('Basotho', ARRAY['Southern African', 'Cloak'], 'unisex', 1.0, 35.0),  -- Phase 74
('Leteise', ARRAY['Southern African', 'Stiff'], 'female', 1.08, 0.0),  -- Phase 75
('Emahiya', ARRAY['Southern African', 'Wrap'], 'unisex', 1.0, 25.0),   -- Phase 76
('Isicholo', ARRAY['Southern African', 'Headgear'], 'female', 1.0, 5.0),-- Phase 77
('Lamba', ARRAY['Southern African', 'Silk'], 'unisex', 1.2, 0.0),     -- Phase 78
('Liputa', ARRAY['Central African', 'Wax-Print'], 'female', 1.05, 10.0),-- Phase 79
('Muhuila', ARRAY['Central African', 'Beaded'], 'female', 1.0, 20.0),   -- Phase 80
('Thobe/Kandura', ARRAY['Middle Eastern', 'Daily'], 'male', 1.1, 0.0),
('Bisht', ARRAY['Middle Eastern', 'Ceremonial'], 'male', 1.0, 25.0),
('Kufiya/Ghutra', ARRAY['Middle Eastern', 'Headwear'], 'male', 1.0, 5.0),
('Fez/Tarboosh', ARRAY['North African', 'Hat'], 'male', 1.0, 3.0),
('Chador', ARRAY['Middle Eastern', 'Modesty'], 'female', 1.0, 50.0),
('Jilbab', ARRAY['Middle Eastern', 'Modesty'], 'female', 1.0, 20.0),
('Inuit Parka', ARRAY['North American', 'Arctic'], 'unisex', 1.3, 10.0),
('Native Regalia', ARRAY['North American', 'Ceremonial'], 'unisex', 1.2, 5.0),
('Cowboy', ARRAY['North American', 'Western'], 'male', 1.1, 0.0),
('Hawaiian Shirt', ARRAY['North American', 'Casual'], 'unisex', 1.1, 0.0),
('Letterman', ARRAY['North American', 'Jacket'], 'unisex', 1.12, 0.0),
('Māori Korowai', ARRAY['Oceanic', 'Cloak'], 'unisex', 1.0, 25.0),
('Piupiu', ARRAY['Oceanic', 'Skirt'], 'female', 1.05, 0.0),
('Sulu/Lava-lava', ARRAY['Oceanic', 'Wrap'], 'unisex', 1.15, 0.0),
('Driza-Bone', ARRAY['Oceanic', 'Outerwear'], 'unisex', 1.0, 15.0),
('Bush Shirt', ARRAY['Oceanic', 'Casual'], 'male', 1.1, 0.0),
('Grass Skirt', ARRAY['Oceanic', 'Ceremonial'], 'female', 1.05, 0.0),
('Lehenga Choli', ARRAY['Asian', 'Bridal'], 'female', 1.15, 0.0),
('Anarkali', ARRAY['Asian', 'Mughal'], 'female', 1.12, 0.0),
('Dhoti', ARRAY['Asian', 'Draped'], 'male', 1.1, 0.0),
('Turban/Dastar', ARRAY['Asian', 'Headwear'], 'male', 1.0, 8.0),
('Barong Tagalog', ARRAY['Asian', 'Formal'], 'male', 1.08, 0.0),
('Longyi', ARRAY['Asian', 'Wrap'], 'unisex', 1.1, 0.0),
('Sinh', ARRAY['Asian', 'Skirt'], 'female', 1.05, 0.0),
('Baju Melayu', ARRAY['Asian', 'Traditional'], 'male', 1.12, 0.0),
('Dirndl', ARRAY['European', 'Alpine'], 'female', 1.1, 5.0),
('Lederhosen', ARRAY['European', 'Leather'], 'male', 1.08, 0.0),
('Flamenco Dress', ARRAY['European', 'Gown'], 'female', 1.05, 0.0),
('Foustanella', ARRAY['European', 'Ceremonial'], 'male', 1.2, 0.0),
('Sarafan', ARRAY['European', 'Folk'], 'female', 1.15, 0.0),
('Bunad', ARRAY['European', 'Folk'], 'female', 1.1, 0.0),
('Vyshyvanka', ARRAY['European', 'Folk'], 'unisex', 1.15, 0.0),
('Aran Sweater', ARRAY['European', 'Knit'], 'unisex', 1.15, 0.0),
('Smock Frock', ARRAY['European', 'Rural'], 'male', 1.2, 0.0),
('Tweed Suit', ARRAY['European', 'Country'], 'male', 1.1, 0.0),
('Morning Tails', ARRAY['European', 'Formal'], 'male', 1.06, 0.0),
('Breton Shirt', ARRAY['European', 'Casual'], 'unisex', 1.02, 0.0),
('Huipil', ARRAY['Latin American', 'Tunic'], 'female', 1.15, 0.0),
('Poncho', ARRAY['Latin American', 'Wrap'], 'unisex', 1.0, 35.0),
('Charro Suit', ARRAY['Latin American', 'Equestrian'], 'male', 1.15, 0.0),
('Pollera', ARRAY['Latin American', 'Skirt'], 'female', 1.3, 0.0),
('Rebozo', ARRAY['Latin American', 'Shawl'], 'female', 1.0, 15.0),
('Ruana', ARRAY['Latin American', 'Poncho'], 'unisex', 1.0, 25.0),
('Faso Dan Fani', ARRAY['West African', 'Woven'], 'unisex', 1.15, 0.0),
('Kitenge', ARRAY['East African', 'Print'], 'female', 1.1, 0.0),
('Kuba Cloth', ARRAY['Central African', 'Raffia'], 'unisex', 1.1, 5.0),
('Tuxedo', ARRAY['Industrial', 'Formal'], 'male', 1.06, 0.0),
('Denim', ARRAY['Industrial', 'Casual'], 'unisex', 1.03, 0.0),
('Streetwear', ARRAY['Urban', 'Casual'], 'unisex', 1.2, 0.0),
('Swimwear', ARRAY['Industrial', 'Sports'], 'unisex', 0.9, 0.0)
ON CONFLICT (name) DO NOTHING;

-- 5. RLS POLICIES
ALTER TABLE public.attire_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tolerance_matrices ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public attire viewing" ON public.attire_profiles;
CREATE POLICY "Public attire viewing" ON public.attire_profiles FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public tolerance viewing" ON public.tolerance_matrices;
CREATE POLICY "Public tolerance viewing" ON public.tolerance_matrices FOR SELECT USING (true);
