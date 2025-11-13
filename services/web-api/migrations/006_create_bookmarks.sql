-- Migration: Create bookmark tables
-- Description: Add bookmark_folders and bookmarks tables for saving insights
-- Date: 2025-11-12

-- Create bookmark_folders table
CREATE TABLE IF NOT EXISTS bookmark_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for bookmark_folders
CREATE INDEX idx_bookmark_folder_user ON bookmark_folders(user_id);
CREATE INDEX idx_bookmark_folder_created ON bookmark_folders(created_at);

-- Create bookmarks table
CREATE TABLE IF NOT EXISTS bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    insight_id VARCHAR(100) NOT NULL,
    folder_id UUID REFERENCES bookmark_folders(id) ON DELETE SET NULL,
    note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_insight_bookmark UNIQUE (user_id, insight_id)
);

-- Create indexes for bookmarks
CREATE INDEX idx_bookmark_user ON bookmarks(user_id);
CREATE INDEX idx_bookmark_insight ON bookmarks(insight_id);
CREATE INDEX idx_bookmark_folder ON bookmarks(folder_id);
CREATE INDEX idx_bookmark_created ON bookmarks(created_at);

-- Create trigger to update updated_at timestamp for bookmark_folders
CREATE OR REPLACE FUNCTION update_bookmark_folder_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_bookmark_folder_updated_at
    BEFORE UPDATE ON bookmark_folders
    FOR EACH ROW
    EXECUTE FUNCTION update_bookmark_folder_updated_at();

-- Create trigger to update updated_at timestamp for bookmarks
CREATE OR REPLACE FUNCTION update_bookmark_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_bookmark_updated_at
    BEFORE UPDATE ON bookmarks
    FOR EACH ROW
    EXECUTE FUNCTION update_bookmark_updated_at();
