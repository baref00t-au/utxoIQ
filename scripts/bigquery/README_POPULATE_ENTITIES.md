# Populate Known Entities Script

This script populates the `btc.known_entities` BigQuery table with known exchanges, mining pools, and treasury companies.

## Overview

The script inserts three types of entities:

1. **Exchanges** (5 entities)
   - Coinbase
   - Kraken
   - Binance
   - Gemini
   - Bitstamp

2. **Mining Pools** (5 entities)
   - Foundry USA
   - AntPool
   - F2Pool
   - ViaBTC
   - Binance Pool

3. **Treasury Companies** (5 entities)
   - MicroStrategy (MSTR) - ~152,800 BTC
   - Tesla (TSLA) - ~9,720 BTC
   - Block (SQ) - ~8,027 BTC
   - Marathon Digital (MARA) - ~26,842 BTC
   - Riot Platforms (RIOT) - ~9,334 BTC

## Prerequisites

1. **Python 3.12+** installed
2. **Google Cloud SDK** installed and authenticated
3. **BigQuery API** enabled in your GCP project
4. **Required Python package**:
   ```bash
   pip install google-cloud-bigquery
   ```

## Authentication

Authenticate with Google Cloud:

```bash
gcloud auth application-default login
```

Or set the service account key:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Usage

### Basic Usage

```bash
python scripts/bigquery/populate_known_entities.py
```

This will:
- Use the default GCP project from your environment
- Create the `btc.known_entities` table if it doesn't exist
- Insert all entities (exchanges, mining pools, treasury companies)

### Specify Project

```bash
python scripts/bigquery/populate_known_entities.py --project your-project-id
```

### Dry Run (Preview Only)

Preview what would be inserted without actually inserting:

```bash
python scripts/bigquery/populate_known_entities.py --dry-run
```

### Clear and Repopulate

Clear existing data before inserting (use with caution):

```bash
python scripts/bigquery/populate_known_entities.py --clear
```

## Output

The script will:

1. Create the table if it doesn't exist
2. Insert entities by type
3. Verify the inserted data
4. Display counts and samples

Example output:

```
Using GCP project: utxoiq-project
[OK] Table utxoiq-project.btc.known_entities already exists

Inserting 5 exchanges...
[OK] Successfully inserted 5 exchanges

Inserting 5 mining pools...
[OK] Successfully inserted 5 mining pools

Inserting 5 treasury companies...
[OK] Successfully inserted 5 treasury companies

Verifying inserted data...

Entity counts by type:
  exchange: 5
  mining_pool: 5
  treasury: 5

Sample entities:
  Binance (exchange)
    Addresses: 3
  Bitstamp (exchange)
    Addresses: 2
  Coinbase (exchange)
    Addresses: 4
  ...

[OK] Done!
```

## Important Notes

### Address Data

⚠️ **The addresses in this script are EXAMPLES and need to be updated with real addresses.**

To get real addresses:

1. **Exchanges**: Use blockchain explorers (e.g., Blockchain.com, Blockchair) to identify known exchange addresses
2. **Mining Pools**: Check coinbase transaction signatures and known payout addresses
3. **Treasury Companies**: Use public SEC filings and company disclosures

### Holdings Data

Treasury company holdings are approximate and should be updated regularly:

- Check company SEC filings (10-K, 10-Q, 8-K)
- Monitor company press releases
- Use services like bitcointreasuries.net for tracking

### Updating Data

To update entity data:

1. Edit the `EXCHANGES`, `MINING_POOLS`, or `TREASURY_COMPANIES` lists in the script
2. Run with `--clear` flag to replace all data:
   ```bash
   python scripts/bigquery/populate_known_entities.py --clear
   ```

Or manually update specific entities in BigQuery:

```sql
UPDATE `btc.known_entities`
SET 
  addresses = ['new_address_1', 'new_address_2'],
  metadata = JSON '{"ticker": "MSTR", "known_holdings_btc": 160000}',
  updated_at = CURRENT_TIMESTAMP()
WHERE entity_id = 'microstrategy_001';
```

## Table Schema

```sql
CREATE TABLE btc.known_entities (
  entity_id STRING NOT NULL,
  entity_name STRING NOT NULL,
  entity_type STRING NOT NULL,  -- exchange|mining_pool|treasury
  addresses ARRAY<STRING> NOT NULL,
  metadata JSON,
  updated_at TIMESTAMP NOT NULL
)
CLUSTER BY entity_type, entity_name;
```

## Querying the Data

### Get all exchanges

```sql
SELECT entity_name, ARRAY_LENGTH(addresses) as address_count
FROM `btc.known_entities`
WHERE entity_type = 'exchange'
ORDER BY entity_name;
```

### Get treasury companies with holdings

```sql
SELECT 
  entity_name,
  JSON_VALUE(metadata, '$.ticker') as ticker,
  CAST(JSON_VALUE(metadata, '$.known_holdings_btc') AS INT64) as holdings_btc
FROM `btc.known_entities`
WHERE entity_type = 'treasury'
ORDER BY holdings_btc DESC;
```

### Find entity by address

```sql
SELECT entity_name, entity_type
FROM `btc.known_entities`
WHERE 'bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrp' IN UNNEST(addresses);
```

## Troubleshooting

### Authentication Error

```
Error initializing BigQuery client: Could not automatically determine credentials
```

**Solution**: Run `gcloud auth application-default login`

### Permission Denied

```
403 Permission denied on dataset btc
```

**Solution**: Ensure your account has BigQuery Data Editor role:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/bigquery.dataEditor"
```

### Table Already Exists

If you need to recreate the table:

```sql
DROP TABLE IF EXISTS `btc.known_entities`;
```

Then run the script again.

## Integration with Signal Pipeline

This data is used by:

1. **EntityIdentificationModule** - Loads entities on startup and caches in memory
2. **ExchangeProcessor** - Identifies exchange flows
3. **MinerProcessor** - Identifies mining pools
4. **TreasuryProcessor** - Identifies corporate treasury movements

The entity cache reloads every 5 minutes, so updates to this table will be picked up automatically.

## Maintenance

### Regular Updates

Update this data:
- **Monthly**: Treasury company holdings (check SEC filings)
- **Quarterly**: Exchange addresses (monitor blockchain explorers)
- **As needed**: Mining pool addresses (when pools change payout addresses)

### Monitoring

Check entity usage in signals:

```sql
SELECT 
  JSON_VALUE(metadata, '$.entity_name') as entity_name,
  COUNT(*) as signal_count
FROM `intel.signals`
WHERE signal_type IN ('exchange', 'miner', 'treasury')
  AND DATE(created_at) >= CURRENT_DATE() - 7
GROUP BY entity_name
ORDER BY signal_count DESC;
```

## References

- [Requirements Document](.kiro/specs/signal-insight-pipeline/requirements.md) - Requirement 9.1, 9.2
- [Design Document](.kiro/specs/signal-insight-pipeline/design.md) - Entity Identification Module
- [BigQuery Schema](infrastructure/bigquery/schemas/btc_known_entities.sql)
