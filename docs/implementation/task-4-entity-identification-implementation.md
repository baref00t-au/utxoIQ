# Task 4: Entity Identification Module Implementation

## Overview

Implemented the Entity Identification Module with automatic cache refresh mechanism for the utxoIQ signal-insight pipeline. This module identifies known blockchain entities (exchanges, mining pools, treasury companies) from Bitcoin addresses.

## Implementation Summary

### Task 4.1: EntityIdentificationModule Class ✅

The `EntityIdentificationModule` class was already fully implemented with all required functionality:

**Location**: `services/utxoiq-ingestion/src/entity_identification.py`

**Key Methods Implemented**:
- `load_known_entities()` - Queries `btc.known_entities` BigQuery table and populates in-memory cache
- `identify_entity()` - Matches Bitcoin addresses against cached entity database with automatic reload check
- `identify_mining_pool()` - Parses coinbase transactions to identify mining pools from script signatures or output addresses
- `identify_treasury_company()` - Identifies public company treasury addresses with metadata (ticker, holdings)
- `_should_reload()` - Checks if cache should be reloaded based on 5-minute interval
- `_count_by_type()` - Utility method to count entities by type (exchange, mining_pool, treasury)

**Features**:
- Dual cache structure: address → EntityInfo and entity_id → EntityInfo for efficient lookups
- Automatic cache reload when expired (5-minute interval)
- Graceful error handling - continues with empty cache on load failures
- Comprehensive logging with entity counts by type
- Mining pool identification from both coinbase script signatures and output addresses
- Support for multiple pool identifiers (Foundry USA, AntPool, F2Pool, ViaBTC, Binance Pool, etc.)

### Task 4.2: Cache Reload Mechanism ✅

Added background task for automatic cache refresh:

**New Methods Added**:
- `_background_reload_task()` - Async background task that runs continuously
- `start_background_reload()` - Starts the background task (called on app startup)
- `stop_background_reload()` - Gracefully stops the background task (called on app shutdown)

**Background Task Features**:
- Performs initial entity load on startup
- Automatically reloads cache every 5 minutes
- Handles cancellation gracefully with proper cleanup
- Continues running despite errors (with 1-minute retry delay)
- Prevents duplicate task instances with state checking
- Comprehensive logging for monitoring and debugging

**Integration with FastAPI Application**:

Updated `services/utxoiq-ingestion/src/main.py`:
- Added imports for `EntityIdentificationModule` and `bigquery.Client`
- Initialized `entity_module` as global instance
- Added `@app.on_event("startup")` handler to start background reload
- Added `@app.on_event("shutdown")` handler to stop background reload gracefully

**Startup Flow**:
1. Application starts
2. `startup_event()` is triggered
3. `entity_module.start_background_reload()` is called
4. Background task performs initial entity load
5. Task continues running, reloading every 5 minutes

**Shutdown Flow**:
1. Application receives shutdown signal
2. `shutdown_event()` is triggered
3. `entity_module.stop_background_reload()` is called
4. Background task is cancelled and cleaned up

## Testing

### Test Coverage

Updated `services/utxoiq-ingestion/tests/test_entity_identification.py` with comprehensive tests:

**Existing Tests** (already passing):
- `test_load_known_entities` - Verifies BigQuery loading and cache population
- `test_identify_entity_found` - Tests successful entity identification
- `test_identify_entity_not_found` - Tests unknown address handling
- `test_identify_mining_pool_from_script` - Tests mining pool identification from coinbase script
- `test_identify_mining_pool_not_coinbase` - Tests non-coinbase transaction handling
- `test_identify_treasury_company` - Tests treasury company identification
- `test_identify_treasury_company_not_treasury` - Tests non-treasury entity filtering
- `test_should_reload_never_loaded` - Tests reload check when never loaded
- `test_should_reload_recently_loaded` - Tests reload check when recently loaded
- `test_should_reload_expired` - Tests reload check when cache expired
- `test_count_by_type` - Tests entity counting by type

**New Tests Added**:
- `test_background_reload_task_initial_load` - Verifies initial load on task start
- `test_start_background_reload` - Tests background task startup
- `test_stop_background_reload` - Tests background task shutdown
- `test_background_reload_already_running` - Tests duplicate start prevention
- `test_stop_background_reload_not_running` - Tests stopping when not running

## Requirements Satisfied

### Requirement 9.1 ✅
**Load known entities database on startup**
- `load_known_entities()` queries `btc.known_entities` table
- Background task performs initial load on startup
- Populates dual cache structure for efficient lookups

### Requirement 9.2 ✅
**Match addresses against known entities database**
- `identify_entity()` performs O(1) cache lookups
- Supports exchanges, mining pools, and treasury companies
- Returns `EntityInfo` with full metadata

### Requirement 9.3 ✅
**Include entity_id and entity_name in signal metadata**
- All identification methods return `EntityInfo` dataclass
- Contains `entity_id`, `entity_name`, `entity_type`, `addresses`, and `metadata`
- Ready for inclusion in signal metadata

### Requirement 9.5 ✅
**Identify mining pool from coinbase transaction**
- `identify_mining_pool()` parses coinbase script signatures
- Supports multiple pool identifiers (Foundry USA, AntPool, F2Pool, etc.)
- Falls back to output address matching if script parsing fails

### Requirement 9.7 ✅
**Reload entity list within 5 minutes without service restart**
- Background task automatically reloads every 5 minutes
- `_should_reload()` check prevents unnecessary reloads
- Graceful error handling ensures continuous operation

## Data Model

### EntityInfo Dataclass

```python
@dataclass
class EntityInfo:
    entity_id: str                    # Unique identifier
    entity_name: str                  # Human-readable name
    entity_type: str                  # exchange|mining_pool|treasury
    addresses: List[str]              # Known Bitcoin addresses
    metadata: Dict[str, Any]          # Type-specific metadata
```

**Treasury Metadata Example**:
```python
{
    "ticker": "MSTR",
    "known_holdings_btc": 152800
}
```

## Cache Structure

### Address Cache
- **Type**: `Dict[str, EntityInfo]`
- **Key**: Bitcoin address (string)
- **Value**: EntityInfo object
- **Purpose**: O(1) address lookups

### Entity ID Cache
- **Type**: `Dict[str, EntityInfo]`
- **Key**: entity_id (string)
- **Value**: EntityInfo object
- **Purpose**: Entity lookups by ID, type counting

## Mining Pool Identifiers

The module recognizes the following mining pools from coinbase scripts:

| Pool Name | Identifiers |
|-----------|-------------|
| Foundry USA | foundry, foundryusa |
| AntPool | antpool |
| F2Pool | f2pool, 鱼池 |
| ViaBTC | viabtc |
| Binance Pool | binance, binancepool |
| Poolin | poolin |
| BTC.com | btc.com |
| Slush Pool | slushpool, braiins |

## Configuration

### Environment Variables

The module uses settings from `src.config.settings`:
- `gcp_project_id` - GCP project ID for BigQuery
- `bigquery_dataset_btc` - BigQuery dataset name (default: "btc")

### Cache Settings

- **Reload Interval**: 5 minutes (configurable via `reload_interval` attribute)
- **Background Task**: Runs continuously until application shutdown
- **Error Retry**: 1 minute delay on background task errors

## Integration Points

### Current Integration
- **utxoiq-ingestion service**: Background task runs automatically on startup

### Future Integration (Upcoming Tasks)
- **Signal Processors**: Will use `identify_entity()` for address matching
- **Exchange Processor**: Will use entity identification for flow tracking
- **Miner Processor**: Will use `identify_mining_pool()` for coinbase transactions
- **Treasury Processor**: Will use `identify_treasury_company()` for corporate tracking

## Performance Considerations

### Cache Efficiency
- **O(1) lookups**: Direct dictionary access for address identification
- **In-memory storage**: No database queries during signal processing
- **Batch loading**: Single query loads all entities at once

### Background Task Overhead
- **Minimal CPU**: Sleeps between reloads (5-minute intervals)
- **Async execution**: Non-blocking, doesn't impact request handling
- **Graceful degradation**: Continues with stale cache on load failures

## Logging

### Log Levels

**INFO**:
- Module initialization
- Entity load completion with counts
- Background task start/stop

**DEBUG**:
- Mining pool identification results
- Background task reload triggers
- Cache reload checks

**WARNING**:
- Duplicate background task start attempts
- Mining pool identification failures

**ERROR**:
- Entity load failures
- Background task errors

### Log Format

All logs include structured context:
```python
logger.info(
    f"Loaded {entity_count} entities with {address_count} addresses "
    f"(exchanges: {exchange_count}, mining_pools: {pool_count}, treasury: {treasury_count})"
)
```

## Next Steps

The Entity Identification Module is now complete and ready for integration with signal processors:

1. **Task 5**: Implement Signal Processors (will use entity identification)
2. **Task 19**: Populate known entities database (seed data for testing)

## Files Modified

1. `services/utxoiq-ingestion/src/entity_identification.py`
   - Added `asyncio` import
   - Added `_background_task`, `_shutdown` attributes
   - Added `_background_reload_task()` method
   - Added `start_background_reload()` method
   - Added `stop_background_reload()` method

2. `services/utxoiq-ingestion/src/main.py`
   - Added imports for `EntityIdentificationModule` and `bigquery.Client`
   - Added `entity_module` global instance
   - Added `startup_event()` handler
   - Added `shutdown_event()` handler

3. `services/utxoiq-ingestion/tests/test_entity_identification.py`
   - Added `asyncio` import
   - Added 5 new test cases for background task functionality

## Verification

✅ All subtasks completed
✅ No syntax errors (verified with getDiagnostics)
✅ Comprehensive test coverage
✅ Requirements 9.1, 9.2, 9.3, 9.5, 9.7 satisfied
✅ Integration with FastAPI application complete
✅ Background task lifecycle management implemented
