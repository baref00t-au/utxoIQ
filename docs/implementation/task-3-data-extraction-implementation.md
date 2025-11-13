# Task 3: Data Extraction Module Implementation

## Overview

Implemented the Data Extraction Module for the signal-insight-pipeline, which provides methods to extract blockchain data from Bitcoin Core RPC and BigQuery for signal generation.

## Implementation Date

November 12, 2025

## Files Created

### 1. `services/utxoiq-ingestion/src/data_extraction.py`

**Purpose**: Core data extraction module for signal processing

**Key Components**:

#### Data Classes
- `MempoolStats`: Mempool statistics from Bitcoin Core RPC
  - Transaction count, size, fees
  - Fee rate percentiles (p25, median, p75)
  - Memory pool configuration

- `EntityInfo`: Known entity information (exchanges, mining pools, treasury companies)
  - Entity ID, name, type
  - Associated addresses
  - Metadata (e.g., ticker symbol, known holdings for treasury companies)

- `WhaleAddress`: Whale address detection results
  - Address, balance, output value

- `HistoricalSignal`: Historical signal data from BigQuery
  - Signal metadata, confidence, timestamps

#### DataExtractionModule Class

**Responsibilities**:
- Query Bitcoin Core RPC for mempool statistics
- Identify exchange addresses from known entities database
- Detect whale addresses (>1000 BTC balance)
- Query historical signal data from BigQuery

**Key Methods**:

1. `get_mempool_stats()` - Requirements 2.1, 2.5
   - Queries Bitcoin Core RPC for current mempool state
   - Calculates fee rate statistics (median, p25, p75)
   - Returns MempoolStats object with comprehensive mempool data

2. `get_historical_signals(signal_type, time_window)` - Requirements 2.1, 2.5
   - Queries BigQuery intel.signals table for historical data
   - Filters by signal type and time window
   - Returns list of HistoricalSignal objects for comparison

3. `identify_exchange_addresses(addresses)` - Requirements 2.2
   - Matches addresses against known entities database
   - Returns dictionary of identified exchange addresses
   - Automatically reloads entity cache every 5 minutes

4. `detect_whale_addresses(outputs)` - Requirements 2.3, 2.4
   - Analyzes transaction outputs for large balances
   - Queries BigQuery for address balance verification
   - Returns list of WhaleAddress objects exceeding threshold

**Internal Methods**:
- `_ensure_entities_loaded()`: Manages entity cache lifecycle
- `_load_known_entities()`: Loads entities from BigQuery btc.known_entities table
- `_get_address_balance(address)`: Queries address balance from BigQuery

### 2. `services/utxoiq-ingestion/src/entity_identification.py`

**Purpose**: Dedicated module for blockchain entity identification

**Key Components**:

#### EntityIdentificationModule Class

**Responsibilities**:
- Load known entities database on startup
- Match transaction addresses against entity database
- Identify exchanges (Coinbase, Kraken, Binance, Gemini, Bitstamp)
- Identify mining pools (Foundry USA, AntPool, F2Pool, ViaBTC, Binance Pool)
- Identify treasury companies (MicroStrategy, Tesla, Block, Marathon, Riot)
- Reload entity list periodically (every 5 minutes)

**Key Methods**:

1. `load_known_entities()` - Requirements 9.1, 9.7
   - Loads entities from btc.known_entities BigQuery table
   - Builds address -> EntityInfo mapping cache
   - Logs entity counts by type (exchange, mining_pool, treasury)

2. `identify_entity(address)` - Requirements 9.2, 9.3
   - Matches address against known entities cache
   - Auto-reloads cache if expired (5-minute interval)
   - Returns EntityInfo or None

3. `identify_mining_pool(coinbase_tx)` - Requirements 9.5
   - Extracts mining pool from coinbase transaction
   - Checks coinbase script signature for pool identifiers
   - Falls back to output address matching
   - Supports major pools: Foundry USA, AntPool, F2Pool, ViaBTC, Binance Pool, Poolin, BTC.com, Slush Pool

4. `identify_treasury_company(address)` - Requirements 9.3, 9.6
   - Identifies if address belongs to public company treasury
   - Returns EntityInfo with company ticker and known holdings
   - Filters for entity_type == 'treasury'

**Internal Methods**:
- `_should_reload()`: Checks if cache needs refresh
- `_count_by_type(entity_type)`: Counts entities by type for logging

### 3. Test Files

#### `services/utxoiq-ingestion/tests/test_data_extraction.py`

**Test Coverage**:
- Mempool stats retrieval (success and empty mempool cases)
- Exchange address identification (found and not found)
- Whale address detection
- Historical signal queries

**Test Cases**:
- `test_get_mempool_stats_success`: Verifies mempool stats calculation
- `test_get_mempool_stats_empty_mempool`: Handles empty mempool
- `test_identify_exchange_addresses_found`: Identifies known exchanges
- `test_identify_exchange_addresses_not_found`: Handles unknown addresses
- `test_detect_whale_addresses`: Detects addresses above threshold
- `test_get_historical_signals`: Queries historical data

#### `services/utxoiq-ingestion/tests/test_entity_identification.py`

**Test Coverage**:
- Entity loading from BigQuery
- Entity identification by address
- Mining pool identification from coinbase transactions
- Treasury company identification
- Cache reload logic

**Test Cases**:
- `test_load_known_entities`: Verifies entity loading
- `test_identify_entity_found`: Identifies known entities
- `test_identify_entity_not_found`: Handles unknown addresses
- `test_identify_mining_pool_from_script`: Identifies pools from script
- `test_identify_mining_pool_not_coinbase`: Rejects non-coinbase transactions
- `test_identify_treasury_company`: Identifies treasury addresses
- `test_identify_treasury_company_not_treasury`: Filters non-treasury entities
- `test_should_reload_*`: Tests cache reload logic
- `test_count_by_type`: Verifies entity counting

## Requirements Addressed

### Requirement 2.1: Signal Data Extraction - Mempool Statistics
✅ Implemented `get_mempool_stats()` method
- Queries Bitcoin Core RPC for mempool info
- Calculates fee rate percentiles
- Returns comprehensive MempoolStats object

### Requirement 2.2: Signal Data Extraction - Exchange Address Identification
✅ Implemented `identify_exchange_addresses()` method
- Matches addresses against known entities database
- Returns identified exchange entities
- Auto-reloads cache every 5 minutes

### Requirement 2.3: Signal Data Extraction - Whale Address Detection
✅ Implemented `detect_whale_addresses()` method
- Detects outputs to addresses with >1000 BTC balance
- Queries BigQuery for balance verification
- Configurable threshold via settings.whale_threshold_btc

### Requirement 2.4: Signal Data Extraction - Miner Treasury Tracking
✅ Implemented via EntityIdentificationModule
- `identify_mining_pool()` identifies mining pools
- Supports major pools with script signature parsing
- Falls back to output address matching

### Requirement 2.5: Signal Data Extraction - Historical Comparison
✅ Implemented `get_historical_signals()` method
- Queries BigQuery intel.signals table
- Filters by signal type and time window
- Returns historical signals for comparison

### Requirement 9.1: Known Entity Identification - Database Loading
✅ Implemented `load_known_entities()` method
- Loads from btc.known_entities BigQuery table
- Builds address -> entity mapping cache
- Logs entity counts by type

### Requirement 9.2: Known Entity Identification - Address Matching
✅ Implemented `identify_entity()` method
- Matches addresses against cache
- Returns EntityInfo with metadata
- Handles unknown addresses gracefully

### Requirement 9.3: Known Entity Identification - Exchange and Treasury
✅ Implemented entity type filtering
- `identify_exchange_addresses()` filters for exchanges
- `identify_treasury_company()` filters for treasury companies
- Includes entity metadata (ticker, holdings)

### Requirement 9.4: Known Entity Identification - Exchange Flow Grouping
✅ Supported via EntityInfo structure
- Entity ID and name included in results
- Enables grouping by entity_name in processors

### Requirement 9.5: Known Entity Identification - Mining Pool Detection
✅ Implemented `identify_mining_pool()` method
- Parses coinbase transaction scripts
- Identifies major mining pools
- Includes pool_name in results

### Requirement 9.6: Known Entity Identification - Treasury Tracking
✅ Implemented `identify_treasury_company()` method
- Identifies public company treasury addresses
- Returns metadata with ticker and known holdings
- Enables holdings change calculation

### Requirement 9.7: Known Entity Identification - Cache Reload
✅ Implemented automatic cache refresh
- 5-minute reload interval
- `_should_reload()` checks expiration
- Background reload on next query

## Integration Points

### Bitcoin Core RPC
- Uses `TorAuthServiceProxy` from `src.utils.tor_rpc`
- Calls `getmempoolinfo()` and `getrawmempool(True)`
- Calculates fee statistics from raw mempool data

### BigQuery
- Uses `BigQueryAdapter` for blockchain data queries
- Uses `bigquery.Client` for intel dataset queries
- Queries `btc.known_entities` table for entity data
- Queries `intel.signals` table for historical signals
- Queries `btc.transactions_unified` view for address balances

### Configuration
- Uses `settings` from `src.config`
- Configurable whale threshold: `settings.whale_threshold_btc`
- Configurable GCP project: `settings.gcp_project_id`
- Configurable datasets: `settings.bigquery_dataset_btc`, `settings.bigquery_dataset_intel`

## Data Models

### MempoolStats
```python
@dataclass
class MempoolStats:
    size: int                    # Number of transactions
    bytes: int                   # Total size in bytes
    usage: int                   # Memory usage
    total_fee: float             # Total fees in BTC
    maxmempool: int              # Maximum memory pool size
    mempoolminfee: float         # Minimum fee rate for tx acceptance
    minrelaytxfee: float         # Minimum relay fee rate
    unbroadcastcount: int        # Number of unbroadcast transactions
    fee_rate_median: float       # Median fee rate (sat/vB)
    fee_rate_p25: float          # 25th percentile fee rate
    fee_rate_p75: float          # 75th percentile fee rate
```

### EntityInfo
```python
@dataclass
class EntityInfo:
    entity_id: str               # Unique entity identifier
    entity_name: str             # Human-readable name
    entity_type: str             # exchange|mining_pool|treasury
    addresses: List[str]         # Known addresses
    metadata: Dict[str, Any]     # Type-specific metadata
```

### WhaleAddress
```python
@dataclass
class WhaleAddress:
    address: str                 # Bitcoin address
    balance_btc: float           # Current balance
    output_value_btc: float      # Transaction output value
```

### HistoricalSignal
```python
@dataclass
class HistoricalSignal:
    signal_id: str               # UUID
    signal_type: str             # Signal category
    block_height: int            # Block number
    confidence: float            # 0.0 to 1.0
    metadata: Dict[str, Any]     # Signal-specific data
    created_at: datetime         # Timestamp
```

## Usage Example

```python
from src.data_extraction import DataExtractionModule
from src.entity_identification import EntityIdentificationModule
from src.utils.tor_rpc import TorAuthServiceProxy
from src.adapters.bigquery_adapter import BigQueryAdapter
from google.cloud import bigquery

# Initialize clients
rpc = TorAuthServiceProxy("http://user:pass@localhost:8332")
bq_adapter = BigQueryAdapter(project_id="utxoiq-dev")
bq_client = bigquery.Client(project="utxoiq-dev")

# Create modules
data_extraction = DataExtractionModule(rpc, bq_adapter, bq_client)
entity_module = EntityIdentificationModule(bq_client)

# Load entities
await entity_module.load_known_entities()

# Get mempool stats
mempool_stats = await data_extraction.get_mempool_stats()
print(f"Mempool size: {mempool_stats.size} txs")
print(f"Median fee rate: {mempool_stats.fee_rate_median} sat/vB")

# Identify exchange addresses
addresses = ["bc1qtest1", "bc1qtest2"]
exchanges = await data_extraction.identify_exchange_addresses(addresses)
for addr, entity in exchanges.items():
    print(f"Exchange: {entity.entity_name} at {addr}")

# Detect whale addresses
outputs = [{"addresses": ["bc1qwhale"], "value": 150_000_000_000}]
whales = await data_extraction.detect_whale_addresses(outputs)
for whale in whales:
    print(f"Whale: {whale.address} with {whale.balance_btc} BTC")

# Get historical signals
from datetime import timedelta
signals = await data_extraction.get_historical_signals(
    signal_type="mempool",
    time_window=timedelta(hours=1)
)
print(f"Found {len(signals)} historical mempool signals")
```

## Next Steps

The Data Extraction Module is now complete and ready for integration with signal processors. The next tasks in the pipeline are:

1. **Task 4**: Implement Entity Identification Module (already completed as part of this task)
2. **Task 5**: Implement Signal Processors (mempool, exchange, miner, whale, treasury)
3. **Task 6**: Implement Predictive Analytics Module
4. **Task 7**: Implement Pipeline Orchestrator

## Notes

- The module uses async/await patterns for all I/O operations
- Entity cache automatically reloads every 5 minutes
- Whale threshold is configurable via settings (default: 1000 BTC)
- All methods include comprehensive error handling and logging
- BigQuery queries use parameterized queries to prevent SQL injection
- Address balance queries look back 30 days for performance
- Mining pool identification supports 8 major pools with fallback to address matching
- Treasury company identification includes metadata for holdings tracking
