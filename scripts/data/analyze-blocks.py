"""
Analyze blockchain data and generate insights.
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import statistics

def analyze_blocks():
    """Analyze recent blocks and generate insights."""
    
    client = bigquery.Client(project="utxoiq-dev")
    
    print("=" * 70)
    print("utxoIQ Blockchain Intelligence Report")
    print("=" * 70)
    print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    # 1. Block Production Analysis
    print("📊 BLOCK PRODUCTION ANALYSIS")
    print("-" * 70)
    
    query = """
    SELECT 
        number,
        timestamp,
        transaction_count,
        size,
        TIMESTAMP_DIFF(
            timestamp,
            LAG(timestamp) OVER (ORDER BY number),
            SECOND
        ) as block_time_seconds
    FROM `utxoiq-dev.btc.blocks_unified`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
    ORDER BY number DESC
    LIMIT 20
    """
    
    blocks = list(client.query(query).result())
    
    if blocks:
        block_times = [b.block_time_seconds for b in blocks if b.block_time_seconds]
        tx_counts = [b.transaction_count for b in blocks]
        sizes = [b.size for b in blocks]
        
        print(f"Recent Blocks: {len(blocks)}")
        print(f"Height Range: {blocks[-1].number} → {blocks[0].number}")
        print()
        
        if block_times:
            avg_time = statistics.mean(block_times)
            min_time = min(block_times)
            max_time = max(block_times)
            
            print(f"Block Time:")
            print(f"  Average: {avg_time:.1f} seconds")
            print(f"  Fastest: {min_time:.0f} seconds (Block {[b.number for b in blocks if b.block_time_seconds == min_time][0]})")
            print(f"  Slowest: {max_time:.0f} seconds (Block {[b.number for b in blocks if b.block_time_seconds == max_time][0]})")
            
            if avg_time < 540:  # Less than 9 minutes
                print(f"  ⚡ Status: FAST - Blocks arriving {600 - avg_time:.0f}s faster than 10min target")
            elif avg_time > 660:  # More than 11 minutes
                print(f"  🐌 Status: SLOW - Blocks arriving {avg_time - 600:.0f}s slower than 10min target")
            else:
                print(f"  ✅ Status: NORMAL - On target (~10 minutes)")
        
        print()
        print(f"Transaction Volume:")
        print(f"  Average: {statistics.mean(tx_counts):.0f} tx/block")
        print(f"  Highest: {max(tx_counts)} tx (Block {[b.number for b in blocks if b.transaction_count == max(tx_counts)][0]})")
        print(f"  Lowest: {min(tx_counts)} tx (Block {[b.number for b in blocks if b.transaction_count == min(tx_counts)][0]})")
        print(f"  Total: {sum(tx_counts):,} transactions")
        
        print()
        print(f"Block Size:")
        print(f"  Average: {statistics.mean(sizes) / 1_000_000:.2f} MB")
        print(f"  Largest: {max(sizes) / 1_000_000:.2f} MB (Block {[b.number for b in blocks if b.size == max(sizes)][0]})")
        print(f"  Smallest: {min(sizes) / 1_000_000:.2f} MB (Block {[b.number for b in blocks if b.size == min(sizes)][0]})")
        
        # Block fullness
        avg_fullness = (statistics.mean(sizes) / 4_000_000) * 100
        print(f"  Fullness: {avg_fullness:.1f}% of 4MB limit")
        
        if avg_fullness > 90:
            print(f"  🔥 INSIGHT: Blocks are nearly FULL - High network demand")
        elif avg_fullness < 50:
            print(f"  💤 INSIGHT: Blocks are half-empty - Low network demand")
    
    print()
    print()
    
    # 2. Transaction Analysis
    print("💸 TRANSACTION ANALYSIS")
    print("-" * 70)
    
    query = """
    SELECT 
        COUNT(*) as total_transactions,
        COUNT(DISTINCT block_hash) as blocks_with_tx,
        AVG(ARRAY_LENGTH(inputs)) as avg_inputs,
        AVG(ARRAY_LENGTH(outputs)) as avg_outputs,
        MAX(ARRAY_LENGTH(outputs)) as max_outputs,
        SUM(ARRAY_LENGTH(inputs)) as total_inputs,
        SUM(ARRAY_LENGTH(outputs)) as total_outputs
    FROM `utxoiq-dev.btc.transactions`
    """
    
    result = list(client.query(query).result())[0]
    
    print(f"Total Transactions: {result.total_transactions:,}")
    print(f"Blocks Analyzed: {result.blocks_with_tx}")
    print()
    print(f"Transaction Complexity:")
    print(f"  Avg Inputs: {result.avg_inputs:.1f}")
    print(f"  Avg Outputs: {result.avg_outputs:.1f}")
    print(f"  Max Outputs: {result.max_outputs} (likely exchange consolidation)")
    print()
    print(f"UTXO Activity:")
    print(f"  Total Inputs Spent: {result.total_inputs:,}")
    print(f"  Total Outputs Created: {result.total_outputs:,}")
    print(f"  Net UTXO Change: {result.total_outputs - result.total_inputs:+,}")
    
    if result.total_outputs > result.total_inputs:
        print(f"  📈 INSIGHT: UTXO set is GROWING - More outputs than inputs")
    else:
        print(f"  📉 INSIGHT: UTXO set is SHRINKING - Consolidation activity")
    
    print()
    print()
    
    # 3. Network Activity Patterns
    print("🔍 NETWORK ACTIVITY PATTERNS")
    print("-" * 70)
    
    query = """
    SELECT 
        number,
        transaction_count,
        size,
        timestamp
    FROM `utxoiq-dev.btc.blocks_unified`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
    ORDER BY number
    """
    
    blocks = list(client.query(query).result())
    
    if len(blocks) >= 3:
        # Detect trends
        recent_3 = blocks[-3:]
        tx_trend = [b.transaction_count for b in recent_3]
        size_trend = [b.size for b in recent_3]
        
        print(f"Last 3 Blocks Trend:")
        print(f"  Block {recent_3[0].number}: {recent_3[0].transaction_count} tx, {recent_3[0].size / 1_000_000:.2f} MB")
        print(f"  Block {recent_3[1].number}: {recent_3[1].transaction_count} tx, {recent_3[1].size / 1_000_000:.2f} MB")
        print(f"  Block {recent_3[2].number}: {recent_3[2].transaction_count} tx, {recent_3[2].size / 1_000_000:.2f} MB")
        print()
        
        if tx_trend[2] > tx_trend[1] > tx_trend[0]:
            print("  📈 SIGNAL: Transaction volume INCREASING")
            print("     → Network activity is ramping up")
        elif tx_trend[2] < tx_trend[1] < tx_trend[0]:
            print("  📉 SIGNAL: Transaction volume DECREASING")
            print("     → Network activity is cooling down")
        else:
            print("  ➡️  SIGNAL: Transaction volume STABLE")
        
        # Detect anomalies
        avg_tx = statistics.mean([b.transaction_count for b in blocks])
        std_tx = statistics.stdev([b.transaction_count for b in blocks]) if len(blocks) > 1 else 0
        
        latest = blocks[-1]
        if latest.transaction_count > avg_tx + (2 * std_tx):
            print()
            print(f"  ⚠️  ANOMALY DETECTED: Block {latest.number}")
            print(f"     Transaction count ({latest.transaction_count}) is {((latest.transaction_count - avg_tx) / avg_tx * 100):.0f}% above average")
            print(f"     → Possible mempool backlog clearing or exchange batch")
        elif latest.transaction_count < avg_tx - (2 * std_tx):
            print()
            print(f"  ⚠️  ANOMALY DETECTED: Block {latest.number}")
            print(f"     Transaction count ({latest.transaction_count}) is {((avg_tx - latest.transaction_count) / avg_tx * 100):.0f}% below average")
            print(f"     → Possible low-fee period or miner selection")
    
    print()
    print()
    
    # 4. Data Quality Check
    print("✅ DATA QUALITY")
    print("-" * 70)
    
    query = """
    SELECT 
        COUNT(*) as total_blocks,
        COUNT(DISTINCT number) as unique_blocks,
        MIN(number) as min_height,
        MAX(number) as max_height,
        MAX(number) - MIN(number) + 1 as expected_blocks
    FROM `utxoiq-dev.btc.blocks_unified`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
    """
    
    result = list(client.query(query).result())[0]
    
    print(f"Total Blocks: {result.total_blocks}")
    print(f"Unique Blocks: {result.unique_blocks}")
    print(f"Height Range: {result.min_height} → {result.max_height}")
    print(f"Expected Blocks: {result.expected_blocks}")
    
    if result.total_blocks == result.unique_blocks == result.expected_blocks:
        print("✅ No duplicates, no gaps - Data is clean!")
    elif result.total_blocks > result.unique_blocks:
        print(f"⚠️  Found {result.total_blocks - result.unique_blocks} duplicate blocks")
    elif result.unique_blocks < result.expected_blocks:
        print(f"⚠️  Missing {result.expected_blocks - result.unique_blocks} blocks")
    
    print()
    print("=" * 70)
    print("End of Report")
    print("=" * 70)


if __name__ == "__main__":
    analyze_blocks()
