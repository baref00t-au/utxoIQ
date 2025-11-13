-- Create intel.insights table with partitioning by created_at
-- This table stores AI-generated insights from blockchain signals

CREATE TABLE IF NOT EXISTS `intel.insights` (
  insight_id STRING NOT NULL,
  signal_id STRING NOT NULL,  -- Reference to source signal
  category STRING NOT NULL,  -- mempool|exchange|miner|whale|treasury|predictive
  headline STRING NOT NULL,  -- Max 80 chars
  summary STRING NOT NULL,  -- 2-3 sentences
  confidence FLOAT64 NOT NULL,  -- Inherited from signal (0.0 to 1.0)
  evidence STRUCT<
    block_heights ARRAY<INT64>,
    transaction_ids ARRAY<STRING>
  > NOT NULL,
  chart_url STRING,  -- Null initially, populated by chart-renderer
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(created_at)
CLUSTER BY category, confidence
OPTIONS(
  description="AI-generated insights from blockchain signals with evidence and confidence scores",
  require_partition_filter=false
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_insights_by_signal
ON `intel.insights` (signal_id);

CREATE INDEX IF NOT EXISTS idx_insights_by_category
ON `intel.insights` (category, created_at DESC);

-- Add comments for documentation
ALTER TABLE `intel.insights`
  ALTER COLUMN insight_id SET OPTIONS (description="Unique identifier (UUID) for the insight"),
  ALTER COLUMN signal_id SET OPTIONS (description="Reference to the source signal that generated this insight"),
  ALTER COLUMN category SET OPTIONS (description="Insight category matching signal type: mempool, exchange, miner, whale, treasury, or predictive"),
  ALTER COLUMN headline SET OPTIONS (description="Short headline (max 80 characters) summarizing the insight"),
  ALTER COLUMN summary SET OPTIONS (description="2-3 sentence explanation of why this insight matters"),
  ALTER COLUMN confidence SET OPTIONS (description="Confidence score inherited from source signal (0.0 to 1.0)"),
  ALTER COLUMN evidence SET OPTIONS (description="Blockchain evidence including block heights and transaction IDs"),
  ALTER COLUMN chart_url SET OPTIONS (description="URL to chart visualization (null until populated by chart-renderer)"),
  ALTER COLUMN created_at SET OPTIONS (description="Timestamp when insight was generated");
