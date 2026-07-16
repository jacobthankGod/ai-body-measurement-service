-- Phase 046: Add progress columns to garment_jobs table
ALTER TABLE garment_jobs ADD COLUMN IF NOT EXISTS progress INT DEFAULT 0;
ALTER TABLE garment_jobs ADD COLUMN IF NOT EXISTS progress_message TEXT DEFAULT '';
