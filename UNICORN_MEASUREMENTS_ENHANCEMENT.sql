-- UNICORN MEASUREMENTS TABLE ENHANCEMENT
-- Adds missing fields for dual-account ownership and scan data tracking
-- ⚠️ Run this AFTER the initial schema tables exist

-- 0. Create invitations table (if not exists) - MUST RUN FIRST
CREATE TABLE IF NOT EXISTS public.invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token TEXT UNIQUE NOT NULL,
    merchant_id UUID REFERENCES auth.users(id) NOT NULL,
    client_name TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.invitations ENABLE ROW LEVEL SECURITY;

-- Policy
DROP POLICY IF EXISTS "Merchants manage own invites" ON public.invitations;
CREATE POLICY "Merchants manage own invites" ON invitations 
    FOR ALL USING (auth.uid() = merchant_id);

-- Create index
CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_merchant ON invitations(merchant_id);

-- 1. Add missing columns to measurements table
ALTER TABLE public.measurements 
ADD COLUMN IF NOT EXISTS landmarks_3d JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS mesh_url TEXT,
ADD COLUMN IF NOT EXISTS body_shape TEXT,
ADD COLUMN IF NOT EXISTS size_recommendation TEXT,
ADD COLUMN IF NOT EXISTS source_merchant_id UUID,
ADD COLUMN IF NOT EXISTS scan_source TEXT DEFAULT 'direct', -- 'direct' | 'widget' | 'invite'
ADD COLUMN IF NOT EXISTS scan_session_id TEXT,
ADD COLUMN IF NOT EXISTS specialty TEXT DEFAULT 'standard',
ADD COLUMN IF NOT EXISTS image_front_url TEXT,
ADD COLUMN IF NOT EXISTS image_side_url TEXT,
ADD COLUMN IF NOT EXISTS quality_score FLOAT,
ADD COLUMN IF NOT EXISTS size_passport_url TEXT,
ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS shared_with UUID[] DEFAULT ARRAY[]::UUID[],
ADD COLUMN IF NOT EXISTS payment_reference TEXT,
ADD COLUMN IF NOT EXISTS created_via TEXT DEFAULT 'api', -- 'api' | 'widget' | 'share_page'
ADD COLUMN IF NOT EXISTS ip_address TEXT,
ADD COLUMN IF NOT EXISTS user_agent TEXT;

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_measurements_merchant ON measurements(source_merchant_id);
CREATE INDEX IF NOT EXISTS idx_measurements_body_shape ON measurements(body_shape);
CREATE INDEX IF NOT EXISTS idx_measurements_gender_shape ON measurements(gender, body_shape);
CREATE INDEX IF NOT EXISTS idx_measurements_created ON measurements(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_measurements_scan_session ON measurements(scan_session_id);

-- 3. Create client_scan_data table (for storing raw scan session data)
CREATE TABLE IF NOT EXISTS public.client_scan_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id), -- Client who did the scan
    merchant_id UUID REFERENCES auth.users(id), -- Merchant who invited (if any)
    invite_token TEXT REFERENCES invitations(token),
    client_name TEXT,
    height FLOAT,
    gender TEXT,
    specialty TEXT DEFAULT 'standard',
    
    -- Raw image data (stored as base64 or URLs)
    image_front_url TEXT,
    image_side_url TEXT,
    image_front_thumb TEXT,
    image_side_thumb TEXT,
    
    -- Pose detection data
    pose_quality_score FLOAT,
    pose_feedback TEXT[],
    
    -- Processing status
    status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Client device info
    device_type TEXT,
    device_model TEXT,
    os_version TEXT,
    app_version TEXT
);

-- 4. Indexes for client_scan_data
CREATE INDEX IF NOT EXISTS idx_client_scan_user ON client_scan_data(user_id);
CREATE INDEX IF NOT EXISTS idx_client_scan_merchant ON client_scan_data(merchant_id);
CREATE INDEX IF NOT EXISTS idx_client_scan_session ON client_scan_data(session_id);
CREATE INDEX IF NOT EXISTS idx_client_scan_status ON client_scan_data(status);

-- 5. Enable RLS on client_scan_data
ALTER TABLE public.client_scan_data ENABLE ROW LEVEL SECURITY;

-- 6. RLS Policies for client_scan_data
DROP POLICY IF EXISTS "Client sees own scan data" ON public.client_scan_data;
CREATE POLICY "Client sees own scan data" ON client_scan_data 
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Merchant sees invited scans" ON public.client_scan_data;
CREATE POLICY "Merchant sees invited scans" ON client_scan_data 
    FOR ALL USING (auth.uid() = merchant_id);

-- 7. Create scan_invitations tracking table
CREATE TABLE IF NOT EXISTS public.scan_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invite_token TEXT UNIQUE NOT NULL,
    merchant_id UUID REFERENCES auth.users(id) NOT NULL,
    client_email TEXT,
    client_name TEXT,
    client_phone TEXT,
    
    -- Tracking
    scan_url TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, completed, expired
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Completion data
    completed_at TIMESTAMPTZ,
    measurement_id UUID REFERENCES measurements(id),
    client_user_id UUID REFERENCES auth.users(id),
    
    -- Channel tracking
    channel TEXT DEFAULT 'email', -- email, whatsapp, sms, link
    send_count INTEGER DEFAULT 0,
    last_sent_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Indexes for scan_invitations
CREATE INDEX IF NOT EXISTS idx_scan_inv_token ON scan_invitations(invite_token);
CREATE INDEX IF NOT EXISTS idx_scan_inv_merchant ON scan_invitations(merchant_id);
CREATE INDEX IF NOT EXISTS idx_scan_inv_client_email ON scan_invitations(client_email);
CREATE INDEX IF NOT EXISTS idx_scan_inv_status ON scan_invitations(status);

-- 9. Enable RLS
ALTER TABLE public.scan_invitations ENABLE ROW LEVEL SECURITY;

-- 10. RLS Policies
DROP POLICY IF EXISTS "Merchant manages own invites" ON public.scan_invitations;
CREATE POLICY "Merchant manages own invites" ON scan_invitations 
    FOR ALL USING (auth.uid() = merchant_id);

-- 11. Add foreign key to measurements for dual-account linking
-- Note: user_id is already the primary, but we add source_merchant_id for tracking

-- 12. Update function to get client measurements (for client passport)
CREATE OR REPLACE FUNCTION get_client_passport_measurements(p_user_id UUID)
RETURNS TABLE(
    id UUID,
    client_name TEXT,
    height FLOAT,
    gender TEXT,
    biometrics JSONB,
    body_shape TEXT,
    size_recommendation TEXT,
    mesh_url TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.client_name,
        m.height,
        m.gender,
        m.biometrics,
        m.body_shape,
        m.size_recommendation,
        m.mesh_url,
        m.created_at
    FROM measurements m
    WHERE m.user_id = p_user_id
    ORDER BY m.created_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 13. Function to get merchant's client measurements
CREATE OR REPLACE FUNCTION get_merchant_clients(p_merchant_id UUID)
RETURNS TABLE(
    measurement_id UUID,
    client_name TEXT,
    client_user_id UUID,
    height FLOAT,
    gender TEXT,
    biometrics JSONB,
    body_shape TEXT,
    size_recommendation TEXT,
    created_at TIMESTAMPTZ,
    last_scan TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.client_name,
        m.user_id,
        m.height,
        m.gender,
        m.biometrics,
        m.body_shape,
        m.size_recommendation,
        m.created_at,
        MAX(m.created_at) OVER(PARTITION BY m.user_id) as last_scan
    FROM measurements m
    WHERE m.source_merchant_id = p_merchant_id OR m.user_id = p_merchant_id
    ORDER BY m.created_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 14. Create view for client size passport
CREATE OR REPLACE VIEW client_size_passport AS
SELECT 
    m.user_id as client_id,
    m.client_name,
    m.height,
    m.gender,
    m.biometrics,
    m.body_shape,
    m.size_recommendation,
    m.mesh_url,
    m.created_at as scan_date,
    m.source_merchant_id as merchant_id,
    (SELECT company_name FROM profiles p WHERE p.id = m.source_merchant_id) as merchant_name
FROM measurements m
ORDER BY m.created_at DESC;

-- COMMENT documentation
COMMENT ON TABLE measurements IS 'Unicorn measurement storage with dual-account ownership';
COMMENT ON TABLE client_scan_data IS 'Raw client scan session data for audit and reprocessing';
COMMENT ON TABLE scan_invitations IS 'Invitation tracking with multi-channel support';

-- Run this migration after initial schema:
-- psql $DATABASE_URL -f UNICORN_MEASUREMENTS_ENHANCEMENT.sql
