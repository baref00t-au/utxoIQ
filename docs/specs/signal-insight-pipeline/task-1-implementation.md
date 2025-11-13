# Task 1 Implementation: BigQuery Schema and Data Models

## Overview

This document describes the implementation of Task 1 from the signal-insight-pipeline spec: setting up BigQuery schemas and Python Pydantic models for the signal-to-insight pipeline.

## Completed Components

### 1. BigQuery Schema Definitions

Created SQL schema files in `infrastructure/bigquery/schemas/`:

#### intel.signals Table
- **File**: `intel_signals.sql`
- **Purpose**: Stores computed blockchain signals with metadata and confidence scores
- **Partitioning**: Daily partitioning by `created_at` for efficient time-range queries
- **Clustering**: By `signal_type` and `block_height` for optimized filtering
- **Key Features**:
  - UUID-based signal identification
  - Support for 6 signal types: mempool, exchange, miner, whale, treasury, predictive
  - JSON metadata field for flexible signal-specific data
  - Processing tracking with `processed` and `processed_at` fields
  - Confidence scoring from 0.0 to 1.0

#### intel.insights Table
- **File**: `intel_insights.sql`
- **Purpose**: Stores AI-generated insights from blockchain signals
- **Partitioning**: Daily partitioning by `created_at`
- **Clustering**: By `category` and `confidence` for efficient filtering
- **Key Features**:
  - Links to source signals via `signal_id`
  - Structured evidence with block heights and transaction IDs
  - Headline limited to 80 characters
  - Chart URL field (populated later by chart-renderer)
  - Confidence score inherited from source signal

#### btc.known_entities Table
- **File**: `btc_known_entities.sql`
- **Purpose**: Stores identified exchanges, mining pools, and treasury companies
- **Clustering**: By `entity_type` and `entity_name`
- **Key Features**:
  - Support for 3 entity types: exchange, mining_pool, treasury
  - Array of Bitcoin addresses per entity
  - JSON metadata for treasury-specific data (ticker, holdings)
  - Timestamp tracking for entity updates

### 2. Python Pydantic Models

Created comprehensive data models in `shared/types/signal_models.py`:

#### Core Models

**Signal Model**
- Represents computed blockchain signals
- Validates signal_type enum (6 types)
- Enforces confidence range (0.0 to 1.0)
- Validates non-negative block heights
- Supports flexible metadata dictionary
- Tracks processing state

**Insight Model**
- Represents AI-generated insights
- Validates headline length (max 80 chars)
- Links to source signal
- Includes structured Evidence
- Supports optional chart URL
- Inherits confidence from signal

**Evidence Model**
- Blockchain proof for insights
- Arrays of block heights and transaction IDs
- Validates non-negative block heights
- Supports empty arrays for initialization

**EntityInfo Model**
- Represents known blockchain entities
- Validates entity_type enum (3 types)
- Requires at least one address
- Supports flexible metadata dictionary
- Tracks update timestamps

#### Specialized Metadata Models

Created typed metadata models for each signal type:
- `MempoolSignalMetadata`: Fee rates, mempool size, transaction counts
- `ExchangeSignalMetadata`: Entity info, flow type, amounts, addresses
- `TreasurySignalMetadata`: Company info, ticker, holdings, changes
- `MinerSignalMetadata`: Pool name, amounts, treasury changes
- `WhaleSignalMetadata`: Whale address, amounts, balances
- `PredictiveSignalMetadata`: Predictions, confidence intervals, forecasts

### 3. Deployment Scripts

#### Shell Script (Linux/Mac)
- **File**: `scripts/setup/create-signal-tables.sh`
- **Features**:
  - Creates intel and btc datasets if needed
  - Deploys all three tables
  - Verifies table creation
  - Provides next steps guidance
  - Color-coded output for clarity

#### Batch Script (Windows)
- **File**: `scripts/setup/create-signal-tables.bat`
- **Features**:
  - Windows-compatible deployment
  - Same functionality as shell script
  - Error handling and validation
  - Clear success/failure messages

### 4. Entity Population Script

**File**: `scripts/populate_treasury_entities.py`

**Features**:
- Populates btc.known_entities with real-world data
- Includes 8 treasury companies with known BTC holdings
- Includes 5 major exchanges
- Includes 5 major mining pools
- Supports dry-run mode for testing
- Provides detailed summary output

**Treasury Companies Included**:
1. MicroStrategy (MSTR): 152,800 BTC
2. Tesla (TSLA): 9,720 BTC
3. Block (SQ): 8,027 BTC
4. Marathon Digital (MARA): 26,842 BTC
5. Riot Platforms (RIOT): 9,334 BTC
6. Coinbase (COIN): 9,000 BTC
7. Galaxy Digital (GLXY): 15,449 BTC
8. Hut 8 Mining (HUT): 9,102 BTC

**Total Treasury Holdings**: 240,274 BTC

### 5. Testing

**File**: `shared/types/test_signal_models.py`

**Test Coverage**:
- Signal model validation (valid/invalid cases)
- Evidence model validation
- Insight model validation (headline length, empty checks)
- EntityInfo model validation (addresses, entity types)
- Metadata model validation for all signal types
- Confidence score validation
- Block height validation
- Enum validation for signal and entity types

### 6. Documentation

**File**: `infrastructure/bigquery/schemas/README.md`

**Contents**:
- Table descriptions and schemas
- Deployment instructions
- Query examples
- Maintenance guidelines
- Cost optimization tips
- Partition management
- Related files references

## Usage Instructions

### 1. Deploy BigQuery Tables

**Linux/Mac**:
```bash
cd scripts/setup
chmod +x create-signal-tables.sh
./create-signal-tables.sh your-project-id
```

**Windows**:
```cmd
cd scripts\setup
create-signal-tables.bat your-project-id
```

**Or using environment variable**:
```bash
export GCP_PROJECT_ID=your-project-id
./create-signal-tables.sh
```

### 2. Populate Known Entities

```bash
# Dry run to preview data
python scripts/populate_treasury_entities.py --project-id your-project-id --dry-run

# Actual insertion
python scripts/populate_treasury_entities.py --project-id your-project-id
```

### 3. Verify Tables

```bash
# List tables
bq ls --project_id=your-project-id intel
bq ls --project_id=your-project-id btc

# Show schemas
bq show --project_id=your-project-id intel.signals
bq show --project_id=your-project-id intel.insights
bq show --project_id=your-project-id btc.known_entities

# Query data
bq query --project_id=your-project-id --use_legacy_sql=false \
  "SELECT entity_name, entity_type FROM btc.known_entities LIMIT 10"
```

### 4. Use Python Models

```python
from shared.types.signal_models import Signal, SignalType, EntityInfo, EntityType
from datetime import datetime
import uuid

# Create a signal
signal = Signal(
    signal_id=str(uuid.uuid4()),
    signal_type=SignalType.MEMPOOL,
    block_height=800000,
    confidence=0.85,
    metadata={
        "fee_rate_median": 50.5,
        "fee_rate_change_pct": 25.3,
        "tx_count": 15000,
        "mempool_size_mb": 120.5,
        "comparison_window": "1h"
    },
    created_at=datetime.utcnow()
)

# Validate and serialize
signal_dict = signal.model_dump()
signal_json = signal.model_dump_json()

# Create an entity
entity = EntityInfo(
    entity_id="microstrategy_001",
    entity_name="MicroStrategy",
    entity_type=EntityType.TREASURY,
    addresses=["bc1q123", "bc1q456"],
    metadata={
        "ticker": "MSTR",
        "known_holdings_btc": 152800
    },
    updated_at=datetime.utcnow()
)
```

### 5. Run Tests

```bash
cd shared/types
pytest test_signal_models.py -v
```

## Schema Design Decisions

### 1. Partitioning Strategy
- **Daily partitioning** by `created_at` for both signals and insights
- Optimizes time-range queries (common use case)
- Reduces query costs by scanning only relevant partitions
- Aligns with 60-second pipeline SLA (queries typically within same day)

### 2. Clustering Strategy
- **intel.signals**: Clustered by `signal_type` and `block_height`
  - Enables efficient filtering by signal type
  - Supports block-range queries for historical analysis
- **intel.insights**: Clustered by `category` and `confidence`
  - Optimizes category-based filtering for UI
  - Supports confidence-based filtering (e.g., high-confidence only)
- **btc.known_entities**: Clustered by `entity_type` and `entity_name`
  - Enables efficient entity type filtering
  - Supports entity name lookups

### 3. JSON Metadata Fields
- Flexible schema for signal-specific data
- Avoids rigid column structure
- Supports evolution of signal types
- BigQuery native JSON support for querying

### 4. Processing Tracking
- `processed` boolean flag for insight generation
- `processed_at` timestamp for audit trail
- Enables polling for unprocessed signals
- Supports retry logic and monitoring

### 5. Evidence Structure
- Nested STRUCT for blockchain citations
- Arrays support multiple blocks/transactions
- Enables verification and exploration
- Structured for efficient querying

## Requirements Mapping

This implementation satisfies the following requirements from the spec:

- **Requirement 1.3**: Signal persistence to BigQuery with all required fields
- **Requirement 4.2**: Insight evidence with block heights and transaction IDs
- **Requirement 9.1**: Known entities database with treasury company metadata

## Next Steps

After completing Task 1, proceed with:

1. **Task 2**: Implement Signal Persistence Module
   - Use Signal model for type safety
   - Write to intel.signals table
   - Implement batch insert logic

2. **Task 3**: Implement Data Extraction Module
   - Use EntityInfo model for entity identification
   - Query btc.known_entities table
   - Return typed data structures

3. **Task 4**: Implement Entity Identification Module
   - Load entities from btc.known_entities
   - Cache EntityInfo objects in memory
   - Support treasury company identification

## Files Created

```
infrastructure/bigquery/schemas/
├── intel_signals.sql
├── intel_insights.sql
├── btc_known_entities.sql
└── README.md

scripts/setup/
├── create-signal-tables.sh
└── create-signal-tables.bat

scripts/
└── populate_treasury_entities.py

shared/types/
├── signal_models.py
└── test_signal_models.py

docs/specs/signal-insight-pipeline/
└── task-1-implementation.md
```

## Validation Checklist

- [x] intel.signals table schema created with partitioning
- [x] intel.insights table schema created with partitioning
- [x] btc.known_entities table schema updated for treasury companies
- [x] Signal Pydantic model with validation
- [x] Insight Pydantic model with validation
- [x] Evidence Pydantic model with validation
- [x] EntityInfo Pydantic model with validation
- [x] Specialized metadata models for all signal types
- [x] Deployment scripts (shell and batch)
- [x] Entity population script with treasury data
- [x] Unit tests for all models
- [x] Documentation and usage examples
- [x] Requirements mapping verified

## Conclusion

Task 1 is complete. All BigQuery schemas and Python Pydantic models are implemented, tested, and documented. The foundation is ready for implementing the signal persistence and processing modules in subsequent tasks.
