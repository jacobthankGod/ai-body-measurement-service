-- KORRA | PROFILE IMAGE STORAGE & SCHEMA SYNC
-- ===============================================
-- Objective: Enable user profile picture persistence via Supabase Storage.

-- 1. EXTEND PROFILES TABLE
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS profile_image_url TEXT;

-- 2. CREATE STORAGE BUCKET FOR PROFILES
-- Note: This requires the 'storage' schema to exist (standard in Supabase)
INSERT INTO storage.buckets (id, name, public)
VALUES ('profiles', 'profiles', true)
ON CONFLICT (id) DO NOTHING;

-- 3. STORAGE POLICIES (RLS)
-- Allow authenticated users to upload their own profile pictures
DROP POLICY IF EXISTS "Users can upload their own profile images" ON storage.objects;
CREATE POLICY "Users can upload their own profile images"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'profiles' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow public read access to profile images
DROP POLICY IF EXISTS "Public Profile Image Access" ON storage.objects;
CREATE POLICY "Public Profile Image Access"
ON storage.objects FOR SELECT
USING (bucket_id = 'profiles');

-- Allow users to update/delete their own images
DROP POLICY IF EXISTS "Users can update their own profile images" ON storage.objects;
CREATE POLICY "Users can update their own profile images"
ON storage.objects FOR UPDATE
USING (bucket_id = 'profiles' AND (storage.foldername(name))[1] = auth.uid()::text);

DROP POLICY IF EXISTS "Users can delete their own profile images" ON storage.objects;
CREATE POLICY "Users can delete their own profile images"
ON storage.objects FOR DELETE
USING (bucket_id = 'profiles' AND (storage.foldername(name))[1] = auth.uid()::text);
