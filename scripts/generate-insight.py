#!/usr/bin/env python3
"""
Generate AI insights from blockchain data in BigQuery
"""

import os
import sys
import requests
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'data-ingestion', 'src'))

from dotenv import load_dotenv
load_dotenv()

from bigquery_client import BigQueryClient

def generate_insight_with_gemini(api_key, prompt):
    """Call Gemini API to generate insight"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    result = response.json()
    return result['candidates'][0]['content']['parts'][0]['text']

def main():
    print("🤖 Generating Blockchain Insights\n")
    
    # Initialize clients
    bq = BigQueryClient()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    # Query recent blockchain activity
    print("📊 Analyzing recent blockchain data...")
    
    query = """
    WITH recent_blocks AS (
        SELECT 
            block_hash,
            height,
            timestamp,
            size,
            tx_count,
            fees_total
        FROM `utxoiq-dev.btc.blocks`
        WHERE height >= 922620  -- Last 10 blocks we have data for
        ORDER BY height DESC
    ),
    block_stats AS (
        SELECT
            COUNT(*) as block_count,
            AVG(size) as avg_size,
            AVG(tx_count) as avg_tx_count,
            SUM(tx_count) as total_txs,
            AVG(fees_total) as avg_fees
        FROM recent_blocks
    ),
    tx_stats AS (
        SELECT
            COUNT(*) as total_transactions,
            AVG(fee_rate) as avg_fee_rate,
            MAX(fee_rate) as max_fee_rate,
            SUM(CASE WHEN output_value > 10 THEN 1 ELSE 0 END) as large_txs
        FROM `utxoiq-dev.btc.transactions`
        WHERE block_height >= (SELECT MIN(height) FROM recent_blocks)
    ),
    utxo_stats AS (
        SELECT
            COUNT(*) as total_utxos,
            SUM(CASE WHEN value > 10 THEN 1 ELSE 0 END) as large_utxos,
            SUM(CASE WHEN value > 100 THEN 1 ELSE 0 END) as whale_utxos
        FROM `utxoiq-dev.btc.utxos`
        WHERE block_height >= (SELECT MIN(height) FROM recent_blocks)
    )
    SELECT * FROM block_stats, tx_stats, utxo_stats
    """
    
    result = bq.client.query(query).result()
    
    for row in result:
        stats = {
            'block_count': row.block_count,
            'avg_size': round(row.avg_size) if row.avg_size else 0,
            'avg_tx_count': round(row.avg_tx_count) if row.avg_tx_count else 0,
            'total_txs': row.total_transactions or 0,
            'avg_fee_rate': round(row.avg_fee_rate, 2) if row.avg_fee_rate else 0,
            'max_fee_rate': round(row.max_fee_rate, 2) if row.max_fee_rate else 0,
            'large_txs': row.large_txs or 0,
            'total_utxos': row.total_utxos or 0,
            'large_utxos': row.large_utxos or 0,
            'whale_utxos': row.whale_utxos or 0,
        }
    
    print(f"✅ Data collected\n")
    print(f"📈 Stats:")
    print(f"   Blocks analyzed: {stats['block_count']}")
    print(f"   Total transactions: {stats['total_txs']:,}")
    print(f"   Total UTXOs: {stats['total_utxos']:,}")
    print(f"   Large transactions (>10 BTC): {stats['large_txs']}")
    print(f"   Whale UTXOs (>100 BTC): {stats['whale_utxos']}")
    print(f"   Avg fee rate: {stats['avg_fee_rate']} sat/vB")
    print()
    
    # Generate insight
    prompt = f"""
Analyze this Bitcoin blockchain data and create a concise insight for traders:

Recent Activity (last {stats['block_count']} blocks):
- Total Transactions: {stats['total_txs']:,}
- Average Block Size: {stats['avg_size']:,} bytes
- Average Transactions per Block: {stats['avg_tx_count']}
- Average Fee Rate: {stats['avg_fee_rate']} sat/vB
- Max Fee Rate: {stats['max_fee_rate']} sat/vB
- Large Transactions (>10 BTC): {stats['large_txs']}
- Total UTXOs Created: {stats['total_utxos']:,}
- Large UTXOs (>10 BTC): {stats['large_utxos']}
- Whale UTXOs (>100 BTC): {stats['whale_utxos']}

Provide:
1. A catchy headline (max 80 characters)
2. A 2-3 sentence analysis explaining what's notable
3. What this means for traders

Keep it professional but accessible.
"""
    
    print("🤖 Generating AI insight...")
    insight = generate_insight_with_gemini(api_key, prompt)
    
    print("\n" + "="*60)
    print("✨ AI-GENERATED INSIGHT")
    print("="*60)
    print(insight)
    print("="*60)
    
    print("\n💡 This insight could be:")
    print("   - Stored in BigQuery intel.insights table")
    print("   - Posted to X (Twitter)")
    print("   - Displayed on the web frontend")
    print("   - Sent as email alerts")

if __name__ == '__main__':
    main()
