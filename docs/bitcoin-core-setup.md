# Bitcoin Core Setup for utxoIQ

## Quick Start

### Option 1: Use Bitcoin Core (Recommended for Production)

#### 1. Install Bitcoin Core
Download from: https://bitcoin.org/en/download

#### 2. Configure bitcoin.conf
Location: `%APPDATA%\Bitcoin\bitcoin.conf` (Windows)

```conf
# RPC Settings
server=1
rpcuser=utxoiq
rpcpassword=<generate-strong-password>
rpcport=8332
rpcallowip=127.0.0.1

# Network
testnet=0  # Use mainnet
txindex=1  # Required for transaction lookups

# Performance
dbcache=4096
maxmempool=300
```

#### 3. Start Bitcoin Core
```bash
bitcoind -daemon
```

#### 4. Wait for Sync
```bash
bitcoin-cli getblockchaininfo
```

#### 5. Test Connection
```bash
python scripts/test-bitcoin-connection.py --rpc-url http://utxoiq:<password>@localhost:8332
```

### Option 2: Use Public BigQuery Dataset Only (Fastest)

Since the public dataset is 0 hours behind, you can skip Bitcoin Core entirely for now:

**Advantages:**
- No Bitcoin Core setup needed
- No sync wait time
- Immediate access to all historical data
- 0 hours lag (essentially real-time)

**Limitations:**
- No sub-hour real-time data
- Can't add custom processing
- Dependent on Google's update schedule

**Implementation:**
Just use the unified views - they'll automatically use public dataset:

```python
# This works immediately without Bitcoin Core
blocks = bq_adapter.query_recent_blocks(hours=24, limit=100)
```

### Option 3: Use Bitcoin RPC API Services

Use a hosted Bitcoin node service:

**Services:**
- BlockCypher API
- Blockchain.com API
- QuickNode
- Alchemy

**Example with BlockCypher:**
```python
import requests

def get_latest_block():
    response = requests.get('https://api.blockcypher.com/v1/btc/main')
    return response.json()
```

## Recommended Approach for Development

### Phase 1: Use Public Dataset Only
1. ✅ Already complete - unified views are set up
2. ✅ Query public dataset for all data
3. ✅ Test application with historical data
4. ✅ Develop features without Bitcoin Core

### Phase 2: Add Bitcoin Core Later
1. Install and sync Bitcoin Core
2. Run backfill script for last hour
3. Enable real-time ingestion
4. Get sub-hour competitive advantage

## Current Status

**Public Dataset:**
- ✅ Available and working
- ✅ 0 hours lag
- ✅ 923,123+ blocks
- ✅ Full transaction history with nested inputs/outputs

**Custom Dataset:**
- ✅ Tables created and ready
- ✅ Views configured with deduplication
- ⏳ Waiting for Bitcoin Core to backfill
- ⏳ Real-time ingestion pending

## Testing Without Bitcoin Core

You can test everything except real-time ingestion:

```bash
# Test unified views (uses public dataset)
python scripts/test-hybrid-setup.py

# Test deduplication
python scripts/test-deduplication.py

# Deploy feature-engine (will work with public data)
cd services/feature-engine
gcloud run deploy feature-engine --source .
```

## When to Add Bitcoin Core

Add Bitcoin Core when you need:
- Sub-hour real-time insights (competitive advantage)
- Custom processing on raw block data
- Independence from public dataset
- Ability to add custom features

## Cost Comparison

### Public Dataset Only
- Storage: $0/month (using Google's data)
- Queries: $25-30/month
- **Total: ~$30/month**

### Public + Bitcoin Core (1-hour buffer)
- Storage: $0.002/month (tiny custom dataset)
- Queries: $25-30/month
- Bitcoin Core: $0/month (self-hosted)
- **Total: ~$30/month**

**Conclusion:** Same cost either way! The hybrid approach is ready whenever you add Bitcoin Core.

## Next Steps

### Without Bitcoin Core (Immediate)
1. ✅ Deploy feature-engine service
2. ✅ Set up Cloud Scheduler for cleanup
3. ✅ Monitor query costs
4. ✅ Develop application features

### With Bitcoin Core (Later)
1. Install and sync Bitcoin Core
2. Run backfill script
3. Enable real-time ingestion
4. Get sub-hour insights

## Support

For Bitcoin Core setup help:
- Official docs: https://bitcoin.org/en/full-node
- RPC documentation: https://developer.bitcoin.org/reference/rpc/
- Community: https://bitcoin.stackexchange.com/
