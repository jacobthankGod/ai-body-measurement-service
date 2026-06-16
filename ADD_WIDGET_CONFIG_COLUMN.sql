-- Add widget_config column to profiles table
-- Run this in Supabase SQL Editor

ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS widget_config JSONB DEFAULT '{"primary": "#57D7C0", "theme": "dark"}'::jsonb;

-- Verify the column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'profiles' AND column_name = 'widget_config';
