# BigQuery Buffer Management Strategy

## Buffer Configuration

### Primary Strategy: 1-Hour Real-Time Buffer

**Configuration:**
- **Real-time window**: Last 1 hour in custom dataset
- **Cleanup threshold**: Delete data older than 2 hours
- **Cleanup frequency**: Every 30 minutes

**Rationale:**
- Public dataset is 0 hours behind (essentially real-time)
- 1-hour buffer provides competitive advantage for sub-hour insights
- 2-hour cleanup threshold provides safety margin

## Overlap Prevention

### The Duplication Problem

If custom dataset accumulates old data, queries return duplicates:

```sql
-- Public dataset: blocks 100-200 (24h+ old)
-- Custom dataset: blocks 100-250 (if cleanup fails)
-- Unified view: blocks 100-200 appear TWICE! ❌
```

### Solution 1: Aggressive Cleanup (Recommended)

**Automatic cleanup every 30 minutes:**
```sql
DELETE FROM `utxoiq-dev.btc.blocks`
WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR);

DELETE FROM `utxoiq-dev.btc.transactions`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR);
```

**Benefits:**
- ✅ Prevents duplication
- ✅ Minimizes storage costs
- ✅ Fast queries (small custom dataset)

**Risks:**
- ⚠️ If cleanup fails, duplicates can occur
- ⚠️ Need monitoring and alerting

### Solution 2: Deduplication in Views

**Add deduplication logic to unified views:**

```sql
-- Blocks unified with deduplication
CREATE OR REPLACE VIEW `utxoiq-dev.btc.blocks_unified` AS
WITH custom_blocks AS (
  SELECT * FROM `utxoiq-dev.btc.blocks`
),
public_blocks AS (
  SELECT * FROM `bigquery-public-data.crypto_bitcoin.blocks`
  WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
    -- Exclude blocks that exist in custom dataset
    AND `hash` NOT IN (SELECT `hash` FROM custom_blocks)
)
SELECT * FROM custom_blocks
UNION ALL
SELECT * FROM public_blocks;
```

**Benefits:**
- ✅ Guarantees no duplicates
- ✅ Works even if cleanup fails
- ✅ Graceful degradation

**Risks:**
- ⚠️ More expensive queries (NOT IN subquery)
- ⚠️ Slower performance

### Solution 3: Hybrid Approach (Best)

**Combine both strategies:**

1. **Aggressive cleanup** (primary defense)
2. **Deduplication in views** (safety net)
3. **Monitoring and alerts** (early warning)

## Implementation

### Updated Unified Views with Deduplication

```sql
-- Blocks unified (deduplication-safe)
CREATE OR REPLACE VIEW `utxoiq-dev.btc.blocks_unified` AS
SELECT * FROM `utxoiq-dev.btc.blocks`
UNION ALL
SELECT * FROM `bigquery-public-data.crypto_bitcoin.blocks`
WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  AND `hash` NOT IN (
    SELECT `hash` FROM `utxoiq-dev.btc.blocks`
  );

-- Transactions unified (deduplication-safe)
CREATE OR REPLACE VIEW `utxoiq-dev.btc.transactions_unified` AS
SELECT * FROM `utxoiq-dev.btc.transactions`
UNION ALL
SELECT * FROM `bigquery-public-data.crypto_bitcoin.transactions`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  AND `hash` NOT IN (
    SELECT `hash` FROM `utxoiq-dev.btc.transactions`
  );
```

### Cleanup Configuration

**Cloud Scheduler Job:**
```bash
# Run every 30 minutes
gcloud scheduler jobs create http bigquery-cleanup \
  --schedule="*/30 * * * *" \
  --uri="https://feature-engine-xxx.run.app/cleanup?hours=2" \
  --http-method=POST \
  --oidc-service-account-email=feature-engine@utxoiq-dev.iam.gserviceaccount.com
```

**Cleanup Endpoint:**
```python
@app.post("/cleanup")
async def cleanup_old_data(hours: int = 2):
    """Clean up data older than specified hours."""
    try:
        results = bq_adapter.cleanup_old_data(hours)
        
        # Alert if too much data was deleted (indicates ingestion failure)
        if results['blocks'] > 200:  # More than ~3 hours of blocks
            logger.warning(
                f"Cleanup deleted {results['blocks']} blocks - "
                f"ingestion may have been down"
            )
        
        return {
            "status": "success",
            "deleted": results,
            "cutoff_hours": hours
        }
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Monitoring and Alerts

**Metrics to track:**

1. **Custom dataset size**
   ```sql
   SELECT 
     COUNT(*) as block_count,
     TIMESTAMP_DIFF(MAX(timestamp), MIN(timestamp), HOUR) as hours_span
   FROM `utxoiq-dev.btc.blocks`
   ```
   - Alert if `hours_span > 3` (indicates cleanup failure)

2. **Oldest block age**
   ```sql
   SELECT 
     MIN(timestamp) as oldest_block,
     TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MIN(timestamp), HOUR) as hours_old
   FROM `utxoiq-dev.btc.blocks`
   ```
   - Alert if `hours_old > 2` (indicates cleanup failure)

3. **Duplicate detection**
   ```sql
   SELECT 
     `hash`,
     COUNT(*) as count
   FROM `utxoiq-dev.btc.blocks_unified`
   WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
   GROUP BY `hash`
   HAVING COUNT(*) > 1
   ```
   - Alert if any duplicates found

## Failure Scenarios

### Scenario 1: Cleanup Job Fails

**What happens:**
- Custom dataset accumulates 3-6 hours of data
- Some overlap with public dataset

**Impact:**
- ❌ Duplicates in queries (if using simple UNION ALL)
- ✅ No duplicates (if using deduplication views)
- 💰 Slightly higher query costs

**Recovery:**
- Manual cleanup: `curl -X POST https://feature-engine-xxx.run.app/cleanup?hours=2`
- Automatic recovery on next successful cleanup run

### Scenario 2: Ingestion Stops for 24+ Hours

**What happens:**
- Custom dataset has stale data (24+ hours old)
- Public dataset has caught up and has same data

**Impact:**
- ❌ Major duplicates (if using simple UNION ALL)
- ✅ No duplicates (if using deduplication views)
- 💰 Higher query costs (scanning both datasets)

**Recovery:**
- Aggressive cleanup: `curl -X POST https://feature-engine-xxx.run.app/cleanup?hours=1`
- Or manual: `DELETE FROM utxoiq-dev.btc.blocks WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)`

### Scenario 3: Public Dataset Lag Increases

**What happens:**
- Public dataset falls behind (e.g., 6 hours lag)
- Custom dataset has 1-6 hours of data

**Impact:**
- ✅ No duplicates (custom has newer data)
- ✅ Seamless coverage (custom fills the gap)
- 💰 Slightly higher storage costs

**Recovery:**
- No action needed - this is the intended behavior
- When public dataset catches up, cleanup will remove overlap

## Cost Analysis

### 1-Hour Buffer with 2-Hour Cleanup

**Storage:**
- Average: ~0.1 GB (1-2 hours of blocks)
- Cost: $0.002/month

**Queries:**
- 95% from public dataset (free)
- 5% from custom dataset (real-time)
- Estimated: $25-30/month

**Total: ~$30/month (53% savings vs custom-only)**

### Worst Case: 24-Hour Buffer (Cleanup Failure)

**Storage:**
- Worst case: ~2 GB (24 hours of blocks)
- Cost: $0.04/month

**Queries:**
- 90% from public dataset (free)
- 10% from custom dataset
- Estimated: $30-35/month

**Total: ~$35/month (still 46% savings)**

## Recommendations

### Production Configuration

1. **Use 1-hour buffer** with deduplication views
2. **Cleanup every 30 minutes** (delete data > 2 hours old)
3. **Monitor custom dataset size** (alert if > 3 hours of data)
4. **Set up alerting** for cleanup failures
5. **Weekly review** of query costs and dataset sizes

### View Strategy

**Use deduplication views for production:**
- Guarantees correctness even if cleanup fails
- Slightly higher query cost is worth the safety
- Simplifies operations (less manual intervention)

### Cleanup Strategy

**Aggressive cleanup schedule:**
- Every 30 minutes (not every 6 hours)
- 2-hour threshold (not 48 hours)
- Monitoring and alerting for failures

## Testing Cleanup Behavior

```bash
# Test cleanup endpoint
curl -X POST "https://feature-engine-xxx.run.app/cleanup?hours=2"

# Check custom dataset size
bq query --use_legacy_sql=false "
SELECT 
  COUNT(*) as blocks,
  MIN(timestamp) as oldest,
  MAX(timestamp) as newest,
  TIMESTAMP_DIFF(MAX(timestamp), MIN(timestamp), HOUR) as span_hours
FROM \`utxoiq-dev.btc.blocks\`
"

# Check for duplicates
bq query --use_legacy_sql=false "
SELECT 
  \`hash\`,
  COUNT(*) as count
FROM \`utxoiq-dev.btc.blocks_unified\`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
GROUP BY \`hash\`
HAVING COUNT(*) > 1
LIMIT 10
"
```

## Summary

**Best Practice:**
- ✅ 1-hour real-time buffer
- ✅ Deduplication in views (safety net)
- ✅ Aggressive cleanup every 30 minutes
- ✅ Monitoring and alerting
- ✅ Graceful degradation if cleanup fails

**This approach provides:**
- Maximum cost savings (53% reduction)
- Real-time competitive advantage (sub-hour insights)
- Robustness (no duplicates even if cleanup fails)
- Operational simplicity (automatic recovery)
