-- =============================================================================
-- UNICORN COMPLETE DATABASE SCHEMA
-- Run this ONE file to create all tables needed for measurement flow
-- =============================================================================

-- STEP 1: Create profiles table if not exists (required by references)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    company_name TEXT,
    full_name TEXT,
    email TEXT,
    phone TEXT[],
    avatar_url TEXT,
    brand_logo_url TEXT,
    credits INTEGER DEFAULT 0,
    account_type TEXT DEFAULT 'individual',
    default_specialty TEXT DEFAULT 'standard',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- STEP 2: Create measurements table if not exists
CREATE TABLE IF NOT EXISTS public.measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    client_name TEXT,
    height FLOAT,
    gender TEXT,
    biometrics JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- STEP 3: Create invitations table (THIS WAS MISSING)
CREATE TABLE IF NOT EXISTS public.invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token TEXT UNIQUE NOT NULL,
    merchant_id UUID REFERENCES auth.users(id) NOT NULL,
    client_name TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- STEP 4: Add unicorn-enhanced columns to measurements
ALTER TABLE public.measurements 
ADD COLUMN IF NOT EXISTS landmarks_3d JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS mesh_url TEXT,
ADD COLUMN IF NOT EXISTS body_shape TEXT,
ADD COLUMN IF NOT EXISTS size_recommendation TEXT,
ADD COLUMN IF NOT EXISTS source_merchant_id UUID,
ADD COLUMN IF NOT EXISTS scan_source TEXT DEFAULT 'direct',
ADD COLUMN IF NOT EXISTS scan_session_id TEXT,
ADD COLUMN IF NOT EXISTS specialty TEXT DEFAULT 'standard',
ADD COLUMN IF NOT EXISTS image_front_url TEXT,
ADD COLUMN IF NOT EXISTS image_side_url TEXT,
ADD COLUMN IF NOT EXISTS quality_score FLOAT,
ADD COLUMN IF NOT EXISTS size_passport_url TEXT,
ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS shared_with UUID[] DEFAULT ARRAY[]::UUID[],
ADD COLUMN IF NOT EXISTS payment_reference TEXT,
ADD COLUMN IF NOT EXISTS created_via TEXT DEFAULT 'api',
ADD COLUMN IF NOT EXISTS ip_address TEXT,
ADD COLUMN IF NOT EXISTS user_agent TEXT;

-- STEP 5: Create client_scan_data table
CREATE TABLE IF NOT EXISTS public.client_scan_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    merchant_id UUID,
    invite_token TEXT,
    client_name TEXT,
    height FLOAT,
    gender TEXT,
    specialty TEXT DEFAULT 'standard',
    image_front_url TEXT,
    image_side_url TEXT,
    image_front_thumb TEXT,
    image_side_thumb TEXT,
    pose_quality_score FLOAT,
    pose_feedback TEXT[],
    status TEXT DEFAULT 'pending',
    processing_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    device_type TEXT,
    device_model TEXT,
    os_version TEXT,
    app_version TEXT
);

-- STEP 6: Create scan_invitations tracking table
CREATE TABLE IF NOT EXISTS public.scan_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invite_token TEXT UNIQUE NOT NULL,
    merchant_id UUID NOT NULL,
    client_email TEXT,
    client_name TEXT,
    client_phone TEXT,
    scan_url TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    expires_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    measurement_id UUID,
    client_user_id UUID,
    channel TEXT DEFAULT 'email',
    send_count INTEGER DEFAULT 0,
    last_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- STEP 7: Create webhook_configs table
CREATE TABLE IF NOT EXISTS public.webhook_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID,
    webhook_url TEXT NOT NULL,
    secret_key TEXT,
    events TEXT[] DEFAULT ARRAY['scan_completed', 'scan_request'],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- STEP 8: Create measurement_links table
CREATE TABLE IF NOT EXISTS public.measurement_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    measurement_id UUID,
    merchant_id UUID,
    share_token TEXT UNIQUE NOT NULL,
    shared_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    views_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMPTZ
);

-- STEP 9: Create scan_requests table
CREATE TABLE IF NOT EXISTS public.scan_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID,
    client_email TEXT NOT NULL,
    client_name TEXT,
    request_token TEXT UNIQUE NOT NULL,
    specialty TEXT DEFAULT 'standard',
    message TEXT,
    status TEXT DEFAULT 'pending',
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- STEP 10: Create client_notifications table
CREATE TABLE IF NOT EXISTS public.client_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    data JSONB DEFAULT '{}',
    link_url TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- STEP 11: Create email_queue table
CREATE TABLE IF NOT EXISTS public.email_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    to_email TEXT NOT NULL,
    to_name TEXT,
    subject TEXT NOT NULL,
    template_type TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- STEP 12: Create client_accounts table
CREATE TABLE IF NOT EXISTS public.client_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone TEXT,
    password_hash TEXT,
    merchant_id UUID,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token TEXT,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========================================================
-- INDEXES
-- ========================================================
CREATE INDEX IF NOT EXISTS idx_measurements_user ON measurements(user_id);
CREATE INDEX IF NOT EXISTS idx_measurements_merchant ON measurements(source_merchant_id);
CREATE INDEX IF NOT EXISTS idx_measurements_body_shape ON measurements(body_shape);
CREATE INDEX IF NOT EXISTS idx_measurements_created ON measurements(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_merchant ON invitations(merchant_id);

CREATE INDEX IF NOT EXISTS idx_client_scan_user ON client_scan_data(user_id);
CREATE INDEX IF NOT EXISTS idx_client_scan_merchant ON client_scan_data(merchant_id);
CREATE INDEX IF NOT EXISTS idx_client_scan_session ON client_scan_data(session_id);

CREATE INDEX IF NOT EXISTS idx_webhook_configs_merchant ON webhook_configs(merchant_id);
CREATE INDEX IF NOT EXISTS idx_scan_requests_token ON scan_requests(request_token);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON client_notifications(user_id, is_read);

-- ========================================================
-- ROW LEVEL SECURITY
-- ========================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.client_scan_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.webhook_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.measurement_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.client_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.client_accounts ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Own Profile" ON public.profiles;
CREATE POLICY "Own Profile" ON profiles FOR ALL USING (auth.uid() = id);

DROP POLICY IF EXISTS "Own Vault" ON public.measurements;
CREATE POLICY "Own Vault" ON measurements FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Merchant manages own invites" ON public.invitations;
CREATE POLICY "Merchant manages own invites" ON invitations FOR ALL USING (auth.uid() = merchant_id);

DROP POLICY IF EXISTS "Client sees own scan data" ON public.client_scan_data;
CREATE POLICY "Client sees own scan data" ON client_scan_data FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Merchant sees own webhooks" ON public.webhook_configs;
CREATE POLICY "Merchant sees own webhooks" ON webhook_configs FOR SELECT USING (merchant_id = auth.uid());

DROP POLICY IF EXISTS "Users see own notifications" ON public.client_notifications;
CREATE POLICY "Users see own notifications" ON client_notifications FOR SELECT USING (user_id = auth.uid());

-- Functions
CREATE OR REPLACE FUNCTION generate_share_token()
RETURNS TEXT AS $$
DECLARE
    token TEXT;
BEGIN
    WHILE TRUE LOOP
        token := encode(gen_random_bytes(16), 'hex');
        IF NOT EXISTS (SELECT 1 FROM measurement_links WHERE share_token = token) THEN
            RETURN token;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION add_notification(
    p_user_id UUID,
    p_type TEXT,
    p_title TEXT,
    p_message TEXT DEFAULT NULL,
    p_data JSONB DEFAULT '{}',
    p_link_url TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    notif_id UUID;
BEGIN
    INSERT INTO client_notifications (user_id, type, title, message, data, link_url)
    VALUES (p_user_id, p_type, p_title, p_message, p_data, p_link_url)
    RETURNING id INTO notif_id;
    RETURN notif_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comments
COMMENT ON TABLE measurements IS 'Measurement storage with dual-account ownership';
COMMENT ON TABLE client_scan_data IS 'Raw client scan session data for audit';
COMMENT ON TABLE scan_invitations IS 'Invitation tracking with multi-channel support';
COMMENT ON TABLE client_notifications IS 'In-app notifications for users';

-- Run this one file:
-- psql $DATABASE_URL -f UNICORN_COMPLETE_SCHEMA.sql
