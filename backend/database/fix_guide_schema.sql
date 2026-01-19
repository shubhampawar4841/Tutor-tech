-- Fix Guide Sessions Schema - Add missing UUID default
-- Run this in Supabase SQL Editor to fix existing table

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Fix the id column default if table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'guide_sessions') THEN
        -- Check if default is set correctly
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'guide_sessions' 
            AND column_name = 'id' 
            AND column_default LIKE '%uuid_generate_v4%'
        ) THEN
            -- Alter the column to add default
            ALTER TABLE guide_sessions 
            ALTER COLUMN id SET DEFAULT uuid_generate_v4();
        END IF;
        
        -- Add updated_at if missing
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'guide_sessions' 
            AND column_name = 'updated_at'
        ) THEN
            ALTER TABLE guide_sessions 
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        END IF;
        
        -- Update existing rows
        UPDATE guide_sessions 
        SET updated_at = created_at 
        WHERE updated_at IS NULL;
    END IF;
END $$;

-- Create trigger function to update updated_at
CREATE OR REPLACE FUNCTION update_guide_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger if it doesn't exist
DROP TRIGGER IF EXISTS trigger_update_guide_sessions_updated_at ON guide_sessions;
CREATE TRIGGER trigger_update_guide_sessions_updated_at
    BEFORE UPDATE ON guide_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_guide_sessions_updated_at();






