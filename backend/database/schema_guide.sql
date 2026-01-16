-- Guided Learning Feature Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Guide Sessions Table
CREATE TABLE IF NOT EXISTS guide_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notebook_ids UUID[] NOT NULL,  -- Array of notebook IDs
    current_step INTEGER DEFAULT 1,
    total_steps INTEGER,
    status VARCHAR(50) DEFAULT 'active',  -- active, completed, paused
    content JSONB,  -- Generated learning content (steps, topics, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fix existing table if it was created without proper defaults
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'guide_sessions') THEN
        -- Fix id column default
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'guide_sessions' 
            AND column_name = 'id' 
            AND column_default LIKE '%uuid_generate_v4%'
        ) THEN
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
    END IF;
END $$;

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_guide_sessions_status ON guide_sessions(status);
CREATE INDEX IF NOT EXISTS idx_guide_sessions_created_at ON guide_sessions(created_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_guide_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER trigger_update_guide_sessions_updated_at
    BEFORE UPDATE ON guide_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_guide_sessions_updated_at();

-- Add comments
COMMENT ON TABLE guide_sessions IS 'Guided learning sessions created from notebooks';
COMMENT ON COLUMN guide_sessions.notebook_ids IS 'Array of notebook UUIDs used to generate the guide';
COMMENT ON COLUMN guide_sessions.content IS 'JSON structure containing learning steps, topics, and content';
COMMENT ON COLUMN guide_sessions.status IS 'Session status: active, completed, or paused';

