#!/usr/bin/env python3
"""
Quick script to generate a few AI-style insights and save to BigQuery.
This creates realistic insights without requiring full Vertex AI setup.
"""
from google.cloud import bigquery
from datetime import datetime, timedelta
import uuid
import json

PROJECT_ID = "utxoiq-dev"
DATASET_INTEL = "intel"

# Pre-written AI-quality insights
INSIGHTS = [
    {
        "signal_type": "mempool",
        "headline": "Mempool fees spike to 45 sat/vB as network demand surges",
        "summary": "Transaction fees have increased significantly over the past 6 hours, reaching 45 sat/vB average. This development suggests heightened network activity and increased demand for block space. Historical patterns indicate this could continue if demand remains elevated.",
        "confidence": 0.87,
        "tags": ["fees", "congestion"],
        "is_predictive": False
    },
    {
        "signal_type": "exchange",
        "headline": "Net exchange outflow of 6,250 BTC indicates accumulation phase",
        "summary": "Exchange flow analysis reveals significant outward movement of Bitcoin over the past 24 hours. This pattern typically precedes price appreciation and has been observed multiple times this year. Market participants should monitor for confirmation signals.",
        "confidence": 0.82,
        "tags": ["flows", "accumulation"],
        "is_predictive": True
    },
    {
        "signal_type": "miner",
        "headline": "Hash rate reaches 550 EH/s as mining network strengthens",
        "summary": "Mining network metrics show increased activity with hash rate hitting new highs. The network strength adjustment reflects growing miner confidence and investment. This development could support price stability in the coming weeks.",
        "confidence": 0.91,
        "tags": ["hashrate", "security"],
        "is_predictive": False
    },
    {
        "signal_type": "mempool",
        "headline": "Transaction backlog clears as fees drop to 12 sat/vB",
        "summary": "Low-fee transactions are now clearing efficiently as mempool congestion eases. The fee market has cooled significantly from recent highs. This creates favorable conditions for smaller transactions and network accessibility.",
        "confidence": 0.85,
        "tags": ["fees", "transactions"],
        "is_predictive": False
    },
    {
        "signal_type": "whale",
        "headline": "Dormant address from 2015 activates with 15,000 BTC",
        "summary": "Large holder activity indicates potential distribution behavior after 8 years of dormancy. The movement of 15,000 BTC from cold storage suggests strategic positioning. Historical data shows similar patterns often precede market volatility.",
        "confidence": 0.79,
        "tags": ["whale", "dormant"],
        "is_predictive": True
    }
]

def main():
    print("=" * 60)
    print("Quick Insight Generation")
    print("=" * 60)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{DATASET_INTEL}.insights"
    
    records = []
    current_block = 870000
    
    for i, insight_template in enumerate(INSIGHTS):
        insight_id = f"insight_{uuid.uuid4().hex[:12]}"
        created_at = datetime.utcnow() - timedelta(hours=i * 4)
        
        record = {
            "insight_id": insight_id,
            "signal_type": insight_template["signal_type"],
            "headline": insight_template["headline"],
            "summary": insight_template["summary"],
            "confidence": insight_template["confidence"],
            "created_at": created_at.isoformat(),
            "block_height": current_block - (i * 24),
            "evidence_blocks": [current_block - (i * 24)],
            "evidence_txids": [],
            "chart_url": None,
            "tags": insight_template["tags"],
            "confidence_factors": json.dumps({
                "signal_strength": insight_template["confidence"],
                "historical_accuracy": 0.85,
                "data_quality": 0.92
            }),
            "confidence_explanation": f"High confidence based on strong signal analysis and verified data quality.",
            "supporting_evidence": [
                "Real-time blockchain data analysis",
                "Historical pattern recognition",
                "Multi-source data verification"
            ],
            "accuracy_rating": None,
            "is_predictive": insight_template["is_predictive"],
            "model_version": "v1.5.0"
        }
        
        records.append(record)
        print(f"✅ Generated: [{record['signal_type']}] {record['headline'][:60]}...")
    
    print()
    print(f"Inserting {len(records)} insights into BigQuery...")
    
    errors = client.insert_rows_json(table_id, records)
    
    if errors:
        print(f"❌ Errors: {errors}")
    else:
        print(f"✅ Successfully inserted {len(records)} insights!")
        print()
        print("=" * 60)
        print("Test the API:")
        print("https://utxoiq-web-api-dev-544291059247.us-central1.run.app/insights/public")
        print("=" * 60)

if __name__ == "__main__":
    main()
