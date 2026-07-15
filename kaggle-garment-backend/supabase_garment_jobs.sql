-- Garment Reconstruction Job Queue
-- Run this in Supabase SQL Editor

-- ═══════════════════════════════════════════════════════════
-- 1. Job tracking table (all 6 audit fixes applied)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS garment_jobs (
  id TEXT PRIMARY KEY,
  status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  image_hash TEXT,
  include_mesh BOOLEAN DEFAULT true,
  include_pattern BOOLEAN DEFAULT true,
  result_zip BYTEA,
  result_url TEXT,          -- Supabase Storage URL (backup for large ZIPs)
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  processed_by TEXT          -- which Kaggle instance processed it
);

-- Indexes for polling, cleanup, and user queries
CREATE INDEX IF NOT EXISTS idx_garment_jobs_status ON garment_jobs(status);
CREATE INDEX IF NOT EXISTS idx_garment_jobs_created_at ON garment_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_garment_jobs_user_id ON garment_jobs(user_id);

-- ═══════════════════════════════════════════════════════════
-- 2. RLS — disabled; proxy handles auth via JWT verification
-- ═══════════════════════════════════════════════════════════
ALTER TABLE garment_jobs DISABLE ROW LEVEL SECURITY;

-- ═══════════════════════════════════════════════════════════
-- 3. Cleanup stuck jobs (stuck in "processing" for > 1 hour)
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION cleanup_stuck_garment_jobs()
RETURNS void AS $$
BEGIN
  UPDATE garment_jobs
  SET status = 'failed', error_message = 'Job timed out (stuck in processing)'
  WHERE status = 'processing' AND created_at < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════
-- 4. Cleanup old completed/failed jobs (older than 7 days)
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION cleanup_old_garment_jobs()
RETURNS void AS $$
BEGIN
  DELETE FROM garment_jobs
  WHERE status IN ('completed', 'failed')
    AND created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;
