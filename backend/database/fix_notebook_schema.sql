-- Fix Notebook Schema - Add missing columns
-- Run this in Supabase SQL Editor to fix existing tables

-- Add updated_at column to notebooks table
ALTER TABLE notebooks 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column to notebook_items table
ALTER TABLE notebook_items 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Update existing rows to have updated_at = created_at if it's null
UPDATE notebooks 
SET updated_at = created_at 
WHERE updated_at IS NULL;

UPDATE notebook_items 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- Create trigger function to update updated_at on notebooks
CREATE OR REPLACE FUNCTION update_notebooks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger function to update updated_at on notebook_items
CREATE OR REPLACE FUNCTION update_notebook_items_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
DROP TRIGGER IF EXISTS trigger_update_notebooks_updated_at ON notebooks;
CREATE TRIGGER trigger_update_notebooks_updated_at
    BEFORE UPDATE ON notebooks
    FOR EACH ROW
    EXECUTE FUNCTION update_notebooks_updated_at();

DROP TRIGGER IF EXISTS trigger_update_notebook_items_updated_at ON notebook_items;
CREATE TRIGGER trigger_update_notebook_items_updated_at
    BEFORE UPDATE ON notebook_items
    FOR EACH ROW
    EXECUTE FUNCTION update_notebook_items_updated_at();

-- Fix the update_notebook_item_count function to work with updated_at
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

-- Recreate the trigger for item_count updates
DROP TRIGGER IF EXISTS trigger_update_notebook_item_count ON notebook_items;
CREATE TRIGGER trigger_update_notebook_item_count
    AFTER INSERT OR DELETE ON notebook_items
    FOR EACH ROW
    EXECUTE FUNCTION update_notebook_item_count();









