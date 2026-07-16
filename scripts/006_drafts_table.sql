-- ═══════════════════════════════════════════════════════════════
-- 006: Drafts Table — Save scan-in-progress as draft
-- ═══════════════════════════════════════════════════════════════
-- Users can save their in-progress scans (photos + form fields)
-- to continue later. Photos stored in scan_photos bucket under
-- drafts/{userId}/{draftId}_{side}.jpg.
-- ═══════════════════════════════════════════════════════════════

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drafts table
CREATE TABLE IF NOT EXISTS public.drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_name TEXT DEFAULT '',
    height NUMERIC,
    gender TEXT DEFAULT '',
    front_photo_url TEXT DEFAULT '',
    side_photo_url TEXT DEFAULT '',
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'completed', 'discarded')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: users can only see/edit their own drafts
ALTER TABLE public.drafts ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'drafts' AND policyname = 'Users can view own drafts'
    ) THEN
        CREATE POLICY "Users can view own drafts"
            ON public.drafts FOR SELECT
            USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'drafts' AND policyname = 'Users can insert own drafts'
    ) THEN
        CREATE POLICY "Users can insert own drafts"
            ON public.drafts FOR INSERT
            WITH CHECK (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'drafts' AND policyname = 'Users can update own drafts'
    ) THEN
        CREATE POLICY "Users can update own drafts"
            ON public.drafts FOR UPDATE
            USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'drafts' AND policyname = 'Users can delete own drafts'
    ) THEN
        CREATE POLICY "Users can delete own drafts"
            ON public.drafts FOR DELETE
            USING (auth.uid() = user_id);
    END IF;
END $$;

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_drafts_user_id ON public.drafts(user_id);
CREATE INDEX IF NOT EXISTS idx_drafts_status ON public.drafts(status);
