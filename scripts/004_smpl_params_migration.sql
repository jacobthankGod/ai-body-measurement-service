-- 004_smpl_params_migration.sql
-- SMPL Parameter Storage + Training Infrastructure
-- Phase 0: Complete Data Capture (self-improving accuracy system)
-- Applied: 2026-07-01

-- 1. SMPL-specific columns on measurements table
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS smpl_params JSONB;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS joints_3d JSONB;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS tpose_mesh_url TEXT;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS smpl_params_version INTEGER DEFAULT 1;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS storage_uploaded_at TIMESTAMPTZ;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS dataset_version INTEGER;

-- 2. Index for fast dataset aggregation (find scans with SMPL params)
CREATE INDEX IF NOT EXISTS idx_measurements_smpl_params_not_null
    ON measurements (id)
    WHERE smpl_params IS NOT NULL;

-- 3. Composite index for stratified dataset queries (gender + height)
CREATE INDEX IF NOT EXISTS idx_measurements_gender_height_smpl
    ON measurements (gender, height)
    WHERE smpl_params IS NOT NULL;

-- 4. Composite index for body shape subgroup queries
CREATE INDEX IF NOT EXISTS idx_measurements_body_shape_gender_smpl
    ON measurements (body_shape, gender)
    WHERE smpl_params IS NOT NULL;

-- 5. Index for T-pose mesh existence queries
CREATE INDEX IF NOT EXISTS idx_measurements_tpose_mesh
    ON measurements (id)
    WHERE tpose_mesh_url IS NOT NULL;

-- 6. Index for dataset version tracking
CREATE INDEX IF NOT EXISTS idx_measurements_dataset_version
    ON measurements (dataset_version)
    WHERE dataset_version IS NOT NULL;

-- 7. Training runs metadata table
CREATE TABLE IF NOT EXISTS training_runs (
    id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL,
    dataset_version INTEGER NOT NULL,
    scan_count INTEGER NOT NULL,
    male_count INTEGER DEFAULT 0,
    female_count INTEGER DEFAULT 0,
    height_min REAL,
    height_max REAL,
    sha256_manifest TEXT,
    shape_stats JSONB,
    meas_stats JSONB,
    gmm_bic REAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running'
);

-- 8. Training run <-> scan junction table
CREATE TABLE IF NOT EXISTS training_run_scans (
    run_id INTEGER REFERENCES training_runs(id) ON DELETE CASCADE,
    scan_id UUID REFERENCES measurements(id) ON DELETE CASCADE,
    PRIMARY KEY (run_id, scan_id)
);

-- 9. Verify columns were added
DO $$
BEGIN
    RAISE NOTICE 'Migration 004_smpl_params_migration applied successfully';
END $$;
