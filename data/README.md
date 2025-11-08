# Backfill Data Directory

This directory stores blockchain data from the backfill process.

## Structure

```
data/backfill/
├── blocks/
│   ├── 0000000/          # Blocks 0-9,999
│   │   ├── block_0000000.json
│   │   ├── block_0000001.json
│   │   └── ...
│   ├── 0010000/          # Blocks 10,000-19,999
│   └── ...
└── transactions/
    ├── 0000000/          # Transactions for blocks 0-9,999
    │   ├── txs_0000000.json
    │   ├── txs_0000001.json
    │   └── ...
    └── ...
```

## File Format

### Block Files
Each block file contains normalized block data:
```json
{
  "height": 123456,
  "hash": "00000000000000000001234...",
  "timestamp": 1234567890,
  "size": 1234567,
  "tx_count": 2500,
  ...
}
```

### Transaction Files
Each transaction file contains an array of normalized transactions:
```json
[
  {
    "txid": "abc123...",
    "block_height": 123456,
    "inputs": [...],
    "outputs": [...],
    ...
  }
]
```

## Usage

### Import to BigQuery

Once you have GCP credentials configured, you can import this data:

```bash
# Import blocks
bq load --source_format=NEWLINE_DELIMITED_JSON \
  btc.blocks \
  data/backfill/blocks/*/*.json

# Import transactions
bq load --source_format=NEWLINE_DELIMITED_JSON \
  btc.transactions \
  data/backfill/transactions/*/*.json
```

### Query Locally

You can also query the JSON files directly with tools like `jq`:

```bash
# Count total blocks
find data/backfill/blocks -name "*.json" | wc -l

# View a specific block
cat data/backfill/blocks/0000000/block_0000100.json | jq .

# Find blocks with high transaction counts
find data/backfill/blocks -name "*.json" -exec jq -r 'select(.tx_count > 2000) | "\(.height): \(.tx_count) txs"' {} \;
```

## Storage Estimates

- **Block file**: ~1-5 KB per block
- **Transaction file**: ~10-500 KB per block (varies widely)
- **Total for 922,000 blocks**: ~50-100 GB

## Cleanup

To remove old data:

```bash
# Remove all backfill data
rm -rf data/backfill

# Remove specific range
rm -rf data/backfill/blocks/0000000
rm -rf data/backfill/transactions/0000000
```
