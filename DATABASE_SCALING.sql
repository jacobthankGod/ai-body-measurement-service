-- KORRA | INDUSTRIAL DATABASE SCALING (PHASE 125)
-- ===============================================
-- Objective: Optimize query performance for 10,000+ monthly scan records.

-- 1. INDEXING THE BIOMETRICS JSONB COLUMN
-- GIN (Generalized Inverted Index) allows for high-speed searches inside JSON fields.
CREATE INDEX IF NOT EXISTS idx_measurements_biometrics ON public.measurements USING GIN (biometrics);

-- 2. INDEXING FOR MERCHANT LEDGER FILTERS
-- Accelerates searches by client name and scan date.
CREATE INDEX IF NOT EXISTS idx_measurements_client_name ON public.measurements (client_name);
CREATE INDEX IF NOT EXISTS idx_measurements_created_at ON public.measurements (created_at DESC);

-- 3. INDEXING FOR CLINCAL VALIDITY AUDITS
-- Speeds up reports showing scans with high Realism Index.
CREATE INDEX IF NOT EXISTS idx_measurements_realism ON public.measurements (clinical_realism_index) WHERE clinical_realism_index IS NOT NULL;

-- 4. VACUUM AND ANALYZE
-- Ensure the Postgres planner has up-to-date statistics for these new indexes.
ANALYZE public.measurements;
