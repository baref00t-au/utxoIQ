"""
Generate actual utxoIQ insights from blockchain data.
This demonstrates the types of insights the platform would produce.
"""

from google.cloud import bigquery
from datetime import datetime
import statistics

def generate_insights():
    """Generate real utxoIQ-style insights."""
    
    client = bigquery.Client(project="utxoiq-dev")
    
    print("=" * 80)
    print("                        utxoIQ INTELLIGENCE FEED")
    print("=" * 80)
    print(f"                    {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 80)
    print()
    
    insights = []
    
    # Query recent blocks
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
    
    # Query transactions
    tx_query = """
    SELECT 
        COUNT(*) as total_tx,
        AVG(ARRAY_LENGTH(inputs)) as avg_inputs,
        AVG(ARRAY_LENGTH(outputs)) as avg_outputs,
        MAX(ARRAY_LENGTH(outputs)) as max_outputs,
        SUM(ARRAY_LENGTH(inputs)) as total_inputs,
        SUM(ARRAY_LENGTH(outputs)) as total_outputs
    FROM `utxoiq-dev.btc.transactions`
    """
    tx_stats = list(client.query(tx_query).result())[0]
    
    # INSIGHT 1: Mempool Congestion
    if blocks:
        avg_tx = statistics.mean([b.transaction_count for b in blocks])
        latest = blocks[0]
        
        if latest.transaction_count > avg_tx * 1.3:
            insights.append({
                "category": "MEMPOOL",
                "headline": "Mempool Backlog Clearing Detected",
                "summary": f"Block {latest.number} processed {latest.transaction_count} transactions, 30% above recent average. This suggests miners are clearing accumulated mempool transactions, likely due to increased fee rates.",
                "confidence": 0.85,
                "timestamp": latest.timestamp,
                "evidence": {
                    "block_height": latest.number,
                    "tx_count": latest.transaction_count,
                    "avg_tx_count": int(avg_tx)
                },
                "impact": "MEDIUM",
                "actionable": "Fee rates may decrease in next 1-2 blocks as backlog clears."
            })
    
    # INSIGHT 2: Block Fullness
    if blocks:
        avg_size = statistics.mean([b.size for b in blocks])
        fullness = (avg_size / 4_000_000) * 100
        
        if fullness < 50:
            insights.append({
                "category": "MEMPOOL",
                "headline": "Low Network Demand - Optimal Time for Transactions",
                "summary": f"Recent blocks are only {fullness:.0f}% full (avg {avg_size/1_000_000:.2f}MB of 4MB limit). Network has significant spare capacity, indicating low fee competition and optimal conditions for cost-effective transactions.",
                "confidence": 0.92,
                "timestamp": blocks[0].timestamp,
                "evidence": {
                    "avg_block_size_mb": round(avg_size / 1_000_000, 2),
                    "fullness_pct": round(fullness, 1),
                    "blocks_analyzed": len(blocks)
                },
                "impact": "HIGH",
                "actionable": "Execute pending transactions now to benefit from low fees."
            })
    
    # INSIGHT 3: UTXO Set Growth
    utxo_change = tx_stats.total_outputs - tx_stats.total_inputs
    if utxo_change > 1000:
        insights.append({
            "category": "WHALE",
            "headline": "UTXO Set Expansion Indicates Accumulation Phase",
            "summary": f"Network created {utxo_change:,} more outputs than inputs consumed across {tx_stats.total_tx:,} transactions. This pattern typically indicates accumulation behavior, with entities receiving and holding rather than spending.",
            "confidence": 0.78,
            "timestamp": blocks[0].timestamp if blocks else None,
            "evidence": {
                "net_utxo_change": utxo_change,
                "total_inputs": tx_stats.total_inputs,
                "total_outputs": tx_stats.total_outputs,
                "transactions": tx_stats.total_tx
            },
            "impact": "MEDIUM",
            "actionable": "Monitor for continued accumulation trend over next 24 hours."
        })
    
    # INSIGHT 4: Exchange Activity
    if tx_stats.max_outputs > 500:
        insights.append({
            "category": "EXCHANGE",
            "headline": "Large Exchange Batch Transaction Detected",
            "summary": f"A transaction with {tx_stats.max_outputs} outputs was observed, characteristic of exchange withdrawal batching. This indicates significant exchange outflow activity, with users moving funds to self-custody.",
            "confidence": 0.88,
            "timestamp": blocks[0].timestamp if blocks else None,
            "evidence": {
                "max_outputs": tx_stats.max_outputs,
                "typical_outputs": round(tx_stats.avg_outputs, 1)
            },
            "impact": "MEDIUM",
            "actionable": "Exchange outflows often precede price volatility. Monitor for continued pattern."
        })
    
    # INSIGHT 5: Block Time Variance
    if blocks and len(blocks) >= 6:
        block_times = [b.block_time_seconds for b in blocks if b.block_time_seconds and b.block_time_seconds > 0]
        if block_times:
            recent_6 = block_times[:6]
            if max(recent_6) > 1200:  # 20 minutes
                slow_block = [b for b in blocks if b.block_time_seconds and b.block_time_seconds == max(recent_6)][0]
                insights.append({
                    "category": "MINER",
                    "headline": "Slow Block Detected - Possible Hashrate Fluctuation",
                    "summary": f"Block {slow_block.number} took {max(recent_6)/60:.1f} minutes to mine, significantly above the 10-minute target. This could indicate temporary hashrate reduction or difficulty adjustment lag.",
                    "confidence": 0.72,
                    "timestamp": slow_block.timestamp,
                    "evidence": {
                        "block_height": slow_block.number,
                        "block_time_minutes": round(max(recent_6) / 60, 1),
                        "target_minutes": 10
                    },
                    "impact": "LOW",
                    "actionable": "Monitor next 2-3 blocks to confirm if pattern continues."
                })
    
    # INSIGHT 6: Transaction Complexity
    if tx_stats.avg_inputs > 3:
        insights.append({
            "category": "WHALE",
            "headline": "High Input Transactions Suggest UTXO Consolidation",
            "summary": f"Average transaction complexity shows {tx_stats.avg_inputs:.1f} inputs per transaction, above typical levels. This pattern indicates users are consolidating fragmented UTXOs, often done during low-fee periods by sophisticated actors.",
            "confidence": 0.81,
            "timestamp": blocks[0].timestamp if blocks else None,
            "evidence": {
                "avg_inputs": round(tx_stats.avg_inputs, 1),
                "typical_inputs": 2.0,
                "total_transactions": tx_stats.total_tx
            },
            "impact": "LOW",
            "actionable": "Good time for retail users to also consolidate UTXOs while fees are low."
        })
    
    # Display insights
    for i, insight in enumerate(insights, 1):
        print_insight(i, insight)
        print()
    
    # Summary
    print("=" * 80)
    print(f"                    {len(insights)} INSIGHTS GENERATED")
    print("=" * 80)
    print()
    print("CATEGORY BREAKDOWN:")
    categories = {}
    for insight in insights:
        cat = insight['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items()):
        icon = {"MEMPOOL": "📊", "EXCHANGE": "🏦", "MINER": "⛏️", "WHALE": "🐋"}.get(cat, "📈")
        print(f"  {icon} {cat}: {count} insight(s)")
    
    print()
    print("CONFIDENCE LEVELS:")
    high_conf = len([i for i in insights if i['confidence'] >= 0.85])
    med_conf = len([i for i in insights if 0.70 <= i['confidence'] < 0.85])
    low_conf = len([i for i in insights if i['confidence'] < 0.70])
    print(f"  🟢 High (≥85%): {high_conf}")
    print(f"  🟡 Medium (70-84%): {med_conf}")
    print(f"  🔴 Low (<70%): {low_conf}")


def print_insight(number, insight):
    """Print a formatted insight."""
    
    # Category icon
    icons = {
        "MEMPOOL": "📊",
        "EXCHANGE": "🏦",
        "MINER": "⛏️",
        "WHALE": "🐋"
    }
    icon = icons.get(insight['category'], "📈")
    
    # Confidence badge
    conf = insight['confidence']
    if conf >= 0.85:
        conf_badge = "🟢 HIGH"
    elif conf >= 0.70:
        conf_badge = "🟡 MEDIUM"
    else:
        conf_badge = "🔴 LOW"
    
    # Impact badge
    impact_icons = {
        "HIGH": "🔥",
        "MEDIUM": "⚡",
        "LOW": "💡"
    }
    impact_icon = impact_icons.get(insight['impact'], "💡")
    
    print(f"┌{'─' * 78}┐")
    print(f"│ INSIGHT #{number:<71}│")
    print(f"├{'─' * 78}┤")
    print(f"│ {icon} {insight['category']:<20} │ Confidence: {conf_badge} ({conf:.0%}){' ' * 20}│")
    print(f"├{'─' * 78}┤")
    print(f"│                                                                              │")
    print(f"│ {insight['headline']:<76}│")
    print(f"│                                                                              │")
    
    # Wrap summary text
    summary_lines = wrap_text(insight['summary'], 74)
    for line in summary_lines:
        print(f"│ {line:<76}│")
    
    print(f"│                                                                              │")
    print(f"├{'─' * 78}┤")
    print(f"│ EVIDENCE:                                                                    │")
    
    for key, value in insight['evidence'].items():
        key_display = key.replace('_', ' ').title()
        if isinstance(value, float):
            value_display = f"{value:.2f}"
        elif isinstance(value, int):
            value_display = f"{value:,}"
        else:
            value_display = str(value)
        print(f"│   • {key_display}: {value_display:<60}│")
    
    print(f"│                                                                              │")
    print(f"│ {impact_icon} IMPACT: {insight['impact']:<65}│")
    print(f"│ 💡 ACTION: {insight['actionable']:<64}│")
    print(f"└{'─' * 78}┘")


def wrap_text(text, width):
    """Wrap text to specified width."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + len(current_line) <= width:
            current_line.append(word)
            current_length += len(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


if __name__ == "__main__":
    generate_insights()
