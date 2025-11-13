# Task 5: Signal Processors Implementation

## Overview

Implemented the complete signal processor architecture for the utxoIQ intelligence pipeline, including a base abstract class and five concrete processor implementations.

## Implementation Summary

### 5.1 Base SignalProcessor Abstract Class ✅

**File**: `services/utxoiq-ingestion/src/processors/base_processor.py`

Created the foundational abstract base class that defines the interface for all signal processors:

**Key Components**:
- `ProcessorConfig`: Configuration class for processor settings (enabled flag, confidence threshold, time window)
- `ProcessingContext`: Context data container for block processing (block data, historical data, correlation ID)
- `SignalProcessor`: Abstract base class with:
  - `process_block()`: Abstract method that all processors must implement
  - `calculate_confidence()`: Helper method for standardized confidence scoring
  - `should_generate_signal()`: Threshold checking method
  - `create_signal()`: Factory method for creating signal objects

**Features**:
- Configurable enabled flag and confidence thresholds
- Standard confidence calculation based on data quality, signal strength, entity knowledge, and amounts
- Type-safe signal creation with proper enum mapping

### 5.2 MempoolProcessor ✅

**File**: `services/utxoiq-ingestion/src/processors/mempool_processor.py`

Updated existing processor to inherit from base class and added required metadata fields.

**Key Features**:
- Analyzes mempool fee rate changes vs historical data
- Generates signals for significant fee spikes (>20% change)
- Includes required metadata:
  - `fee_rate_median`: Median fee rate from quantiles
  - `fee_rate_change_pct`: Percentage change from historical average
  - `mempool_size_mb`: Mempool size in megabytes
  - `tx_count`: Transaction count

**Implementation**:
- Added async `process_block()` method matching base class interface
- Inherits from `SignalProcessor` with proper configuration
- Maintains existing fee quantile calculation and block inclusion time estimation logic

### 5.3 ExchangeProcessor ✅

**File**: `services/utxoiq-ingestion/src/processors/exchange_processor.py`

Updated existing processor to inherit from base class and added required metadata fields.

**Key Features**:
- Detects exchange inflows and outflows using entity identification
- Tracks per-exchange flow volumes
- Includes required metadata:
  - `entity_id`: Exchange entity identifier
  - `entity_name`: Exchange name (Coinbase, Kraken, etc.)
  - `flow_type`: "inflow", "outflow", or "balanced"
  - `amount_btc`: Primary flow amount
  - `tx_count`: Transaction count

**Implementation**:
- Added async `process_block()` method for batch processing
- Determines flow type based on net flow direction
- Maintains existing anomaly detection and z-score analysis

### 5.4 MinerProcessor ✅

**File**: `services/utxoiq-ingestion/src/processors/miner_processor.py`

Updated existing processor to inherit from base class and added required metadata fields.

**Key Features**:
- Identifies mining pool from coinbase transaction
- Tracks miner treasury balance changes
- Includes required metadata:
  - `pool_name`: Mining pool name (Foundry USA, AntPool, etc.)
  - `amount_btc`: Absolute value of balance change
  - `treasury_balance_change`: Signed balance change

**Implementation**:
- Added async `process_block()` method for batch processing
- Maintains existing daily balance change calculation
- Preserves treasury delta computation and spending pattern analysis

### 5.5 WhaleProcessor ✅

**File**: `services/utxoiq-ingestion/src/processors/whale_processor.py`

Updated existing processor to inherit from base class and added required metadata fields.

**Key Features**:
- Detects transactions to/from addresses with >1000 BTC balance
- Calculates whale movement significance
- Includes required metadata:
  - `whale_address`: Bitcoin address of whale wallet
  - `amount_btc`: Absolute value of 7-day change
  - `balance_btc`: Current balance

**Implementation**:
- Added async `process_block()` method for batch processing
- Maintains existing accumulation pattern analysis
- Preserves whale tier classification and streak tracking

### 5.6 TreasuryProcessor ✅

**File**: `services/utxoiq-ingestion/src/processors/treasury_processor.py`

Created new processor for tracking public company Bitcoin treasury movements.

**Key Features**:
- Identifies public company treasury transactions using entity identification
- Tracks accumulation and distribution patterns
- Calculates holdings change percentage
- Includes required metadata:
  - `entity_name`: Company name (MicroStrategy, Tesla, etc.)
  - `company_ticker`: Stock ticker (MSTR, TSLA, etc.)
  - `flow_type`: "accumulation" or "distribution"
  - `amount_btc`: Transaction amount
  - `known_holdings_btc`: Known total holdings
  - `holdings_change_pct`: Percentage change in holdings

**Implementation**:
- Scans transaction inputs for distribution (company selling)
- Scans transaction outputs for accumulation (company buying)
- Confidence scoring based on amount significance and entity reputation
- Requires entity identification module injection

**Target Companies**:
- MicroStrategy (MSTR): ~152,800 BTC
- Tesla (TSLA): ~9,720 BTC
- Block (SQ): ~8,027 BTC
- Marathon Digital (MARA): ~26,842 BTC
- Riot Platforms (RIOT): ~9,334 BTC

## Architecture Patterns

### Inheritance Hierarchy
```
SignalProcessor (ABC)
├── MempoolProcessor
├── ExchangeProcessor
├── MinerProcessor
├── WhaleProcessor
└── TreasuryProcessor
```

### Configuration Pattern
All processors accept optional `ProcessorConfig` with:
- `enabled`: Boolean flag to enable/disable processor
- `confidence_threshold`: Minimum confidence for signal generation (default 0.7)
- `time_window`: Historical data window (e.g., "1h", "24h", "7d")

### Processing Pattern
All processors implement:
```python
async def process_block(
    self,
    block: BlockData,
    context: ProcessingContext
) -> List[Signal]:
    # Extract relevant data from context
    # Generate signals
    # Filter by confidence threshold
    # Return list of signals
```

## Integration Points

### Entity Identification Module
- ExchangeProcessor: Uses entity module to identify exchange addresses
- TreasuryProcessor: Uses entity module to identify company treasury addresses
- Both require entity module injection via `set_entity_module()`

### Data Extraction Module
- All processors expect relevant data in `ProcessingContext.historical_data`
- Keys: `mempool_data`, `exchange_flows`, `miner_data`, `whale_data`, `transactions`
- Historical data for comparison: `historical_mempool`, `historical_exchange_flows`, etc.

### Signal Persistence Module
- All processors return `List[Signal]` objects
- Signals include:
  - `type`: SignalType enum (MEMPOOL, EXCHANGE, MINER, WHALE, PREDICTIVE)
  - `strength`: Confidence score (0.0 to 1.0)
  - `data`: Metadata dictionary with processor-specific fields
  - `block_height`: Block where signal was detected
  - `transaction_ids`: Evidence transaction IDs
  - `entity_ids`: Involved entity IDs

## Requirements Coverage

### Requirement 1.1 ✅
Signal Persistence Module invokes all registered signal processors (mempool, exchange, miner, whale, treasury)

### Requirement 2.1 ✅
MempoolProcessor queries mempool statistics and generates signals for fee spikes

### Requirement 2.2 ✅
ExchangeProcessor identifies exchange addresses and tracks flows

### Requirement 2.3 ✅
WhaleProcessor detects whale addresses with >1000 BTC balance

### Requirement 2.4 ✅
MinerProcessor tracks miner treasury addresses and balance changes

### Requirement 7.2 ✅
All processors have enabled flag configuration

### Requirement 7.3 ✅
All processors apply confidence threshold filtering

### Requirement 9.3 ✅
ExchangeProcessor and TreasuryProcessor include entity_id and entity_name in metadata

### Requirement 9.4 ✅
ExchangeProcessor groups flows by entity_name

### Requirement 9.5 ✅
MinerProcessor identifies mining pool and includes pool_name in metadata

### Requirement 9.6 ✅
TreasuryProcessor tracks public company treasury movements and calculates holdings change

## Testing Recommendations

### Unit Tests
1. Test each processor's confidence calculation logic
2. Test signal generation with mock data
3. Test threshold filtering
4. Test metadata structure validation

### Integration Tests
1. Test processor initialization with configuration
2. Test process_block with realistic block data
3. Test entity module integration
4. Test historical data handling

### Example Test Cases
```python
# Test MempoolProcessor
async def test_mempool_processor_fee_spike():
    processor = MempoolProcessor()
    context = ProcessingContext(
        block=mock_block,
        historical_data={
            'mempool_data': mock_mempool_data,
            'historical_mempool': mock_historical_data
        }
    )
    signals = await processor.process_block(mock_block, context)
    assert len(signals) > 0
    assert signals[0].data['fee_rate_change_pct'] > 20

# Test TreasuryProcessor
async def test_treasury_processor_accumulation():
    processor = TreasuryProcessor()
    processor.set_entity_module(mock_entity_module)
    context = ProcessingContext(
        block=mock_block,
        historical_data={
            'transactions': mock_treasury_transactions
        }
    )
    signals = await processor.process_block(mock_block, context)
    assert len(signals) > 0
    assert signals[0].data['flow_type'] == 'accumulation'
    assert signals[0].data['company_ticker'] == 'MSTR'
```

## Next Steps

1. **Task 6**: Implement Predictive Analytics Module
   - Fee forecast signals using exponential smoothing
   - Liquidity pressure signals using z-score normalization

2. **Task 7**: Implement Pipeline Orchestrator
   - Coordinate all processors
   - Handle errors gracefully
   - Emit timing metrics

3. **Task 9**: Integrate into utxoiq-ingestion service
   - Wire processors into block monitor
   - Trigger signal generation on new blocks
   - Persist signals to BigQuery

## Files Modified

1. `services/utxoiq-ingestion/src/processors/base_processor.py` (NEW)
2. `services/utxoiq-ingestion/src/processors/mempool_processor.py` (UPDATED)
3. `services/utxoiq-ingestion/src/processors/exchange_processor.py` (UPDATED)
4. `services/utxoiq-ingestion/src/processors/miner_processor.py` (UPDATED)
5. `services/utxoiq-ingestion/src/processors/whale_processor.py` (UPDATED)
6. `services/utxoiq-ingestion/src/processors/treasury_processor.py` (NEW)
7. `services/utxoiq-ingestion/src/processors/__init__.py` (UPDATED)

## Summary

Successfully implemented all signal processors with:
- ✅ Base abstract class with standard interface
- ✅ Configuration support for all processors
- ✅ Async processing pattern
- ✅ Required metadata fields for each signal type
- ✅ Confidence scoring and threshold filtering
- ✅ Entity identification integration
- ✅ Treasury company tracking (new feature)

All processors are ready for integration into the pipeline orchestrator and can be configured independently via environment variables.
