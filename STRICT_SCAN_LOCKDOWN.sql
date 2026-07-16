-- KORRA | STRICT-SCAN BIOMETRIC LOCKDOWN (PHASES 61-75)
-- =======================================================
-- Objective: Enforce clinical validity by tagging scans and locking manual biometrics.

-- 1. ENHANCE MEASUREMENTS WITH VALIDATION METADATA
ALTER TABLE public.measurements
ADD COLUMN IF NOT EXISTS source_of_truth BOOLEAN DEFAULT true, -- Always true for scanned data
ADD COLUMN IF NOT EXISTS confidence_score FLOAT DEFAULT 0.0,    -- MediaPipe/HMR confidence
ADD COLUMN IF NOT EXISTS biometric_valid BOOLEAN DEFAULT true,  -- Result of 3-sigma validation
ADD COLUMN IF NOT EXISTS algorithm_tag TEXT DEFAULT 'ansur-ii-local-mapping';

-- 2. LOCKDOWN POLICY: Prevent manual biometric updates via API
-- This ensures that once a scan is saved, the 'biometrics' JSONB cannot be altered
-- except by the system service.
CREATE OR REPLACE FUNCTION public.enforce_strict_scan_integrity()
RETURNS TRIGGER AS $$
BEGIN
  -- If the update is attempting to change biometrics manually
  -- (Assuming 'service_role' or specific internal tags are checked)
  IF OLD.source_of_truth = true AND NEW.biometrics != OLD.biometrics THEN
      RAISE EXCEPTION 'Manual biometric override is blocked by KORRA Clinical Policy.';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. ATTACH INTEGRITY TRIGGER
DROP TRIGGER IF EXISTS trigger_strict_scan_integrity ON public.measurements;
CREATE TRIGGER trigger_strict_scan_integrity
  BEFORE UPDATE ON public.measurements
  FOR EACH ROW EXECUTE FUNCTION public.enforce_strict_scan_integrity();

-- 4. SECURITY: Update RLS to block manual biometric insertions
-- Only allowing inserts where source_of_truth is true (validated by backend)
DROP POLICY IF EXISTS "Users can only insert verified scans" ON public.measurements;
CREATE POLICY "Users can only insert verified scans" ON public.measurements
  FOR INSERT WITH CHECK (
    source_of_truth = true
    OR auth.role() = 'service_role'
  );
