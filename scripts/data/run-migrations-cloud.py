#!/usr/bin/env python3
"""
Run Alembic migrations against Cloud SQL database using Cloud SQL Python Connector.
This script can be run locally or from Cloud Shell.
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the web-api src directory to Python path
web_api_path = Path(__file__).parent.parent / "services" / "web-api"
sys.path.insert(0, str(web_api_path))

# Set environment variables
os.environ["CLOUD_SQL_CONNECTION_NAME"] = "utxoiq-dev:us-central1:utxoiq-db-dev"
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASSWORD"] = "utxoiq_SecurePass123!"
os.environ["DB_NAME"] = "utxoiq"
os.environ["DB_HOST"] = "127.0.0.1"
os.environ["DB_PORT"] = "5432"
os.environ["ENVIRONMENT"] = "development"
os.environ["GCP_PROJECT_ID"] = "utxoiq-dev"
os.environ["FIREBASE_PROJECT_ID"] = "utxoiq"
os.environ["BIGQUERY_DATASET_INTEL"] = "intel"
os.environ["BIGQUERY_DATASET_BTC"] = "btc"
os.environ["VERTEX_AI_LOCATION"] = "us-central1"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_dummy"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

def main():
    """Run Alembic migrations."""
    print("=" * 60)
    print("Running Alembic Migrations on Cloud SQL")
    print("=" * 60)
    print()
    
    # Change to web-api directory
    os.chdir(web_api_path)
    
    print(f"Working directory: {os.getcwd()}")
    print(f"Database: {os.environ['DB_NAME']}")
    print(f"Cloud SQL Instance: {os.environ['CLOUD_SQL_CONNECTION_NAME']}")
    print()
    
    # Run Alembic upgrade
    print("Running: alembic upgrade head")
    print("-" * 60)
    
    exit_code = os.system("alembic upgrade head")
    
    print()
    if exit_code == 0:
        print("=" * 60)
        print("✅ Migrations completed successfully!")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ Migration failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
