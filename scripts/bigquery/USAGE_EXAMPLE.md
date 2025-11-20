# Quick Usage Examples

## 1. Preview what will be inserted (Dry Run)

```bash
python scripts/bigquery/populate_known_entities.py --dry-run
```

This shows all entities that would be inserted without actually inserting them.

## 2. Insert entities into BigQuery

```bash
# Using default project from environment
python scripts/bigquery/populate_known_entities.py

# Or specify project explicitly
python scripts/bigquery/populate_known_entities.py --project utxoiq-dev
```

## 3. Clear and repopulate (use with caution)

```bash
python scripts/bigquery/populate_known_entities.py --clear
```

This will delete all existing entities and insert fresh data.

## 4. Update specific entity holdings

After initial population, you can update specific entities directly in BigQuery:

```sql
-- Update MicroStrategy holdings
UPDATE `btc.known_entities`
SET 
  metadata = JSON '{"ticker": "MSTR", "known_holdings_btc": 160000, "company_type": "business_intelligence", "public_company": true}',
  updated_at = CURRENT_TIMESTAMP()
WHERE entity_id = 'microstrategy_001';

-- Add new address to Coinbase
UPDATE `btc.known_entities`
SET 
  addresses = ARRAY_CONCAT(addresses, ['bc1qnewaddress123456789']),
  updated_at = CURRENT_TIMESTAMP()
WHERE entity_id = 'coinbase_001';
```

## 5. Verify inserted data

```sql
-- Count entities by type
SELECT entity_type, COUNT(*) as count
FROM `btc.known_entities`
GROUP BY entity_type;

-- View all treasury companies with holdings
SELECT 
  entity_name,
  JSON_VALUE(metadata, '$.ticker') as ticker,
  CAST(JSON_VALUE(metadata, '$.known_holdings_btc') AS INT64) as holdings_btc
FROM `btc.known_entities`
WHERE entity_type = 'treasury'
ORDER BY holdings_btc DESC;

-- Find entity by address
SELECT entity_name, entity_type, ARRAY_LENGTH(addresses) as address_count
FROM `btc.known_entities`
WHERE 'bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrp' IN UNNEST(addresses);
```

## Expected Output

When running successfully, you should see:

```
Using GCP project: utxoiq-dev
[OK] Table utxoiq-dev.btc.known_entities already exists

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
  Coinbase (exchange)
    Addresses: 4
  MicroStrategy (treasury)
    Addresses: 3
    Metadata: {"ticker":"MSTR","known_holdings_btc":152800,...}
  ...

[OK] Done!
```

## Troubleshooting

### Error: Could not automatically determine credentials

**Solution:**
```bash
gcloud auth application-default login
```

### Error: Permission denied

**Solution:**
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/bigquery.dataEditor"
```

### Error: Table not found

The script will automatically create the table if it doesn't exist. If you need to recreate it:

```sql
DROP TABLE IF EXISTS `btc.known_entities`;
```

Then run the script again.

## Integration with Services

Once populated, this data is automatically used by:

1. **utxoiq-ingestion service**
   - EntityIdentificationModule loads entities on startup
   - Cached in memory for fast lookups
   - Reloads every 5 minutes

2. **Signal Processors**
   - ExchangeProcessor: Identifies exchange flows
   - MinerProcessor: Identifies mining pools
   - TreasuryProcessor: Identifies corporate treasury movements

3. **Insight Generation**
   - Entity names appear in AI-generated insights
   - Example: "Coinbase outflow of 1,250 BTC detected"

## Maintenance Schedule

- **Weekly**: Check for new exchange addresses
- **Monthly**: Update treasury company holdings
- **Quarterly**: Review and update mining pool addresses
- **As needed**: Add new entities or remove inactive ones
