-- 008: Add tryon_history JSONB column to measurements table
-- Phase 175 + Phase 206

-- Add tryon_history column (JSONB array of VTO results)
ALTER TABLE public.measurements
ADD COLUMN IF NOT EXISTS tryon_history JSONB DEFAULT '[]'::jsonb;

-- Add refined_photo URLs for cached neutral views
ALTER TABLE public.measurements
ADD COLUMN IF NOT EXISTS refined_front_url TEXT,
ADD COLUMN IF NOT EXISTS refined_side_url TEXT,
ADD COLUMN IF NOT EXISTS refined_back_url TEXT;

-- Index for querying scans with VTO history
CREATE INDEX IF NOT EXISTS idx_measurements_tryon_history
ON public.measurements USING gin (tryon_history)
WHERE tryon_history != '[]'::jsonb;

-- Verify
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'measurements'
AND column_name IN ('tryon_history', 'refined_front_url', 'refined_side_url', 'refined_back_url');
