-- 005_rls_policies.sql
-- RLS Policies for Self-Improving Accuracy System Storage
-- Apply after buckets are created via setup_storage.py

-- 1. Training data bucket: service_role only
-- (This bucket stores exported datasets — not public)
-- Note: PG <15 doesn't support IF NOT EXISTS for policies
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'training_data_service_only_select' AND tablename = 'objects') THEN
    CREATE POLICY "training_data_service_only_select" ON storage.objects FOR SELECT
      USING (bucket_id = 'training_data' AND auth.role() = 'service_role');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'training_data_service_only_insert' AND tablename = 'objects') THEN
    CREATE POLICY "training_data_service_only_insert" ON storage.objects FOR INSERT
      WITH CHECK (bucket_id = 'training_data' AND auth.role() = 'service_role');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'training_data_service_only_delete' AND tablename = 'objects') THEN
    CREATE POLICY "training_data_service_only_delete" ON storage.objects FOR DELETE
      USING (bucket_id = 'training_data' AND auth.role() = 'service_role');
  END IF;
END $$;

-- 2. Scan photos bucket: owner read
-- (Users can see their own uploads)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'scan_photos_owner_select' AND tablename = 'objects') THEN
    CREATE POLICY "scan_photos_owner_select"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'scan_photos'
        AND auth.role() = 'service_role'
        OR (auth.role() = 'authenticated'
            AND auth.uid()::text = (storage.foldername(name))[1])
    );
  END IF;
END $$;

-- 3. Meshes bucket: owner read
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'meshes_owner_select' AND tablename = 'objects') THEN
    CREATE POLICY "meshes_owner_select"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'meshes'
        AND auth.role() = 'service_role'
        OR (auth.role() = 'authenticated'
            AND auth.uid()::text = (storage.foldername(name))[1])
    );
  END IF;
END $$;

-- 4. Verify policies exist
SELECT schemaname, tablename, policyname, permissive, roles, cmd
FROM pg_policies
WHERE tablename = 'objects'
ORDER BY policyname;
