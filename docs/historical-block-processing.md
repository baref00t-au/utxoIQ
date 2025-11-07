# Historical Block Processing Guide

## Overview

You can process Bitcoin blocks from any starting point, including from the genesis block (block 0). This is useful for:
- Building historical datasets
- Backtesting signal detection algorithms
- Analyzing past blockchain events
- Populating your database with historical data

## Options for Processing Blocks

### Option 1: Start from a Specific Block (Real-time Mode)

Process blocks starting from a specific height and continue monitoring for new blocks:

```bash
cd services/data-ingestion

# Start from block 800,000
python src/main.py --start-height 800000

# Start from genesis block
python src/main.py --from-genesis

# Start from current tip (default)
python src/main.py
```

### Option 2: Backfill Historical Blocks (Batch Mode)

Process a specific range of historical blocks without real-time monitoring:

```bash
cd scripts

# Process last 1,000 blocks
python backfill-blocks.py --last 1000

# Process specific range
python backfill-blocks.py --start 800000 --end 801000

# Process from genesis to block 10,000
python backfill-blocks.py --start 0 --end 10000

# Process ALL blocks from genesis (⚠️ takes a long time!)
python backfill-blocks.py --from-genesis
```

## Performance Considerations

### Processing Speed

Typical processing rates on a local Umbrel node:
- **With full transaction data**: ~5-10 blocks/second
- **Block headers only**: ~50-100 blocks/second

### Time Estimates

| Block Range | Blocks | Estimated Time (10 blocks/sec) |
|-------------|--------|-------------------------------|
| Last 144 blocks (1 day) | 144 | ~15 seconds |
| Last 1,008 blocks (1 week) | 1,008 | ~2 minutes |
| Last 52,560 blocks (1 year) | 52,560 | ~1.5 hours |
| Last 210,000 blocks (halving) | 210,000 | ~6 hours |
| From genesis (all blocks) | 922,000+ | ~25+ hours |

### Optimization Tips

1. **Batch Size**: Adjust batch size for optimal performance
   ```bash
   python backfill-blocks.py --start 0 --end 10000 --batch-size 500
   ```

2. **Skip Transaction Details**: For faster processing (future enhancement)
   - Process block headers only
   - Add transaction details later if needed

3. **Parallel Processing**: Run multiple instances for different ranges
   ```bash
   # Terminal 1
   python backfill-blocks.py --start 0 --end 100000
   
   # Terminal 2
   python backfill-blocks.py --start 100001 --end 200000
   ```

## Use Cases

### 1. Recent History (Recommended for Testing)

Process the last week of blocks to test your setup:

```bash
python backfill-blocks.py --last 1008
```

**Why**: Quick to process, includes recent mempool activity, good for testing.

### 2. Specific Event Analysis

Process blocks around a specific event (e.g., fee spike, halving):

```bash
# Bitcoin halving (April 2024) - block 840,000
python backfill-blocks.py --start 839900 --end 840100
```

### 3. Full Historical Dataset

Process all blocks from genesis for complete historical analysis:

```bash
# ⚠️ This will take 24+ hours!
python backfill-blocks.py --from-genesis
```

**Recommendation**: Run overnight or over a weekend.

### 4. Incremental Backfill

Process blocks in chunks over multiple sessions:

```bash
# Day 1: Process first 100k blocks
python backfill-blocks.py --start 0 --end 100000

# Day 2: Process next 100k blocks
python backfill-blocks.py --start 100001 --end 200000

# Continue...
```

## Monitoring Progress

### Real-time Progress

The backfill script shows:
- **Progress percentage**: How much is complete
- **Blocks processed**: Current count vs total
- **Processing rate**: Blocks per second
- **ETA**: Estimated time remaining

Example output:
```
Progress: 45.2% | Blocks: 45,234/100,000 | Rate: 8.5 blocks/sec | ETA: 107.2 min
```

### Logs

Check detailed logs:
```bash
# View logs in real-time
tail -f logs/ingestion.log

# Search for errors
grep ERROR logs/ingestion.log
```

## Handling Interruptions

### Graceful Shutdown

Press `Ctrl+C` to stop processing. The script will:
- Finish processing the current block
- Print a summary of what was processed
- Exit cleanly

### Resume Processing

To resume from where you left off:

```bash
# If you stopped at block 50,000
python backfill-blocks.py --start 50001 --end 100000
```

## Data Storage

### Where Data Goes

Processed blocks are sent to:
1. **Cloud Pub/Sub** (or local emulator)
2. **BigQuery** (via Dataflow pipeline)
3. **PostgreSQL** (for transactional data)

### Verify Data

Check if blocks were processed:

```bash
# PostgreSQL
docker exec -it utxoiq-postgres psql -U utxoiq -d utxoiq_db
SELECT COUNT(*) FROM blocks;

# BigQuery (when configured)
bq query "SELECT COUNT(*) FROM btc.blocks"
```

## Common Scenarios

### Scenario 1: Quick Test Setup

```bash
# Process last 100 blocks to test everything works
python backfill-blocks.py --last 100
```

### Scenario 2: Build Last Year's Dataset

```bash
# Process ~52,560 blocks (1 year)
python backfill-blocks.py --last 52560
```

### Scenario 3: Complete Historical Archive

```bash
# Process all blocks (run overnight)
nohup python backfill-blocks.py --from-genesis > backfill.log 2>&1 &

# Check progress
tail -f backfill.log
```

### Scenario 4: Specific Analysis Period

```bash
# Analyze 2023 blocks (approximate range)
python backfill-blocks.py --start 770000 --end 822000
```

## Troubleshooting

### Slow Processing

**Issue**: Processing is slower than expected

**Solutions**:
1. Check Umbrel node performance
2. Reduce batch size: `--batch-size 50`
3. Check network latency to Umbrel
4. Ensure Docker containers aren't resource-constrained

### Connection Timeouts

**Issue**: RPC connection timeouts

**Solutions**:
1. Verify Umbrel is accessible: `ping umbrel.local`
2. Check RPC credentials in `.env`
3. Increase timeout in `bitcoin_rpc.py`

### Out of Memory

**Issue**: Script crashes with memory errors

**Solutions**:
1. Reduce batch size: `--batch-size 10`
2. Process in smaller ranges
3. Restart Docker containers: `docker-compose restart`

### Pub/Sub Errors

**Issue**: Failed to publish to Pub/Sub

**Solutions**:
1. Check if emulator is running: `docker ps | grep pubsub`
2. Restart emulator: `docker-compose restart pubsub-emulator`
3. Check GCP credentials (for production)

## Best Practices

1. **Start Small**: Test with `--last 100` before processing large ranges
2. **Monitor Resources**: Watch CPU, memory, and disk usage
3. **Use Screen/Tmux**: For long-running backfills
4. **Save Logs**: Redirect output to log files
5. **Verify Data**: Check a few blocks manually after processing
6. **Incremental Approach**: Process in chunks rather than all at once

## Example Workflow

```bash
# 1. Test with recent blocks
python backfill-blocks.py --last 100

# 2. Verify data was stored
docker exec -it utxoiq-postgres psql -U utxoiq -d utxoiq_db -c "SELECT COUNT(*) FROM blocks;"

# 3. Process last week
python backfill-blocks.py --last 1008

# 4. If all looks good, process more history
python backfill-blocks.py --last 52560

# 5. For complete history (optional)
nohup python backfill-blocks.py --from-genesis > backfill.log 2>&1 &
```

## Next Steps

After processing historical blocks:
1. Verify data quality
2. Run signal detection algorithms
3. Generate insights from historical data
4. Build dashboards and visualizations
5. Test anomaly detection on past events
