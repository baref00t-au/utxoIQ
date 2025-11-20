# Design Document

## Overview

The Entity Intelligence system adds entity-awareness to utxoIQ by attributing Bitcoin addresses to real-world entities through label ingestion, heuristic clustering, confidence scoring, and machine learning classification. The system consists of:

- **Data Layer**: BigQuery tables for labels, clusters, entities, and features
- **Processing Layer**: Python jobs for clustering, scoring, and ML training
- **API Layer**: FastAPI service for entity resolution and statistics
- **UI Layer**: Next.js components for entity badges, profiles, and graph visualization
- **Orchestration Layer**: Scheduled jobs for hourly, daily, and weekly updates

The design prioritizes incremental processing, cost efficiency, and extensibility while maintaining sub-300ms API latency.

## Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Sources                              │
│  WalletExplorer │ Arkham │ Bitrawr │ Bitcoin Core (via BQ)      │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Ingestion Layer (Cloud Functions)             │
│  Label Connectors │ Normalization │ Validation                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BigQuery Data Warehouse                       │
│  labels_raw_vX │ entities │ address_labels │ cluster_labels     │
│  clusters │ cluster_addresses │ ml_features_daily │ label_scores│
│  entity_edges_daily │ alerts_rules │ alerts_facts │ alerts_events│
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Processing Layer (Cloud Run Jobs)             │
│  Clustering Engine │ Confidence Scorer │ ML Trainer │ Graph Builder│
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Entity Intelligence API (Cloud Run)                 │
│  /v1/entity/resolve │ /v1/entity/{id}/stats │ /v1/graph         │
│  Redis Cache (Memorystore) │ Rate Limiting │ Auth               │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js on Cloud Run)               │
│  Entity Badges │ Entity Profiles │ Graph Viz │ Alert Config     │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Ingestion Layer**
- Fetch label data from external sources (WalletExplorer, Arkham, Bitrawr)
- Validate Bitcoin addresses with checksum verification
- Normalize entity names and categories
- Version control for label sources
- Write to `labels_raw_vX` tables

**Processing Layer**
- **Clustering Engine**: Apply heuristics to group addresses into clusters
- **Confidence Scorer**: Calculate confidence scores with reason codes
- **ML Trainer**: Train and evaluate classification models weekly
- **Graph Builder**: Compute entity-to-entity flow edges
- **Alert Evaluator**: Check alert conditions and trigger notifications

**API Layer**
- Resolve addresses/clusters to entities with caching
- Provide entity statistics with time windows
- Serve graph data for visualization
- Enforce authentication and rate limiting

**UI Layer**
- Display entity badges with confidence chips
- Render entity profile pages with charts
- Interactive graph visualization with WebGL
- Entity-based filtering and CSV export
- Alert subscription management

## Data Models

### BigQuery Schema

#### labels_raw_vX
Raw label imports with full provenance.

```sql
CREATE TABLE intel.labels_raw_v1 (
  source_name STRING NOT NULL,           -- e.g., 'walletexplorer', 'arkham'
  source_version STRING NOT NULL,        -- e.g., '2024-01-15'
  address STRING NOT NULL,               -- Bitcoin address (checksummed)
  entity_name STRING,                    -- e.g., 'Binance'
  category STRING,                       -- exchange, miner, whale, treasury, mixer
  evidence STRING,                       -- JSON with supporting data
  ingested_at TIMESTAMP NOT NULL,
  _partition_date DATE NOT NULL
)
PARTITION BY _partition_date
CLUSTER BY source_name, category;
```

#### entities
Master entity registry with metadata.

```sql
CREATE TABLE intel.entities (
  entity_id STRING NOT NULL,             -- UUID
  entity_name STRING NOT NULL,           -- Canonical name
  category STRING NOT NULL,              -- Primary category
  metadata_json STRING,                  -- Additional attributes
  first_seen TIMESTAMP NOT NULL,
  last_seen TIMESTAMP NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (entity_id) NOT ENFORCED
);
```

#### address_labels
Normalized labels at address level.

```sql
CREATE TABLE intel.address_labels (
  address STRING NOT NULL,
  entity_id STRING NOT NULL,
  label_source STRING NOT NULL,          -- Source that provided this label
  confidence FLOAT64 NOT NULL,           -- 0.00 to 1.00
  updated_at TIMESTAMP NOT NULL,
  _partition_date DATE NOT NULL
)
PARTITION BY _partition_date
CLUSTER BY address, entity_id;
```

#### clusters
Address clusters with summary features.

```sql
CREATE TABLE intel.clusters (
  cluster_id STRING NOT NULL,            -- Deterministic UUID
  size INT64 NOT NULL,                   -- Number of addresses
  first_seen_height INT64 NOT NULL,
  last_seen_height INT64 NOT NULL,
  script_mix_json STRING,                -- Distribution of script types
  summary_features_json STRING,          -- Aggregate features
  updated_at TIMESTAMP NOT NULL,
  PRIMARY KEY (cluster_id) NOT ENFORCED
);
```

#### cluster_addresses
Cluster membership mapping.

```sql
CREATE TABLE intel.cluster_addresses (
  cluster_id STRING NOT NULL,
  address STRING NOT NULL,
  added_at TIMESTAMP NOT NULL,
  _partition_date DATE NOT NULL
)
PARTITION BY _partition_date
CLUSTER BY cluster_id;
```

#### cluster_labels
Entity labels at cluster level.

```sql
CREATE TABLE intel.cluster_labels (
  cluster_id STRING NOT NULL,
  entity_id STRING NOT NULL,
  confidence FLOAT64 NOT NULL,
  method STRING NOT NULL,                -- 'heuristic', 'ml_model', 'propagated'
  updated_at TIMESTAMP NOT NULL,
  _partition_date DATE NOT NULL
)
PARTITION BY _partition_date
CLUSTER BY cluster_id, entity_id;
```

#### label_scores
Confidence scores with reason codes.

```sql
CREATE TABLE intel.label_scores (
  subject_id STRING NOT NULL,            -- address or cluster_id
  subject_type STRING NOT NULL,          -- 'address' or 'cluster'
  entity_id STRING NOT NULL,
  confidence FLOAT64 NOT NULL,
  reasons_json STRING NOT NULL,          -- Array of reason codes
  computed_at TIMESTAMP NOT NULL,
  _partition_date DATE NOT NULL
)
PARTITION BY _partition_date
CLUSTER BY subject_id, entity_id;
```

#### ml_features_daily
Machine learning features for classification.

```sql
CREATE TABLE intel.ml_features_daily (
  cluster_id STRING NOT NULL,
  feature_date DATE NOT NULL,
  -- Structural features
  avg_inputs FLOAT64,
  avg_outputs FLOAT64,
  script_type_mix_json STRING,
  address_reuse_rate FLOAT64,
  -- Temporal features
  tx_frequency_1d FLOAT64,
  tx_frequency_7d FLOAT64,
  tx_frequency_30d FLOAT64,
  diurnal_pattern_json STRING,
  burstiness_score FLOAT64,
  -- Flow features
  fanin_entropy FLOAT64,
  fanout_entropy FLOAT64,
  counterparty_diversity FLOAT64,
  self_churn_ratio FLOAT64,
  -- UTXO features
  utxo_age_distribution_json STRING,
  coin_days_destroyed_share FLOAT64,
  -- Fee features
  avg_fee_rate_satvb FLOAT64,
  fee_vs_mempool_baseline FLOAT64,
  _partition_date DATE NOT NULL
)
PARTITION BY _partition_date
CLUSTER BY cluster_id;
```

#### entity_edges_daily
Entity-to-entity flow graph.

```sql
CREATE TABLE intel.entity_edges_daily (
  edge_date DATE NOT NULL,
  src_entity_id STRING NOT NULL,
  dst_entity_id STRING NOT NULL,
  value_btc FLOAT64 NOT NULL,
  tx_count INT64 NOT NULL,
  _partition_date DATE NOT NULL
)
PARTITION BY _partition_date
CLUSTER BY src_entity_id, dst_entity_id;
```

#### alerts_rules
User-defined alert configurations.

```sql
CREATE TABLE intel.alerts_rules (
  rule_id STRING NOT NULL,
  user_id STRING NOT NULL,
  name STRING NOT NULL,
  params_json STRING NOT NULL,          -- Metric, threshold, entity filters
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL,
  PRIMARY KEY (rule_id) NOT ENFORCED
);
```

#### alerts_facts
Computed entity metrics for alert evaluation.

```sql
CREATE TABLE intel.alerts_facts (
  entity_id STRING NOT NULL,
  metric STRING NOT NULL,               -- 'inflow_24h', 'outflow_spike', etc.
  value FLOAT64 NOT NULL,
  window STRING NOT NULL,               -- '1h', '24h', '7d', '30d'
  computed_at TIMESTAMP NOT NULL,
  _partition_date DATE NOT NULL
)
PARTITION BY _partition_date
CLUSTER BY entity_id, metric;
```

#### alerts_events
Triggered alert notifications.

```sql
CREATE TABLE intel.alerts_events (
  alert_id STRING NOT NULL,
  rule_id STRING NOT NULL,
  entity_id STRING NOT NULL,
  payload_json STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  status STRING NOT NULL,               -- 'pending', 'delivered', 'failed'
  _partition_date DATE NOT NULL
)
PARTITION BY _partition_date
CLUSTER BY rule_id, status;
```

### API Response Models

#### EntityResolveResponse

```python
from pydantic import BaseModel
from typing import List, Optional

class EntityResolveResponse(BaseModel):
    entity_id: str
    entity_name: str
    category: str                        # exchange, miner, whale, treasury, mixer
    confidence: float                    # 0.00 to 1.00
    reasons: List[str]                   # Reason codes
    cluster_id: Optional[str]
    metadata: Optional[dict]
```

#### EntityStatsResponse

```python
class EntityStatsResponse(BaseModel):
    entity_id: str
    window: str                          # '1h', '24h', '7d', '30d'
    inflow_btc: float
    outflow_btc: float
    net_flow_btc: float
    tx_count: int
    counterparties_top: List[dict]       # [{entity_id, entity_name, value_btc}]
    computed_at: str                     # ISO timestamp
```

#### GraphResponse

```python
class GraphNode(BaseModel):
    entity_id: str
    entity_name: str
    category: str
    total_value_btc: float

class GraphEdge(BaseModel):
    src_entity_id: str
    dst_entity_id: str
    value_btc: float
    tx_count: int

class GraphResponse(BaseModel):
    window: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    computed_at: str
```

## Components and Interfaces

### 1. Label Ingestion Service

**Technology**: Python Cloud Functions triggered by Cloud Scheduler

**Responsibilities**:
- Fetch label data from external sources (HTTP APIs, CSV downloads)
- Validate Bitcoin addresses using `bitcoin-utils` library
- Normalize entity names (trim, lowercase, deduplicate)
- Write to `labels_raw_vX` with source provenance
- Emit metrics for ingestion success/failure

**Key Functions**:
```python
def fetch_walletexplorer_labels() -> List[RawLabel]:
    """Download and parse WalletExplorer export"""
    
def fetch_arkham_labels() -> List[RawLabel]:
    """Fetch Arkham Intelligence open dataset"""
    
def validate_address(address: str) -> bool:
    """Validate Bitcoin address checksum"""
    
def normalize_entity_name(name: str) -> str:
    """Standardize entity naming"""
    
def ingest_labels(labels: List[RawLabel], source: str, version: str):
    """Write labels to BigQuery with versioning"""
```

**Schedule**: Daily at 02:00 UTC

### 2. Clustering Engine

**Technology**: Python Cloud Run Job with BigQuery SQL UDFs

**Responsibilities**:
- Apply common input ownership heuristic
- Detect change outputs with script type and value analysis
- Merge clusters based on behavioral patterns
- Assign deterministic cluster IDs
- Update `clusters` and `cluster_addresses` tables incrementally

**Heuristic Algorithms**:

**Common Input Ownership**:
```sql
-- BigQuery UDF
CREATE TEMP FUNCTION common_input_clustering(tx_inputs ARRAY<STRING>)
RETURNS ARRAY<STRUCT<addr1 STRING, addr2 STRING>>
AS (
  -- Generate pairs of addresses from same transaction
  -- Exclude coinbase and known exceptions (mixing services)
  ARRAY(
    SELECT AS STRUCT i1 AS addr1, i2 AS addr2
    FROM UNNEST(tx_inputs) AS i1
    CROSS JOIN UNNEST(tx_inputs) AS i2
    WHERE i1 < i2
      AND i1 NOT IN (SELECT address FROM intel.mixer_exclusions)
  )
);
```

**Change Detection**:
```python
def detect_change_output(tx: Transaction) -> Optional[str]:
    """
    Identify change output using:
    - Script type matches input majority
    - Value is smaller than largest input
    - Address is novel (not seen before this tx)
    - Round number heuristic (change is non-round)
    """
    input_script_types = [inp.script_type for inp in tx.inputs]
    majority_script = max(set(input_script_types), key=input_script_types.count)
    
    for output in tx.outputs:
        if (output.script_type == majority_script and
            output.value < max(inp.value for inp in tx.inputs) and
            is_novel_address(output.address, tx.txid) and
            not is_round_number(output.value)):
            return output.address
    return None
```

**Cluster Merging**:
```python
def merge_clusters(cluster_graph: nx.Graph) -> Dict[str, str]:
    """
    Use Union-Find to merge connected components.
    Assign deterministic cluster_id = SHA256(sorted_addresses)[:16]
    """
    components = nx.connected_components(cluster_graph)
    cluster_mapping = {}
    
    for component in components:
        sorted_addrs = sorted(component)
        cluster_id = hashlib.sha256(''.join(sorted_addrs).encode()).hexdigest()[:16]
        for addr in component:
            cluster_mapping[addr] = cluster_id
    
    return cluster_mapping
```

**Schedule**: Hourly for new blocks, weekly for full compaction

### 3. Confidence Scoring Engine

**Technology**: Python Cloud Run Job

**Responsibilities**:
- Calculate confidence scores using weighted formula
- Generate reason codes for transparency
- Apply recency decay for stale labels
- Write to `label_scores` table
- Classify labels into verified/likely/hint tiers

**Scoring Formula**:
```python
def calculate_confidence(
    source_weight: float,
    match_strength: float,
    behavioral_consistency: float,
    recency_decay: float
) -> float:
    """
    confidence = w1*source_weight + w2*match_strength + 
                 w3*behavioral_consistency + w4*recency_decay
    
    Weights: w1=0.35, w2=0.25, w3=0.25, w4=0.15
    """
    return (0.35 * source_weight +
            0.25 * match_strength +
            0.25 * behavioral_consistency +
            0.15 * recency_decay)
```

**Reason Codes**:
```python
class ReasonCode(Enum):
    SRC_MATCH = "Matched by trusted label source"
    COSPEND = "Co-spent with known entity addresses"
    CHANGE_HEURISTIC = "Identified as change output"
    PATTERN_FANIN = "Transaction pattern matches entity type"
    RECENT_ACTIVITY = "Recent on-chain activity observed"
    MULTI_SOURCE = "Confirmed by multiple sources"
    ML_PREDICTION = "Machine learning classification"
```

**Recency Decay**:
```python
def recency_decay_factor(days_since_last_seen: int) -> float:
    """
    Exponential decay: e^(-days/90)
    Full confidence if seen in last 30 days
    50% confidence at 90 days
    Near-zero at 180+ days
    """
    if days_since_last_seen <= 30:
        return 1.0
    return math.exp(-days_since_last_seen / 90.0)
```

**Schedule**: Daily at 04:00 UTC

### 4. Entity Intelligence API

**Technology**: FastAPI on Cloud Run with Redis (Memorystore)

**Endpoints**:

```python
from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional

app = FastAPI(title="Entity Intelligence API", version="1.0")

@app.get("/v1/entity/resolve")
async def resolve_entity(
    address: str = Query(..., description="Bitcoin address"),
    include_cluster: bool = Query(True)
) -> EntityResolveResponse:
    """
    Resolve address to entity with confidence and reasons.
    Cache hot addresses in Redis with 1-hour TTL.
    """
    # Check Redis cache
    cached = await redis.get(f"resolve:{address}")
    if cached:
        return EntityResolveResponse.parse_raw(cached)
    
    # Query BigQuery
    result = await query_entity_resolution(address)
    
    # Cache result
    await redis.setex(f"resolve:{address}", 3600, result.json())
    
    return result

@app.post("/v1/entity/resolve/batch")
async def resolve_entities_batch(
    addresses: List[str]
) -> List[EntityResolveResponse]:
    """
    Batch resolve up to 1000 addresses.
    Use BigQuery array operations for efficiency.
    """
    if len(addresses) > 1000:
        raise HTTPException(400, "Maximum 1000 addresses per batch")
    
    return await query_entity_resolution_batch(addresses)
```

```python
@app.get("/v1/entity/{entity_id}/stats")
async def get_entity_stats(
    entity_id: str,
    window: str = Query("24h", regex="^(1h|24h|7d|30d)$")
) -> EntityStatsResponse:
    """
    Get entity statistics for specified time window.
    Use materialized views for common windows.
    """
    # Check if materialized view exists for this window
    if window in ["24h", "7d"]:
        return await query_entity_stats_mv(entity_id, window)
    else:
        return await query_entity_stats_computed(entity_id, window)

@app.get("/v1/cluster/{cluster_id}")
async def get_cluster_info(cluster_id: str) -> ClusterResponse:
    """
    Get cluster details including addresses and features.
    """
    return await query_cluster_details(cluster_id)

@app.get("/v1/graph")
async def get_entity_graph(
    window: str = Query("7d", regex="^(1h|24h|7d|30d)$"),
    min_btc: float = Query(50.0, ge=0),
    categories: Optional[List[str]] = Query(None)
) -> GraphResponse:
    """
    Get entity flow graph for visualization.
    Precomputed daily, filtered by parameters.
    """
    return await query_entity_graph(window, min_btc, categories)

@app.get("/v1/search")
async def search_entities(
    query: str = Query(..., min_length=2),
    type: str = Query("entity", regex="^(entity|cluster)$"),
    limit: int = Query(20, le=100)
) -> List[EntitySearchResult]:
    """
    Search entities by name with fuzzy matching.
    """
    return await search_entities_by_name(query, type, limit)
```

**Authentication & Rate Limiting**:
```python
from fastapi import Depends, Header
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

async def verify_api_key(x_api_key: str = Header(...)):
    """Validate API key and return user tier"""
    user = await get_user_by_api_key(x_api_key)
    if not user:
        raise HTTPException(401, "Invalid API key")
    return user

@app.get("/v1/entity/resolve")
@limiter.limit("100/minute")  # Free tier
async def resolve_entity(
    address: str,
    user = Depends(verify_api_key)
):
    # Apply tier-specific rate limits
    if user.tier == "free" and await check_rate_limit(user.id, "100/minute"):
        raise HTTPException(429, "Rate limit exceeded")
    # ... rest of implementation
```

**Caching Strategy**:
- Redis cache for hot entity resolutions (1-hour TTL)
- BigQuery materialized views for 24h/7d stats (refreshed hourly)
- CDN caching for graph API responses (15-minute TTL)

### 5. ML Classification Pipeline

**Technology**: Python Cloud Run Job with BigQuery ML

**Responsibilities**:
- Extract features from clusters
- Train classification models weekly
- Evaluate on holdout set
- Predict categories for unlabeled clusters
- Version models in registry

**Feature Extraction**:
```python
def extract_cluster_features(cluster_id: str, window_days: int) -> dict:
    """
    Extract features for ML classification.
    Returns dict with structural, temporal, flow, UTXO, and fee features.
    """
    query = f"""
    SELECT
      -- Structural
      AVG(input_count) as avg_inputs,
      AVG(output_count) as avg_outputs,
      COUNT(DISTINCT script_type) / COUNT(*) as script_diversity,
      SUM(CASE WHEN address_reused THEN 1 ELSE 0 END) / COUNT(*) as reuse_rate,
      
      -- Temporal
      COUNT(*) / {window_days} as tx_per_day,
      STDDEV(TIMESTAMP_DIFF(tx_time, LAG(tx_time) OVER (ORDER BY tx_time), SECOND)) as burstiness,
      
      -- Flow
      APPROX_QUANTILES(fanin_count, 100)[OFFSET(50)] as median_fanin,
      APPROX_QUANTILES(fanout_count, 100)[OFFSET(50)] as median_fanout,
      COUNT(DISTINCT counterparty_cluster) / COUNT(*) as counterparty_diversity,
      
      -- UTXO
      AVG(utxo_age_days) as avg_utxo_age,
      SUM(coin_days_destroyed) / SUM(value_btc) as cdd_ratio,
      
      -- Fees
      AVG(fee_rate_satvb) as avg_fee_rate,
      AVG(fee_rate_satvb) / AVG(mempool_median_fee) as fee_vs_baseline
      
    FROM btc.transactions t
    JOIN intel.cluster_addresses ca ON t.address = ca.address
    WHERE ca.cluster_id = @cluster_id
      AND t.block_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {window_days} DAY)
    """
    return execute_query(query, {"cluster_id": cluster_id})
```

**Model Training**:
```python
def train_classification_model():
    """
    Train BigQuery ML logistic regression model.
    Use high-confidence labeled clusters as training data.
    """
    training_query = """
    CREATE OR REPLACE MODEL intel.entity_classifier_v{version}
    OPTIONS(
      model_type='LOGISTIC_REG',
      input_label_cols=['category'],
      auto_class_weights=TRUE
    ) AS
    SELECT
      f.*,
      cl.category
    FROM intel.ml_features_daily f
    JOIN intel.cluster_labels cl ON f.cluster_id = cl.cluster_id
    WHERE cl.confidence >= 0.90
      AND f.feature_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    """
    execute_query(training_query.format(version=get_next_version()))
```

**Model Evaluation**:
```python
def evaluate_model(model_name: str) -> dict:
    """
    Evaluate model on holdout set.
    Return precision, recall, F1 per category.
    """
    eval_query = f"""
    SELECT
      category,
      precision,
      recall,
      f1_score,
      accuracy
    FROM ML.EVALUATE(MODEL intel.{model_name},
      (SELECT f.*, cl.category
       FROM intel.ml_features_daily f
       JOIN intel.cluster_labels cl ON f.cluster_id = cl.cluster_id
       WHERE cl.confidence >= 0.90
         AND MOD(ABS(FARM_FINGERPRINT(f.cluster_id)), 10) = 0))  -- 10% holdout
    """
    return execute_query(eval_query)
```

**Model Promotion**:
```python
def promote_model_if_better(new_model: str, current_model: str):
    """
    Compare new model to current production model.
    Promote if precision >= 0.95 on exchange/miner categories.
    """
    new_metrics = evaluate_model(new_model)
    current_metrics = evaluate_model(current_model)
    
    # Check critical categories
    for category in ["exchange", "miner"]:
        new_precision = new_metrics[category]["precision"]
        current_precision = current_metrics[category]["precision"]
        
        if new_precision < 0.95 or new_precision < current_precision:
            logger.warning(f"New model underperforms on {category}")
            return False
    
    # Promote model
    execute_query(f"ALTER MODEL intel.entity_classifier SET OPTIONS(version='{new_model}')")
    logger.info(f"Promoted {new_model} to production")
    return True
```

**Schedule**: Weekly on Sunday at 03:00 UTC

### 6. Graph Builder

**Technology**: Python Cloud Run Job

**Responsibilities**:
- Compute entity-to-entity flows from transaction data
- Aggregate by day and time window
- Write to `entity_edges_daily` table
- Precompute graph slices for API

**Implementation**:
```python
def build_entity_graph(date: datetime.date):
    """
    Build entity flow graph for specified date.
    Join transactions with cluster labels to attribute flows.
    """
    query = """
    INSERT INTO intel.entity_edges_daily
    SELECT
      @date as edge_date,
      src_cl.entity_id as src_entity_id,
      dst_cl.entity_id as dst_entity_id,
      SUM(t.value_btc) as value_btc,
      COUNT(*) as tx_count,
      @date as _partition_date
    FROM btc.transactions t
    JOIN intel.cluster_addresses src_ca ON t.input_address = src_ca.address
    JOIN intel.cluster_labels src_cl ON src_ca.cluster_id = src_cl.cluster_id
    JOIN intel.cluster_addresses dst_ca ON t.output_address = dst_ca.address
    JOIN intel.cluster_labels dst_cl ON dst_ca.cluster_id = dst_cl.cluster_id
    WHERE DATE(t.block_time) = @date
      AND src_cl.confidence >= 0.70
      AND dst_cl.confidence >= 0.70
      AND src_cl.entity_id != dst_cl.entity_id  -- Exclude self-loops
    GROUP BY src_entity_id, dst_entity_id
    HAVING value_btc >= 0.1  -- Minimum threshold
    """
    execute_query(query, {"date": date})
```

**Schedule**: Daily at 05:00 UTC for previous day

### 7. Alert Engine

**Technology**: Python Cloud Run Job

**Responsibilities**:
- Build alert facts from entity statistics
- Evaluate alert rules against facts
- Trigger notifications for matched conditions
- Prevent duplicate alerts with deduplication window

**Fact Builder**:
```python
def build_alert_facts():
    """
    Compute entity metrics for alert evaluation.
    Run hourly to keep facts fresh.
    """
    metrics = [
        ("inflow_1h", "1 HOUR"),
        ("inflow_24h", "24 HOUR"),
        ("outflow_1h", "1 HOUR"),
        ("outflow_24h", "24 HOUR"),
        ("net_flow_24h", "24 HOUR"),
        ("outflow_spike_vs_30d", "30 DAY")
    ]
    
    for metric_name, window in metrics:
        query = f"""
        INSERT INTO intel.alerts_facts
        SELECT
          entity_id,
          '{metric_name}' as metric,
          {compute_metric_sql(metric_name)} as value,
          '{window}' as window,
          CURRENT_TIMESTAMP() as computed_at,
          CURRENT_DATE() as _partition_date
        FROM intel.entity_stats_mv
        WHERE last_updated >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {window})
        """
        execute_query(query)
```

**Alert Evaluator**:
```python
def evaluate_alerts():
    """
    Check alert rules against computed facts.
    Trigger notifications for matched conditions.
    """
    # Get active rules
    rules = get_active_alert_rules()
    
    for rule in rules:
        # Parse rule parameters
        params = json.loads(rule.params_json)
        metric = params["metric"]
        threshold = params["threshold"]
        entity_filter = params.get("entity_filter", {})
        
        # Query matching facts
        query = """
        SELECT f.entity_id, f.value, e.entity_name, e.category
        FROM intel.alerts_facts f
        JOIN intel.entities e ON f.entity_id = e.entity_id
        WHERE f.metric = @metric
          AND f.value >= @threshold
          AND f.computed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
          AND (@category IS NULL OR e.category = @category)
        """
        
        matches = execute_query(query, {
            "metric": metric,
            "threshold": threshold,
            "category": entity_filter.get("category")
        })
        
        # Trigger alerts with deduplication
        for match in matches:
            if not alert_triggered_recently(rule.rule_id, match.entity_id, hours=24):
                trigger_alert(rule, match)
```

**Alert Delivery**:
```python
def trigger_alert(rule: AlertRule, match: dict):
    """
    Create alert event and deliver notification.
    """
    alert_id = generate_uuid()
    payload = {
        "entity_id": match.entity_id,
        "entity_name": match.entity_name,
        "category": match.category,
        "metric": rule.params_json["metric"],
        "value": match.value,
        "threshold": rule.params_json["threshold"]
    }
    
    # Insert alert event
    insert_alert_event(alert_id, rule.rule_id, match.entity_id, payload)
    
    # Deliver via configured channels
    if "in_app" in rule.channels:
        publish_to_user_feed(rule.user_id, alert_id, payload)
    
    if "email" in rule.channels:
        send_email_notification(rule.user_id, payload)
    
    if "webhook" in rule.channels:
        post_webhook(rule.webhook_url, payload)
```

**Schedule**: Hourly at :15 past the hour

### 8. Frontend Components

**Technology**: Next.js 16, TypeScript, shadcn/ui, TanStack Query, Recharts/D3

#### Entity Badge Component

```typescript
// components/entity/EntityBadge.tsx
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

interface EntityBadgeProps {
  entityName: string;
  category: 'exchange' | 'miner' | 'whale' | 'treasury' | 'mixer';
  confidence: number;
  reasons: string[];
}

export function EntityBadge({ entityName, category, confidence, reasons }: EntityBadgeProps) {
  const categoryColors = {
    exchange: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    miner: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    whale: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
    treasury: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    mixer: 'bg-red-500/10 text-red-400 border-red-500/20'
  };
  
  const confidenceColor = confidence >= 0.9 ? 'text-emerald-400' : 
                          confidence >= 0.7 ? 'text-amber-400' : 
                          'text-zinc-400';
  
  return (
    <Tooltip>
      <TooltipTrigger>
        <Badge className={categoryColors[category]}>
          <span className="w-2 h-2 rounded-full bg-current mr-2" />
          {entityName} • <span className={confidenceColor}>{confidence.toFixed(2)}</span>
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        <div className="space-y-1">
          <p className="font-medium">Confidence: {(confidence * 100).toFixed(0)}%</p>
          <p className="text-sm text-zinc-400">Reasons:</p>
          <ul className="text-sm space-y-0.5">
            {reasons.map((reason, i) => (
              <li key={i}>• {reason}</li>
            ))}
          </ul>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
```

#### Entity Profile Page

```typescript
// app/entity/[id]/page.tsx
import { EntityStats } from '@/components/entity/EntityStats';
import { EntityActivityChart } from '@/components/entity/EntityActivityChart';
import { EntityCounterparties } from '@/components/entity/EntityCounterparties';
import { useQuery } from '@tanstack/react-query';

export default function EntityProfilePage({ params }: { params: { id: string } }) {
  const { data: entity } = useQuery({
    queryKey: ['entity', params.id],
    queryFn: () => fetch(`/api/v1/entity/${params.id}`).then(r => r.json())
  });
  
  const { data: stats } = useQuery({
    queryKey: ['entity-stats', params.id, '7d'],
    queryFn: () => fetch(`/api/v1/entity/${params.id}/stats?window=7d`).then(r => r.json())
  });
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">{entity?.entity_name}</h1>
          <p className="text-zinc-400 capitalize">{entity?.category}</p>
        </div>
        <EntityBadge {...entity} />
      </div>
      
      <EntityStats stats={stats} />
      <EntityActivityChart entityId={params.id} window="7d" />
      <EntityCounterparties entityId={params.id} />
    </div>
  );
}
```

#### Entity Graph Visualization

```typescript
// components/entity/EntityGraph.tsx
import { useQuery } from '@tanstack/react-query';
import { ForceGraph2D } from 'react-force-graph';
import { useState } from 'react';

interface EntityGraphProps {
  window: '1h' | '24h' | '7d' | '30d';
  minBtc: number;
  categories?: string[];
}

export function EntityGraph({ window, minBtc, categories }: EntityGraphProps) {
  const [hoveredNode, setHoveredNode] = useState(null);
  
  const { data: graphData } = useQuery({
    queryKey: ['entity-graph', window, minBtc, categories],
    queryFn: async () => {
      const params = new URLSearchParams({
        window,
        min_btc: minBtc.toString(),
        ...(categories && { categories: categories.join(',') })
      });
      return fetch(`/api/v1/graph?${params}`).then(r => r.json());
    }
  });
  
  const nodes = graphData?.nodes.map(n => ({
    id: n.entity_id,
    name: n.entity_name,
    category: n.category,
    value: n.total_value_btc
  })) || [];
  
  const links = graphData?.edges.map(e => ({
    source: e.src_entity_id,
    target: e.dst_entity_id,
    value: e.value_btc
  })) || [];
  
  return (
    <div className="relative w-full h-[600px] bg-zinc-900 rounded-2xl border border-zinc-800">
      <ForceGraph2D
        graphData={{ nodes, links }}
        nodeLabel="name"
        nodeColor={node => getCategoryColor(node.category)}
        nodeVal={node => Math.sqrt(node.value)}
        linkWidth={link => Math.sqrt(link.value) / 10}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={2}
        onNodeHover={setHoveredNode}
        backgroundColor="#131316"
      />
      
      {hoveredNode && (
        <div className="absolute top-4 left-4 bg-zinc-800 p-4 rounded-lg border border-zinc-700">
          <p className="font-medium">{hoveredNode.name}</p>
          <p className="text-sm text-zinc-400 capitalize">{hoveredNode.category}</p>
          <p className="text-sm mt-2">{hoveredNode.value.toFixed(2)} BTC</p>
        </div>
      )}
    </div>
  );
}
```

#### Entity Filter Component

```typescript
// components/entity/EntityFilter.tsx
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface EntityFilterProps {
  selectedCategories: string[];
  onCategoriesChange: (categories: string[]) => void;
  highConfidenceOnly: boolean;
  onHighConfidenceChange: (value: boolean) => void;
}

export function EntityFilter({
  selectedCategories,
  onCategoriesChange,
  highConfidenceOnly,
  onHighConfidenceChange
}: EntityFilterProps) {
  const categories = ['all', 'exchange', 'miner', 'whale', 'treasury', 'mixer'];
  
  return (
    <div className="space-y-4 p-4 bg-zinc-900 rounded-lg border border-zinc-800">
      <div>
        <Label className="text-sm text-zinc-400 mb-2">Category</Label>
        <Tabs value={selectedCategories[0] || 'all'} onValueChange={(v) => onCategoriesChange([v])}>
          <TabsList className="grid grid-cols-6 w-full">
            {categories.map(cat => (
              <TabsTrigger key={cat} value={cat} className="capitalize">
                {cat}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>
      
      <div className="flex items-center justify-between">
        <Label htmlFor="high-confidence" className="text-sm">
          High confidence only (≥0.70)
        </Label>
        <Switch
          id="high-confidence"
          checked={highConfidenceOnly}
          onCheckedChange={onHighConfidenceChange}
        />
      </div>
    </div>
  );
}
```

## Error Handling

### API Error Responses

All API errors follow consistent format:

```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict]
    request_id: str
```

**Common Error Codes**:
- 400: Invalid address format, invalid parameters
- 401: Missing or invalid API key
- 404: Entity not found, cluster not found
- 429: Rate limit exceeded
- 500: Internal server error
- 503: Service temporarily unavailable

### Retry Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def query_bigquery_with_retry(query: str):
    """Retry BigQuery queries with exponential backoff"""
    return await bigquery_client.query(query).result()
```

### Fallback Mechanisms

**Label Source Failures**:
- Continue with available sources if one fails
- Log failures to Cloud Monitoring
- Alert operators if all sources fail

**ML Model Failures**:
- Fall back to heuristic-only classification
- Use previous model version if new model fails validation
- Manual override capability for critical entities

**API Degradation**:
- Serve stale cached data if BigQuery is slow
- Return partial results with warning flag
- Circuit breaker pattern for external dependencies

## Testing Strategy

### Unit Tests

**Coverage Requirements**: ≥80% for all Python modules

**Key Test Areas**:
- Address validation and normalization
- Clustering heuristics with known test cases
- Confidence scoring formula with edge cases
- API request/response serialization
- Feature extraction correctness

**Example Test**:
```python
def test_common_input_clustering():
    """Test that addresses in same transaction are clustered"""
    tx = Transaction(
        txid="abc123",
        inputs=[
            Input(address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"),
            Input(address="1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2")
        ],
        outputs=[Output(address="1HQ3Go3ggs8pFnXuHVHRytPCq5fGG8Hbhx", value=50.0)]
    )
    
    clusters = apply_common_input_heuristic(tx)
    assert len(clusters) == 1
    assert "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" in clusters[0]
    assert "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2" in clusters[0]
```

### Integration Tests

**Test Scenarios**:
- End-to-end label ingestion to API resolution
- Clustering pipeline with real blockchain data
- ML training and prediction workflow
- Alert rule evaluation and delivery
- Graph computation and API serving

**Example Test**:
```python
@pytest.mark.integration
async def test_entity_resolution_flow():
    """Test complete flow from label ingestion to API resolution"""
    # Ingest test label
    await ingest_labels([
        RawLabel(
            source_name="test",
            address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            entity_name="Satoshi",
            category="whale"
        )
    ])
    
    # Run clustering
    await run_clustering_job()
    
    # Run confidence scoring
    await run_confidence_scoring()
    
    # Query API
    response = await api_client.get("/v1/entity/resolve?address=1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    assert response.status_code == 200
    assert response.json()["entity_name"] == "Satoshi"
    assert response.json()["category"] == "whale"
    assert response.json()["confidence"] >= 0.5
```

### Performance Tests

**Acceptance Criteria**:
- Entity resolution API: p95 < 300ms
- Batch resolution (1000 addresses): p95 < 2s
- Graph API: p95 < 1s
- Clustering job: process 10k new addresses in < 5 minutes

**Load Testing**:
```python
from locust import HttpUser, task, between

class EntityAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def resolve_entity(self):
        address = random.choice(self.test_addresses)
        self.client.get(f"/v1/entity/resolve?address={address}")
    
    @task(1)
    def get_entity_stats(self):
        entity_id = random.choice(self.test_entities)
        self.client.get(f"/v1/entity/{entity_id}/stats?window=24h")
```

### E2E Tests

**User Workflows**:
- View entity badge on insight page
- Click entity badge to open profile
- Filter insights by entity category
- Create entity-based alert
- View entity graph visualization
- Export entity flow data

**Playwright Test**:
```typescript
test('entity badge displays and opens profile', async ({ page }) => {
  await page.goto('/insights');
  
  // Find entity badge
  const badge = page.locator('[data-testid="entity-badge"]').first();
  await expect(badge).toBeVisible();
  
  // Hover to see tooltip
  await badge.hover();
  await expect(page.locator('[role="tooltip"]')).toContainText('Confidence');
  
  // Click to open profile
  await badge.click();
  await expect(page).toHaveURL(/\/entity\/[a-f0-9-]+/);
  await expect(page.locator('h1')).toContainText('Binance');
});
```

## Deployment Strategy

### Phase 1: Foundation (Weeks 1-2)
- Deploy label ingestion connectors
- Create BigQuery schema
- Deploy basic API with resolve endpoint
- Add entity badges to UI (placeholder data)

### Phase 2: Clustering (Weeks 3-4)
- Deploy clustering engine
- Deploy confidence scoring
- Update API to use clusters
- Show confidence in UI

### Phase 3: Intelligence (Weeks 5-6)
- Deploy entity stats endpoints
- Deploy ML training pipeline
- Add entity profiles to UI
- Deploy graph builder

### Phase 4: Alerts & Graph (Weeks 7-8)
- Deploy alert engine
- Add alert UI
- Deploy graph visualization
- Add entity filters

### Phase 5: Hardening (Weeks 9-10)
- Performance optimization
- Cost optimization
- Comprehensive testing
- Documentation
- Beta release

### Rollout Strategy

**Feature Flags**:
```python
FEATURE_FLAGS = {
    "entity_badges": True,           # Show entity badges
    "entity_profiles": True,         # Enable profile pages
    "entity_graph": False,           # Graph viz (beta)
    "entity_alerts": False,          # Entity-based alerts (beta)
    "ml_classification": False       # ML predictions (alpha)
}
```

**Gradual Rollout**:
1. Internal testing (week 9)
2. Beta users (10% traffic, week 10)
3. General availability (100% traffic, week 11)

### Monitoring & Observability

**Key Metrics**:
- API latency (p50, p95, p99)
- Cache hit rate
- BigQuery query costs
- Label coverage percentage
- Clustering accuracy
- ML model precision/recall
- Alert delivery success rate

**Dashboards**:
- Entity Intelligence Overview
- API Performance
- Data Pipeline Health
- ML Model Performance
- Cost Tracking

**Alerts**:
- API latency > 500ms p95
- Cache hit rate < 70%
- BigQuery costs > $100/day
- Label ingestion failures
- ML model precision < 0.95
- Alert delivery failures > 5%

This completes the design document for the Entity Intelligence system.
