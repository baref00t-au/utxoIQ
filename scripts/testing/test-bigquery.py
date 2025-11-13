#!/usr/bin/env python3
"""
Test BigQuery connection and write a sample block
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'data-ingestion', 'src'))

from dotenv import load_dotenv
load_dotenv()

from bitcoin_rpc import BitcoinRPCClient
from bigquery_client import BigQueryClient

def main():
    print("🧪 Testing BigQuery Connection\n")
    
    # Check environment
    project_id = os.getenv('GCP_PROJECT_ID')
    creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    print(f"Project ID: {project_id}")
    print(f"Credentials: {creds_file}")
    print()
    
    if not project_id:
        print("❌ GCP_PROJECT_ID not set in .env")
        return
    
    if not creds_file or not os.path.exists(creds_file):
        print(f"❌ Credentials file not found: {creds_file}")
        return
    
    # Initialize BigQuery client
    try:
        print("📡 Connecting to BigQuery...")
        bq_client = BigQueryClient()
        print(f"✅ Connected to project: {bq_client.project_id}\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Check if tables exist
    print("🔍 Checking if tables exist...")
    if not bq_client.check_tables_exist():
        print("❌ Tables not found. They should have been created during GCP setup.")
        return
    print("✅ Tables exist\n")
    
    # Get a recent block
    print("📦 Fetching a recent block from Bitcoin...")
    try:
        rpc = BitcoinRPCClient()
        current_height = rpc.get_block_count()
        block_hash = rpc.get_block_hash(current_height)
        block_data = rpc.get_block(block_hash, verbosity=2)
        print(f"✅ Fetched block {current_height}\n")
    except Exception as e:
        print(f"❌ Failed to fetch block: {e}")
        return
    
    # Prepare block for BigQuery (match the schema)
    print("💾 Writing block to BigQuery...")
    
    # Calculate total fees (simplified - just use 0 for now)
    fees_total = 0
    
    block_row = {
        "block_hash": block_data.get("hash"),
        "height": block_data.get("height"),
        "timestamp": datetime.fromtimestamp(block_data.get("time")).isoformat(),
        "size": block_data.get("size"),
        "tx_count": len(block_data.get("tx", [])),
        "fees_total": fees_total,
    }
    
    try:
        count = bq_client.stream_blocks([block_row])
        print(f"✅ Successfully wrote {count} block to BigQuery!\n")
        
        print("🎉 SUCCESS! BigQuery is working!")
        print("\nYou can now:")
        print("1. Run the backfill script to load historical blocks")
        print("2. Query your data in BigQuery console")
        print(f"3. View at: https://console.cloud.google.com/bigquery?project={project_id}")
        
    except Exception as e:
        print(f"❌ Failed to write to BigQuery: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
