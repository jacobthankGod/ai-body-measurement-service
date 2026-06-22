-- KORRA | MERCHANT BRANDING STORAGE & SCHEMA SYNC
-- ===============================================
-- Objective: Enable merchant logo persistence via Supabase Storage.

-- 1. EXTEND PROFILES TABLE (If not already in widget_config)
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS brand_logo_url TEXT;

-- 2. CREATE STORAGE BUCKET FOR BRANDING
INSERT INTO storage.buckets (id, name, public)
VALUES ('branding', 'branding', true)
ON CONFLICT (id) DO NOTHING;

-- 3. STORAGE POLICIES (RLS)
DROP POLICY IF EXISTS "Merchants can upload their own logos" ON storage.objects;
CREATE POLICY "Merchants can upload their own logos"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'branding' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

DROP POLICY IF EXISTS "Public Branding Access" ON storage.objects;
CREATE POLICY "Public Branding Access"
ON storage.objects FOR SELECT
USING (bucket_id = 'branding');

DROP POLICY IF EXISTS "Merchants can update their own logos" ON storage.objects;
CREATE POLICY "Merchants can update their own logos"
ON storage.objects FOR UPDATE
USING (bucket_id = 'branding' AND (storage.foldername(name))[1] = auth.uid()::text);

DROP POLICY IF EXISTS "Merchants can delete their own logos" ON storage.objects;
CREATE POLICY "Merchants can delete their own logos"
ON storage.objects FOR DELETE
USING (bucket_id = 'branding' AND (storage.foldername(name))[1] = auth.uid()::text);
