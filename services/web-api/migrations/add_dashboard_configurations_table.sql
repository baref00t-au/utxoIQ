-- Migration: Add dashboard_configurations table
-- Description: Create table for custom monitoring dashboards
-- Date: 2024-01-15

-- Create dashboard_configurations table
CREATE TABLE IF NOT EXISTS dashboard_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    layout JSONB NOT NULL DEFAULT '{}'::jsonb,
    widgets JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    share_token VARCHAR(64) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for dashboard_configurations
CREATE INDEX IF NOT EXISTS idx_dashboard_user ON dashboard_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_share_token ON dashboard_configurations(share_token);
CREATE INDEX IF NOT EXISTS idx_dashboard_public ON dashboard_configurations(is_public);

-- Add comment to table
COMMENT ON TABLE dashboard_configurations IS 'Custom monitoring dashboards with widget configurations';

-- Add comments to columns
COMMENT ON COLUMN dashboard_configurations.id IS 'Unique dashboard identifier';
COMMENT ON COLUMN dashboard_configurations.user_id IS 'User who owns the dashboard';
COMMENT ON COLUMN dashboard_configurations.name IS 'Dashboard name';
COMMENT ON COLUMN dashboard_configurations.description IS 'Dashboard description';
COMMENT ON COLUMN dashboard_configurations.layout IS 'Dashboard layout configuration (grid settings)';
COMMENT ON COLUMN dashboard_configurations.widgets IS 'Array of widget configurations';
COMMENT ON COLUMN dashboard_configurations.is_public IS 'Whether dashboard is publicly accessible';
COMMENT ON COLUMN dashboard_configurations.share_token IS 'Unique token for public dashboard sharing';
COMMENT ON COLUMN dashboard_configurations.created_at IS 'Dashboard creation timestamp';
COMMENT ON COLUMN dashboard_configurations.updated_at IS 'Dashboard last update timestamp';
