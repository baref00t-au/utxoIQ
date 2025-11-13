-- Create or update btc.known_entities table to include treasury companies
-- This table stores identified exchanges, mining pools, and treasury companies with metadata

CREATE TABLE IF NOT EXISTS `btc.known_entities` (
  entity_id STRING NOT NULL,
  entity_name STRING NOT NULL,  -- "Coinbase", "Foundry USA", "MicroStrategy", etc.
  entity_type STRING NOT NULL,  -- exchange|mining_pool|treasury
  addresses ARRAY<STRING> NOT NULL,
  metadata JSON,  -- For treasury: {"ticker": "MSTR", "known_holdings_btc": 152800}
  updated_at TIMESTAMP NOT NULL
)
CLUSTER BY entity_type, entity_name
OPTIONS(
  description="Known blockchain entities including exchanges, mining pools, and treasury companies with addresses and metadata"
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_entities_by_type
ON `btc.known_entities` (entity_type);

-- Add comments for documentation
ALTER TABLE `btc.known_entities`
  ALTER COLUMN entity_id SET OPTIONS (description="Unique identifier for the entity"),
  ALTER COLUMN entity_name SET OPTIONS (description="Human-readable name (e.g., Coinbase, Foundry USA, MicroStrategy)"),
  ALTER COLUMN entity_type SET OPTIONS (description="Type of entity: exchange, mining_pool, or treasury"),
  ALTER COLUMN addresses SET OPTIONS (description="Array of Bitcoin addresses associated with this entity"),
  ALTER COLUMN metadata SET OPTIONS (description="Additional entity metadata (for treasury: ticker symbol and known BTC holdings)"),
  ALTER COLUMN updated_at SET OPTIONS (description="Timestamp when entity record was last updated");

-- Sample data for treasury companies (to be populated via script)
-- MicroStrategy (MSTR): ~152,800 BTC
-- Tesla (TSLA): ~9,720 BTC
-- Block (SQ): ~8,027 BTC
-- Marathon Digital (MARA): ~26,842 BTC
-- Riot Platforms (RIOT): ~9,334 BTC
-- Coinbase (COIN): ~9,000 BTC (corporate holdings)
-- Galaxy Digital (GLXY): ~15,449 BTC
-- Hut 8 Mining (HUT): ~9,102 BTC
