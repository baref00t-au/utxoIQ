#!/usr/bin/env python3
"""
Seed BigQuery intel dataset with sample insights data.
Creates realistic Bitcoin blockchain insights for testing.
"""
from google.cloud import bigquery
from datetime import datetime, timedelta
import random
import uuid

# Configuration
PROJECT_ID = "utxoiq-dev"
DATASET_INTEL = "intel"

# Sample data
SIGNAL_TYPES = ["mempool", "exchange", "miner", "whale"]

HEADLINES = {
    "mempool": [
        "Mempool fees spike to {fee} sat/vB as demand surges",
        "Transaction backlog clears as fees drop to {fee} sat/vB",
        "Mempool congestion reaches {count} pending transactions",
        "Low-fee transactions clearing as mempool empties",
        "Fee market heats up with {fee} sat/vB average"
    ],
    "exchange": [
        "Major exchange sees {amount} BTC outflow in 24 hours",
        "Exchange reserves drop to {amount} BTC, lowest since 2020",
        "Whale deposits {amount} BTC to exchange",
        "Exchange inflows surge by {percent}% signaling potential selling",
        "Net exchange outflow of {amount} BTC indicates accumulation"
    ],
    "miner": [
        "Mining difficulty adjusts {direction} by {percent}%",
        "Hash rate reaches new all-time high of {hashrate} EH/s",
        "Miners hold {amount} BTC, highest in 6 months",
        "Mining pool consolidation: Top 3 pools control {percent}%",
        "Miner revenue hits ${revenue}M as fees spike"
    ],
    "whale": [
        "Whale moves {amount} BTC after {years} years dormant",
        "Large holder accumulates {amount} BTC in past week",
        "Whale wallet splits {amount} BTC across multiple addresses",
        "Dormant address from 2013 activates with {amount} BTC",
        "Top 100 addresses now hold {percent}% of supply"
    ]
}

SUMMARIES = {
    "mempool": "Transaction fees have {trend} significantly over the past {hours} hours. This {impact} suggests {reason}. Historical patterns indicate this could {prediction}.",
    "exchange": "Exchange flow analysis reveals {trend} movement of Bitcoin. This pattern typically {indication} and has been observed {frequency}. Market participants should {advice}.",
    "miner": "Mining network metrics show {trend} activity. The {metric} adjustment reflects {reason}. This development could {impact} in the coming weeks.",
    "whale": "Large holder activity indicates {trend} behavior. The movement of {amount} BTC from {source} suggests {reason}. Historical data shows similar patterns {outcome}."
}

def create_insights_table(client: bigquery.Client):
    """Create insights table in BigQuery."""
    table_id = f"{PROJECT_ID}.{DATASET_INTEL}.insights"
    
    schema = [
        bigquery.SchemaField("insight_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("signal_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("headline", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("summary", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("confidence", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("block_height", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("evidence_blocks", "INTEGER", mode="REPEATED"),
        bigquery.SchemaField("evidence_txids", "STRING", mode="REPEATED"),
        bigquery.SchemaField("chart_url", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
        bigquery.SchemaField("confidence_factors", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("confidence_explanation", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("supporting_evidence", "STRING", mode="REPEATED"),
        bigquery.SchemaField("accuracy_rating", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("is_predictive", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("model_version", "STRING", mode="NULLABLE"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    
    try:
        table = client.create_table(table, exists_ok=True)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        print(f"⚠️  Table might already exist: {e}")

def generate_insight(signal_type: str, days_ago: int, block_height: int) -> dict:
    """Generate a realistic insight."""
    insight_id = f"insight_{uuid.uuid4().hex[:12]}"
    
    # Generate headline with realistic values
    headline_template = random.choice(HEADLINES[signal_type])
    headline_values = {
        "fee": random.randint(20, 150),
        "count": random.randint(50000, 200000),
        "amount": random.randint(1000, 50000),
        "percent": random.randint(5, 45),
        "hashrate": random.randint(400, 600),
        "revenue": random.randint(20, 100),
        "years": random.randint(2, 10),
        "direction": random.choice(["upward", "downward"])
    }
    headline = headline_template.format(**headline_values)
    
    # Generate summary
    summary_template = SUMMARIES[signal_type]
    summary_values = {
        "trend": random.choice(["increased", "decreased", "stabilized"]),
        "hours": random.randint(6, 48),
        "impact": random.choice(["development", "shift", "change"]),
        "reason": random.choice(["increased demand", "network congestion", "market dynamics"]),
        "prediction": random.choice(["continue", "reverse", "stabilize"]),
        "indication": random.choice(["precedes price movement", "signals accumulation", "suggests distribution"]),
        "frequency": random.choice(["multiple times this year", "in previous cycles", "during bull markets"]),
        "advice": random.choice(["monitor closely", "consider implications", "watch for confirmation"]),
        "metric": random.choice(["difficulty", "hash rate", "revenue"]),
        "amount": f"{random.randint(1000, 50000)} BTC",
        "source": random.choice(["cold storage", "exchange", "mining pool"]),
        "outcome": random.choice(["led to rallies", "preceded corrections", "indicated accumulation"])
    }
    summary = summary_template.format(**summary_values)
    
    # Generate confidence and evidence
    confidence = round(random.uniform(0.65, 0.95), 2)
    
    evidence_blocks = [block_height - i for i in range(random.randint(1, 5))]
    evidence_txids = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]
    
    # Tags
    tag_options = {
        "mempool": ["fees", "congestion", "transactions"],
        "exchange": ["flows", "reserves", "liquidity"],
        "miner": ["hashrate", "difficulty", "revenue"],
        "whale": ["accumulation", "distribution", "dormant"]
    }
    tags = random.sample(tag_options[signal_type], k=random.randint(1, 2))
    
    # Confidence factors
    confidence_factors = {
        "signal_strength": round(random.uniform(0.7, 0.95), 2),
        "historical_accuracy": round(random.uniform(0.65, 0.90), 2),
        "data_quality": round(random.uniform(0.85, 0.98), 2)
    }
    
    confidence_explanation = f"High confidence based on strong signal strength ({confidence_factors['signal_strength']}) and verified data quality."
    
    supporting_evidence = [
        "Historical pattern match confirmed",
        "Multiple data sources corroborate",
        "Statistical significance verified"
    ]
    
    # Accuracy rating (for past insights)
    accuracy_rating = round(random.uniform(0.70, 0.92), 2) if days_ago > 7 else None
    
    created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
    
    return {
        "insight_id": insight_id,
        "signal_type": signal_type,
        "headline": headline,
        "summary": summary,
        "confidence": confidence,
        "created_at": created_at.isoformat(),
        "block_height": block_height,
        "evidence_blocks": evidence_blocks,
        "evidence_txids": evidence_txids,
        "chart_url": f"https://storage.googleapis.com/utxoiq-charts/{insight_id}.png",
        "tags": tags,
        "confidence_factors": confidence_factors,
        "confidence_explanation": confidence_explanation,
        "supporting_evidence": supporting_evidence,
        "accuracy_rating": accuracy_rating,
        "is_predictive": random.choice([True, False]),
        "model_version": random.choice(["v1.2.0", "v1.3.0", "v1.4.0"])
    }

def seed_insights(client: bigquery.Client, count: int = 50):
    """Seed insights data."""
    table_id = f"{PROJECT_ID}.{DATASET_INTEL}.insights"
    
    print(f"Generating {count} sample insights...")
    
    insights = []
    current_block = 870000  # Approximate current block height
    
    for i in range(count):
        days_ago = i // 2  # 2 insights per day going back
        signal_type = random.choice(SIGNAL_TYPES)
        block_height = current_block - (days_ago * 144)  # ~144 blocks per day
        
        insight = generate_insight(signal_type, days_ago, block_height)
        insights.append(insight)
    
    print(f"Inserting {len(insights)} insights into BigQuery...")
    
    errors = client.insert_rows_json(table_id, insights)
    
    if errors:
        print(f"❌ Errors occurred while inserting rows:")
        for error in errors:
            print(f"   {error}")
    else:
        print(f"✅ Successfully inserted {len(insights)} insights!")
        
        # Show sample
        print("\n📊 Sample insights:")
        for insight in insights[:3]:
            print(f"   - [{insight['signal_type']}] {insight['headline']}")

def main():
    """Main function."""
    print("=" * 60)
    print("Seeding BigQuery Intel Dataset")
    print("=" * 60)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Create table
    print("Creating insights table...")
    create_insights_table(client)
    print()
    
    # Seed data
    seed_insights(client, count=50)
    
    print()
    print("=" * 60)
    print("✅ Seeding complete!")
    print("=" * 60)
    print()
    print("You can now:")
    print("1. View insights in BigQuery console")
    print("2. Test the API: https://utxoiq-web-api-dev-544291059247.us-central1.run.app/insights/public")
    print("3. Check the frontend Live Feed")

if __name__ == "__main__":
    main()
