-- Research Sessions Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Research Sessions Table
CREATE TABLE IF NOT EXISTS research_sessions (
    id VARCHAR(255) PRIMARY KEY,  -- Using research_ prefix IDs
    topic TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'researching',  -- researching, writing, completed, error
    progress VARCHAR(10) DEFAULT '0%',
    current_section TEXT,
    section_index INTEGER,
    total_sections INTEGER,
    content JSONB DEFAULT '{}'::jsonb,  -- Report, sections, subtopics
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions(status);
CREATE INDEX IF NOT EXISTS idx_research_sessions_updated_at ON research_sessions(updated_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_research_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS trigger_update_research_sessions_updated_at ON research_sessions;
CREATE TRIGGER trigger_update_research_sessions_updated_at
    BEFORE UPDATE ON research_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_research_sessions_updated_at();






