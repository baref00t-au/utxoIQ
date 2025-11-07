-- Optimized BigQuery Queries for utxoIQ Platform
-- These queries leverage partitioning and clustering for efficient data access

-- ============================================================================
-- QUERY PATTERNS: intel.signals
-- ============================================================================

-- Query 1: Get recent signals by type (uses clustering on 'type')
-- This query efficiently filters by signal type and uses partition pruning
SELECT 
  signal_id,
  type,
  strength,
  block_height,
  data_json,
  processed_at
FROM `{project_id}.intel.signals`
WHERE 
  processed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND type = 'mempool'  -- Clustering on 'type' makes this efficient
ORDER BY processed_at DESC
LIMIT 100;

-- Query 2: Get signals for specific block range (uses clustering on 'block_height')
SELECT 
  signal_id,
  type,
  strength,
  block_height,
  data_json,
  processed_at
FROM `{project_id}.intel.signals`
WHERE 
  processed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND block_height BETWEEN 800000 AND 800100  -- Clustering makes range queries efficient
ORDER BY block_height DESC;

-- Query 3: Aggregate signal strength by type (partition + cluster optimization)
SELECT 
  type,
  DATE(processed_at) as signal_date,
  COUNT(*) as signal_count,
  AVG(strength) as avg_strength,
  MAX(strength) as max_strength
FROM `{project_id}.intel.signals`
WHERE 
  processed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY type, signal_date
ORDER BY signal_date DESC, type;

-- ============================================================================
-- QUERY PATTERNS: intel.insights
-- ============================================================================

-- Query 4: Get high-confidence insights by signal type (uses clustering)
SELECT 
  insight_id,
  signal_type,
  confidence,
  headline,
  summary,
  created_at,
  block_height,
  chart_url
FROM `{project_id}.intel.insights`
WHERE 
  created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND signal_type = 'exchange'  -- Clustering on signal_type
  AND confidence >= 0.7  -- Clustering on confidence
ORDER BY created_at DESC
LIMIT 50;

-- Query 5: Get insights with user feedback aggregation
SELECT 
  i.insight_id,
  i.signal_type,
  i.confidence,
  i.headline,
  i.created_at,
  i.accuracy_rating,
  i.feedback_count,
  COUNT(f.feedback_id) as total_feedback,
  COUNTIF(f.rating = 'useful') as useful_count,
  COUNTIF(f.rating = 'not_useful') as not_useful_count
FROM `{project_id}.intel.insights` i
LEFT JOIN `{project_id}.intel.user_feedback` f
  ON i.insight_id = f.insight_id
  AND f.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
WHERE 
  i.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY 
  i.insight_id,
  i.signal_type,
  i.confidence,
  i.headline,
  i.created_at,
  i.accuracy_rating,
  i.feedback_count
ORDER BY i.created_at DESC;

-- Query 6: Daily brief - top insights by confidence and feedback
SELECT 
  insight_id,
  signal_type,
  confidence,
  headline,
  summary,
  created_at,
  block_height,
  chart_url,
  accuracy_rating,
  feedback_count
FROM `{project_id}.intel.insights`
WHERE 
  DATE(created_at) = CURRENT_DATE()
  AND confidence >= 0.7
ORDER BY 
  confidence DESC,
  COALESCE(accuracy_rating, 0) DESC,
  created_at DESC
LIMIT 5;

-- ============================================================================
-- MATERIALIZED VIEWS FOR COMMON AGGREGATIONS
-- ============================================================================

-- Materialized View 1: Daily signal statistics
-- This pre-aggregates data to avoid repeated calculations
CREATE MATERIALIZED VIEW IF NOT EXISTS `{project_id}.intel.daily_signal_stats`
PARTITION BY signal_date
CLUSTER BY signal_type
AS
SELECT 
  DATE(processed_at) as signal_date,
  type as signal_type,
  COUNT(*) as total_signals,
  AVG(strength) as avg_strength,
  MAX(strength) as max_strength,
  MIN(strength) as min_strength,
  STDDEV(strength) as stddev_strength,
  COUNT(DISTINCT block_height) as unique_blocks
FROM `{project_id}.intel.signals`
WHERE processed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY signal_date, signal_type;

-- Materialized View 2: Insight accuracy leaderboard
CREATE MATERIALIZED VIEW IF NOT EXISTS `{project_id}.intel.insight_accuracy_leaderboard`
PARTITION BY insight_date
CLUSTER BY signal_type
AS
SELECT 
  DATE(i.created_at) as insight_date,
  i.signal_type,
  i.insight_id,
  i.confidence,
  i.accuracy_rating,
  i.feedback_count,
  SAFE_DIVIDE(
    COUNTIF(f.rating = 'useful'),
    COUNT(f.feedback_id)
  ) as useful_ratio
FROM `{project_id}.intel.insights` i
LEFT JOIN `{project_id}.intel.user_feedback` f
  ON i.insight_id = f.insight_id
WHERE i.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY 
  insight_date,
  i.signal_type,
  i.insight_id,
  i.confidence,
  i.accuracy_rating,
  i.feedback_count;

-- ============================================================================
-- QUERY OPTIMIZATION BEST PRACTICES
-- ============================================================================

-- Best Practice 1: Always filter on partitioned columns first
-- ✅ GOOD: Uses partition pruning
SELECT * FROM `{project_id}.intel.signals`
WHERE processed_at >= '2025-01-01'
  AND type = 'mempool';

-- ❌ BAD: Full table scan without partition filter
-- SELECT * FROM `{project_id}.intel.signals`
-- WHERE type = 'mempool';

-- Best Practice 2: Use clustered columns in WHERE and JOIN clauses
-- ✅ GOOD: Leverages clustering
SELECT * FROM `{project_id}.intel.insights`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND signal_type = 'exchange'
  AND confidence >= 0.7;

-- Best Practice 3: Avoid SELECT * - specify only needed columns
-- ✅ GOOD: Reduces data scanned
SELECT insight_id, headline, confidence, created_at
FROM `{project_id}.intel.insights`
WHERE created_at >= CURRENT_DATE();

-- Best Practice 4: Use approximate aggregation for large datasets
-- ✅ GOOD: Faster for large datasets
SELECT 
  signal_type,
  APPROX_COUNT_DISTINCT(insight_id) as unique_insights
FROM `{project_id}.intel.insights`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
GROUP BY signal_type;

-- ============================================================================
-- COST MONITORING QUERIES
-- ============================================================================

-- Query to analyze query costs by user/service
SELECT
  user_email,
  project_id,
  DATE(creation_time) as query_date,
  COUNT(*) as query_count,
  SUM(total_bytes_processed) / POW(10, 12) as total_tb_processed,
  SUM(total_bytes_processed) / POW(10, 12) * 5 as estimated_cost_usd
FROM `{project_id}.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE 
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
GROUP BY user_email, project_id, query_date
ORDER BY total_tb_processed DESC;

-- Query to identify expensive queries
SELECT
  user_email,
  query,
  creation_time,
  total_bytes_processed / POW(10, 9) as gb_processed,
  total_bytes_processed / POW(10, 12) * 5 as estimated_cost_usd,
  total_slot_ms / 1000 as total_seconds
FROM `{project_id}.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE 
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
  AND total_bytes_processed > POW(10, 11)  -- > 100 GB
ORDER BY total_bytes_processed DESC
LIMIT 20;
