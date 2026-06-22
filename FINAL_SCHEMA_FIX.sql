-- KORRA | FINAL SCHEMA REPAIR (PHASE 131)
-- ===============================================
-- Objective: Add missing clinical columns to ensure database parity with AI engine.

-- 1. EXTEND MEASUREMENTS TABLE WITH CLINICAL METADATA
ALTER TABLE public.measurements
ADD COLUMN IF NOT EXISTS clinical_realism_index FLOAT,
ADD COLUMN IF NOT EXISTS accuracy_certificate JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS source_of_truth BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS biometric_valid BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS algorithm_tag TEXT DEFAULT 'ansur-ii-local-mapping-v1.0';

-- 2. RE-APPLY INDEXING FOR CLINICAL VALIDITY
-- Speeds up reports showing scans with high Realism Index.
CREATE INDEX IF NOT EXISTS idx_measurements_realism
ON public.measurements (clinical_realism_index)
WHERE clinical_realism_index IS NOT NULL;

-- 3. VACUUM AND ANALYZE
ANALYZE public.measurements;
