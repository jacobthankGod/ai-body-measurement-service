-- Phase 204: VTO rate limiting table (5 per user per day)
-- Phase 200: Subscriptions table for gating VTO access

-- VTO usage tracking
CREATE TABLE IF NOT EXISTS vto_usage (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vto_usage_user_date ON vto_usage(user_id, created_at);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'trial')),
  plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'basic', 'pro', 'enterprise')),
  started_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status);

-- RLS: Users can only read their own VTO usage
ALTER TABLE vto_usage ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own vto_usage" ON vto_usage
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service role manages vto_usage" ON vto_usage
  FOR ALL USING (true) WITH CHECK (true);

-- RLS: Users can only read their own subscriptions
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own subscriptions" ON subscriptions
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service role manages subscriptions" ON subscriptions
  FOR ALL USING (true) WITH CHECK (true);
