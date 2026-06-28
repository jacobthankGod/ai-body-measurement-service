-- Mesh Storage Resilience Migration
-- Adds columns for Supabase Storage persistence (meshes + photos)
-- Run: psql "$POSTGRES_URL" -f scripts/003_mesh_storage_migration.sql

ALTER TABLE measurements ADD COLUMN IF NOT EXISTS mesh_storage_url TEXT;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS photo_front_url TEXT;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS photo_side_url TEXT;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS mesh_uploaded_at TIMESTAMPTZ;

-- Nullify mesh_url for scans whose mesh files were lost in the container rebuild of 2026-06-28
UPDATE measurements SET mesh_url = NULL
WHERE mesh_url IN (
  '/meshes/korra_twin_dcaa7c29-21f5-42a6-a96a-68628c179f7a.obj',
  '/meshes/korra_twin_6d9ebc67-42ec-4343-ba91-33652f824b43.obj',
  '/meshes/korra_twin_04a32ede-65f2-4c8c-b9cc-c463a66c5a3d.obj'
);

-- Verify
SELECT id, client_name, mesh_url, mesh_storage_url, photo_front_url, photo_side_url
FROM measurements
WHERE mesh_url IS NULL
   OR mesh_storage_url IS NOT NULL
   OR photo_front_url IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;
