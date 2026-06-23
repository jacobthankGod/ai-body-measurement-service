-- UNICORN SYNC DATABASE SCHEMA
-- Phase 1: Foundation for Two-Way Communication

-- 1. Webhook Configs (Merchant webhook registration)
CREATE TABLE IF NOT EXISTS webhook_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    webhook_url TEXT NOT NULL,
    secret_key TEXT,
    events TEXT[] DEFAULT ARRAY['scan_completed', 'scan_request'],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Measurement Links (Client sharing with multiple merchants)
CREATE TABLE IF NOT EXISTS measurement_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    measurement_id UUID REFERENCES measurements(id) ON DELETE CASCADE,
    merchant_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    share_token TEXT UNIQUE NOT NULL,
    shared_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    views_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMPTZ
);

-- 3. Scan Requests (Merchant → Client re-scan requests)
CREATE TABLE IF NOT EXISTS scan_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    client_email TEXT NOT NULL,
    client_name TEXT,
    request_token TEXT UNIQUE NOT NULL,
    specialty TEXT DEFAULT 'standard',
    message TEXT,
    status TEXT DEFAULT 'pending', -- pending, completed, expired
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 4. Client Notifications (In-app notifications)
CREATE TABLE IF NOT EXISTS client_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL, -- scan_completed, scan_request, measurement_shared, webhook_triggered
    title TEXT NOT NULL,
    message TEXT,
    data JSONB DEFAULT '{}',
    link_url TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Email Queue (For reliable email delivery)
CREATE TABLE IF NOT EXISTS email_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    to_email TEXT NOT NULL,
    to_name TEXT,
    subject TEXT NOT NULL,
    template_type TEXT NOT NULL, -- scan_completed, scan_request, measurement_shared, verification
    data JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending', -- pending, sent, failed
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Client Accounts (Optional client registration)
CREATE TABLE IF NOT EXISTS client_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone TEXT,
    password_hash TEXT,
    merchant_id UUID REFERENCES profiles(id), -- Associated merchant
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token TEXT,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- INDEXES for performance
CREATE INDEX IF NOT EXISTS idx_webhook_configs_merchant ON webhook_configs(merchant_id);
CREATE INDEX IF NOT EXISTS idx_measurement_links_measurement ON measurement_links(measurement_id);
CREATE INDEX IF NOT EXISTS idx_measurement_links_merchant ON measurement_links(merchant_id);
CREATE INDEX IF NOT EXISTS idx_scan_requests_token ON scan_requests(request_token);
CREATE INDEX IF NOT EXISTS idx_scan_requests_email ON scan_requests(client_email);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON client_notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON client_notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status, scheduled_at);

-- Row Level Security (RLS) - Enable for data privacy
ALTER TABLE webhook_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurement_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_accounts ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own webhooks" ON webhook_configs 
    FOR SELECT USING (merchant_id = auth.uid());

CREATE POLICY "Users can view own measurement links" ON measurement_links 
    FOR SELECT USING (merchant_id = auth.uid());

CREATE POLICY "Users can view own notifications" ON client_notifications 
    FOR SELECT USING (user_id = auth.uid());

-- Function to create scan request token
CREATE OR REPLACE FUNCTION generate_scan_token()
RETURNS TEXT AS $$
DECLARE
    token TEXT;
    attempts INTEGER := 0;
BEGIN
    -- Generate unique token with max attempts
    WHILE attempts < 100 LOOP
        token := encode(gen_random_bytes(16), 'hex');
        IF NOT EXISTS (SELECT 1 FROM scan_requests WHERE request_token = token) THEN
            RETURN token;
        END IF;
        attempts := attempts + 1;
    END LOOP;
    -- Fallback: use UUID
    RETURN replace(gen_random_uuid()::TEXT, '-', '');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to generate share token
CREATE OR REPLACE FUNCTION generate_share_token()
RETURNS TEXT AS $$
DECLARE
    token TEXT;
    attempts INTEGER := 0;
BEGIN
    WHILE attempts < 100 LOOP
        token := encode(gen_random_bytes(16), 'hex');
        IF NOT EXISTS (SELECT 1 FROM measurement_links WHERE share_token = token) THEN
            RETURN token;
        END IF;
        attempts := attempts + 1;
    END LOOP;
    RETURN replace(gen_random_uuid()::TEXT, '-', '');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to add notification
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

-- Function to get unread notification count
CREATE OR REPLACE FUNCTION get_unread_notification_count(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
    count_val INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_val
    FROM client_notifications
    WHERE user_id = p_user_id AND is_read = FALSE AND is_archived = FALSE;
    RETURN count_val;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comment documentation
COMMENT ON TABLE webhook_configs IS 'Merchant webhook configurations for receiving scan notifications';
COMMENT ON TABLE measurement_links IS 'Links allowing clients to share measurements with multiple merchants';
COMMENT ON TABLE scan_requests IS 'Re-scan requests sent by merchants to clients';
COMMENT ON TABLE client_notifications IS 'In-app notifications for users';
COMMENT ON TABLE email_queue IS 'Reliable email delivery queue with retry logic';
COMMENT ON TABLE client_accounts IS 'Optional client accounts for two-way authentication';

-- Trigger function to clean up expired scan requests
CREATE OR REPLACE FUNCTION cleanup_expired_scan_requests()
RETURNS VOID AS $$
BEGIN
    UPDATE scan_requests 
    SET status = 'expired' 
    WHERE status = 'pending' AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Run cleanup on schedule (if pg_cron extension available)
-- SELECT cron.schedule('cleanup-scan-requests', '0 0 * * *', 'SELECT cleanup_expired_scan_requests()');
