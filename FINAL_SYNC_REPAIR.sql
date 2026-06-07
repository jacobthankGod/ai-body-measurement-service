-- ==========================================
-- KORRA | DIGITAL TWIN INFRASTRUCTURE SYNC
-- ==========================================
-- Objective: Hardening the schema for 3D Mesh & Landmark storage.

-- 1. EXTEND MEASUREMENTS TABLE
DO $$ BEGIN
  -- Add mesh_url for .OBJ file storage
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='measurements' AND column_name='mesh_url') THEN
    ALTER TABLE public.measurements ADD COLUMN mesh_url TEXT;
  END IF;

  -- Add landmarks_3d for raw (X,Y,Z) point storage
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='measurements' AND column_name='landmarks_3d') THEN
    ALTER TABLE public.measurements ADD COLUMN landmarks_3d JSONB DEFAULT '{}'::jsonb;
  END IF;
END $$;

-- 2. STORAGE BUCKET INITIALIZATION (Instruction for Admin)
-- Please ensure you create a bucket named 'korra-meshes' in the Supabase Dashboard.

-- 3. STORAGE RLS POLICIES (Atomic Security)
-- Allow users to see only THEIR OWN meshes
DROP POLICY IF EXISTS "Users can view own meshes" ON storage.objects;
CREATE POLICY "Users can view own meshes" ON storage.objects
  FOR SELECT USING (bucket_id = 'korra-meshes' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Allow users to upload THEIR OWN meshes
DROP POLICY IF EXISTS "Users can upload own meshes" ON storage.objects;
CREATE POLICY "Users can upload own meshes" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'korra-meshes' AND auth.uid()::text = (storage.foldername(name))[1]);

-- 4. RE-HARDEN API_KEYS TABLE (Fix 406 Drift)
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='api_keys' AND column_name='is_active') THEN
    ALTER TABLE public.api_keys ADD COLUMN is_active BOOLEAN DEFAULT true;
  END IF;
END $$;
