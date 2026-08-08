-- ═══════════════════════════════════════════════════════════════
-- 012: QR Sessions Table — Persistent ephemeral scan tokens
-- ═══════════════════════════════════════════════════════════════
-- Migrates from in-memory ACTIVE_SESSIONS to persistent PostgreSQL.
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.qr_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token TEXT UNIQUE NOT NULL,
    merchant_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_name TEXT DEFAULT 'Retail Customer',
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Only admins or system-role can see all sessions.
-- Merchants don't strictly need to see the table, just the API route does.
ALTER TABLE public.qr_sessions ENABLE ROW LEVEL SECURITY;

-- Index for fast token lookup during widget verification
CREATE INDEX IF NOT EXISTS idx_qr_sessions_token ON public.qr_sessions(token);
CREATE INDEX IF NOT EXISTS idx_qr_sessions_expires_at ON public.qr_sessions(expires_at);
