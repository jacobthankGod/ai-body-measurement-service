-- Definitive SQL for KORRA "Unicorn" UI Improvements
-- Purpose: Support persistent widget configuration and user metadata

-- 1. Extend Profiles Table with comprehensive widget configuration
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS widget_config JSONB DEFAULT '{
  "primary": "#57D7C0",
  "theme": "dark",
  "brand_name": "KORRA",
  "brand_color": "#FFFFFF",
  "logo_size": 24,
  "btn_text_fitting": "Get body measurements",
  "btn_text_measured": "Get Measured",
  "btn_color": "#57D7C0"
}'::jsonb;

-- 2. Audit Trial for Brand Changes
CREATE TABLE IF NOT EXISTS brand_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    previous_config JSONB,
    new_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 3. Security: Enable RLS for brand logs
ALTER TABLE brand_audit_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view their own brand logs" ON brand_audit_logs;
CREATE POLICY "Users can view their own brand logs" ON brand_audit_logs FOR SELECT USING (auth.uid() = user_id);

-- 4. Ensure industry verticals and account types are properly represented
-- (Assuming profiles table already has these, this is just ensuring consistency)
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS onboarding_phase INTEGER DEFAULT 1;
