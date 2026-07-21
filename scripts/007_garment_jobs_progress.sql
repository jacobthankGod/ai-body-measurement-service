-- Phase 045/046: Add progress tracking columns to garment_jobs
-- Run this in Supabase SQL Editor AFTER supabase_garment_jobs.sql

-- ═══════════════════════════════════════════════════════════
-- 1. Progress tracking columns (Phase 045)
-- ═══════════════════════════════════════════════════════════
ALTER TABLE garment_jobs
  ADD COLUMN IF NOT EXISTS progress_stage TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS progress_pct INTEGER DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS progress_message TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS result_url TEXT DEFAULT NULL;

-- ═══════════════════════════════════════════════════════════
-- 2. Refined photo columns for VTO (Phase 152)
-- ═══════════════════════════════════════════════════════════
ALTER TABLE measurements
  ADD COLUMN IF NOT EXISTS refined_front_url TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS refined_side_url TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS refined_back_url TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS tryon_history JSONB DEFAULT '[]'::jsonb;

-- ═══════════════════════════════════════════════════════════
-- 3. VTO usage tracking table (Phase 204)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS vto_usage (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  scan_id TEXT DEFAULT NULL,
  angle TEXT DEFAULT NULL,
  rating TEXT DEFAULT NULL,
  garment_type TEXT DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for rate limiting queries
CREATE INDEX IF NOT EXISTS idx_vto_usage_user_created ON vto_usage(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_vto_usage_user_today ON vto_usage(user_id, created_at) WHERE created_at > (NOW() - INTERVAL '1 day');

-- ═══════════════════════════════════════════════════════════
-- 4. RLS for vto_usage (owner-only)
-- ═══════════════════════════════════════════════════════════
ALTER TABLE vto_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert own vto_usage"
  ON vto_usage FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can read own vto_usage"
  ON vto_usage FOR SELECT
  USING (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════
-- 5. Subscriptions table (referenced by proxy check_subscription)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  plan TEXT NOT NULL DEFAULT 'free',
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired')),
  credits INTEGER DEFAULT 0,
  expires_at TIMESTAMPTZ DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status);

ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own subscriptions"
  ON subscriptions FOR SELECT
  USING (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════
-- 6. Garment meshes storage bucket (Phase 047)
-- ═══════════════════════════════════════════════════════════
-- Run via Supabase Dashboard > Storage > New Bucket
-- Bucket name: garment_meshes
-- Public: false (signed URLs only)
-- File size limit: 50MB
-- Allowed MIME types: application/zip, model/obj, application/json
