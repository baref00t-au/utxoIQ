#!/usr/bin/env python3
"""
Create database tables directly using Cloud SQL Python Connector.
This bypasses Alembic and creates tables from SQL file.
"""
import asyncio
import asyncpg
from google.cloud.sql.connector import Connector
from pathlib import Path

# Configuration
INSTANCE_CONNECTION_NAME = "utxoiq-dev:us-central1:utxoiq-db-dev"
DB_USER = "postgres"
DB_PASSWORD = "utxoiq_SecurePass123!"
DB_NAME = "utxoiq"


async def create_tables():
    """Create all database tables."""
    print("=" * 60)
    print("Creating Database Tables")
    print("=" * 60)
    print()
    
    # Initialize Cloud SQL Connector in the same event loop
    loop = asyncio.get_event_loop()
    connector = Connector(loop=loop)
    
    try:
        # Connect to database
        print(f"Connecting to Cloud SQL instance: {INSTANCE_CONNECTION_NAME}")
        conn: asyncpg.Connection = await connector.connect_async(
            INSTANCE_CONNECTION_NAME,
            "asyncpg",
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
        )
        print("✅ Connected successfully!")
        print()
        
        # Read SQL file
        sql_file = Path(__file__).parent / "create-tables.sql"
        print(f"Reading SQL file: {sql_file}")
        sql_content = sql_file.read_text()
        print(f"✅ SQL file loaded ({len(sql_content)} characters)")
        print()
        
        # Execute SQL
        print("Executing SQL script...")
        print("-" * 60)
        
        try:
            # Execute the entire SQL script at once
            await conn.execute(sql_content)
            print("✅ All SQL commands executed successfully")
        except Exception as e:
            print(f"❌ Error executing SQL: {e}")
            raise
        
        print()
        print("-" * 60)
        
        # Verify tables were created
        print("Verifying tables...")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        print(f"\n✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        print()
        print("=" * 60)
        print("✅ Database tables created successfully!")
        print("=" * 60)
        
        # Close connection
        await conn.close()
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        raise
    
    finally:
        # Close connector
        await connector.close_async()


if __name__ == "__main__":
    asyncio.run(create_tables())
