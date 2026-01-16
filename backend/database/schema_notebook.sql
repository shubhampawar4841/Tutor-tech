-- Notebook Feature Schema
-- Run this in Supabase SQL Editor after running the main schema.sql

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Notebooks Table
CREATE TABLE IF NOT EXISTS notebooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3b82f6',  -- Hex color code
    icon VARCHAR(10) DEFAULT '📓',        -- Emoji icon
    item_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notebook Items Table
CREATE TABLE IF NOT EXISTS notebook_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notebook_id UUID NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- 'solve', 'question', 'research', 'note'
    title VARCHAR(255) NOT NULL,
    content JSONB NOT NULL,     -- Flexible content storage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add updated_at columns if tables exist but columns are missing (for existing installations)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'notebooks') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notebooks' AND column_name = 'updated_at') THEN
            ALTER TABLE notebooks ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        END IF;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'notebook_items') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notebook_items' AND column_name = 'updated_at') THEN
            ALTER TABLE notebook_items ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        END IF;
    END IF;
END $$;

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_notebook_items_notebook_id ON notebook_items(notebook_id);
CREATE INDEX IF NOT EXISTS idx_notebook_items_type ON notebook_items(type);
CREATE INDEX IF NOT EXISTS idx_notebook_items_created_at ON notebook_items(created_at DESC);

-- Function to update notebook item_count
CREATE OR REPLACE FUNCTION update_notebook_item_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE notebooks 
        SET item_count = item_count + 1,
            updated_at = NOW()
        WHERE id = NEW.notebook_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE notebooks 
        SET item_count = GREATEST(item_count - 1, 0),
            updated_at = NOW()
        WHERE id = OLD.notebook_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update item_count
CREATE TRIGGER trigger_update_notebook_item_count
    AFTER INSERT OR DELETE ON notebook_items
    FOR EACH ROW
    EXECUTE FUNCTION update_notebook_item_count();

-- Add comments
COMMENT ON TABLE notebooks IS 'User notebooks for organizing learning materials';
COMMENT ON TABLE notebook_items IS 'Items stored in notebooks (solutions, questions, research, notes)';
COMMENT ON COLUMN notebook_items.type IS 'Type of item: solve, question, research, or note';
COMMENT ON COLUMN notebook_items.content IS 'JSON content specific to item type';

