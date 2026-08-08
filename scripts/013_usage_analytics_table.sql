-- ═══════════════════════════════════════════════════════════════
-- 013: Usage Analytics Table — Capture merchant usage patterns
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.usage_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,
    action TEXT NOT NULL,
    label TEXT,
    page TEXT,
    client_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: Only admins can view analytics
ALTER TABLE public.usage_analytics ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_analytics_category ON public.usage_analytics(category);
CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON public.usage_analytics(client_timestamp);
