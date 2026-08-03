-- Camera Kit Try-On Captures Table
-- Run this migration to create the table for storing Camera Kit captures

CREATE TABLE IF NOT EXISTS tryon_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    outfit_id TEXT,
    lens_id TEXT,
    group_id TEXT,
    photo_url TEXT NOT NULL,
    filename TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_tryon_captures_user_id ON tryon_captures(user_id);
CREATE INDEX IF NOT EXISTS idx_tryon_captures_created_at ON tryon_captures(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE tryon_captures ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Users can read their own captures
CREATE POLICY "Users can read own captures" ON tryon_captures
    FOR SELECT
    USING (auth.uid()::text = user_id OR user_id = 'anonymous');

-- Users can insert their own captures
CREATE POLICY "Users can insert own captures" ON tryon_captures
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id OR user_id = 'anonymous');

-- Users can update their own captures
CREATE POLICY "Users can update own captures" ON tryon_captures
    FOR UPDATE
    USING (auth.uid()::text = user_id);

-- Users can delete their own captures
CREATE POLICY "Users can delete own captures" ON tryon_captures
    FOR DELETE
    USING (auth.uid()::text = user_id);

-- Service role can do everything
CREATE POLICY "Service role full access" ON tryon_captures
    FOR ALL
    USING (auth.role() = 'service_role');

-- Create storage bucket for tryon captures
-- Run this in Supabase Dashboard > Storage > New Bucket

/*
Bucket Name: tryon_captures
Public: true (or false if you want signed URLs)
File Size Limit: 10MB
Allowed MIME Types: image/png, image/jpeg, image/webp
*/

-- Storage policies
-- Allow authenticated users to upload
CREATE POLICY "Allow authenticated uploads" ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id = 'tryon_captures');

-- Allow public read access
CREATE POLICY "Allow public read" ON storage.objects
    FOR SELECT
    TO public
    USING (bucket_id = 'tryon_captures');

-- Allow users to delete their own files
CREATE POLICY "Allow users to delete own files" ON storage.objects
    FOR DELETE
    TO authenticated
    USING (bucket_id = 'tryon_captures' AND (storage.foldername(name))[1] = auth.uid()::text);
