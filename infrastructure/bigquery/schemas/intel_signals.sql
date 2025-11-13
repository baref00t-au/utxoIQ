-- Create intel.signals table with partitioning by created_at
-- This table stores computed signals from blockchain data analysis

CREATE TABLE IF NOT EXISTS `intel.signals` (
  signal_id STRING NOT NULL,
  signal_type STRING NOT NULL,  -- mempool|exchange|miner|whale|treasury|predictive
  block_height INT64 NOT NULL,
  confidence FLOAT64 NOT NULL,  -- 0.0 to 1.0
  metadata JSON NOT NULL,  -- Signal-specific data (varies by signal_type)
  created_at TIMESTAMP NOT NULL,
  processed BOOLEAN NOT NULL DEFAULT FALSE,  -- For insight generation tracking
  processed_at TIMESTAMP
)
PARTITION BY DATE(created_at)
CLUSTER BY signal_type, block_height
OPTIONS(
  description="Computed blockchain signals with metadata and confidence scores",
  require_partition_filter=false
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_signals_unprocessed
ON `intel.signals` (processed, confidence, signal_type)
WHERE processed = FALSE;

-- Add comments for documentation
ALTER TABLE `intel.signals`
  ALTER COLUMN signal_id SET OPTIONS (description="Unique identifier (UUID) for the signal"),
  ALTER COLUMN signal_type SET OPTIONS (description="Type of signal: mempool, exchange, miner, whale, treasury, or predictive"),
  ALTER COLUMN block_height SET OPTIONS (description="Bitcoin block height where signal was detected"),
  ALTER COLUMN confidence SET OPTIONS (description="Confidence score from 0.0 to 1.0 indicating signal reliability"),
  ALTER COLUMN metadata SET OPTIONS (description="Signal-specific metadata in JSON format (structure varies by signal_type)"),
  ALTER COLUMN created_at SET OPTIONS (description="Timestamp when signal was generated"),
  ALTER COLUMN processed SET OPTIONS (description="Whether insight has been generated from this signal"),
  ALTER COLUMN processed_at SET OPTIONS (description="Timestamp when insight was generated from this signal");
