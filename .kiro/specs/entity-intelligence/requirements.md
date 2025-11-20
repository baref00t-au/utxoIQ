# Requirements Document

## Introduction

The Entity Intelligence feature transforms utxoIQ from a transaction-level analytics platform into an entity-aware intelligence system. By attributing Bitcoin activity to real-world entities (exchanges, miners, whales, treasuries) and clustering related addresses, the system will provide deeper context for insights, alerts, and user queries. This feature enables users to understand not just what happened on-chain, but who was involved and why it matters.

## Glossary

- **Entity**: A real-world organization or individual that controls Bitcoin addresses (e.g., Binance, Foundry USA, Michael Saylor)
- **Cluster**: A group of Bitcoin addresses determined to be controlled by the same entity through heuristic analysis
- **Label**: An attribution that associates an address or cluster with a named entity and category
- **Confidence Score**: A numeric value (0.00-1.00) representing the certainty of an entity attribution
- **Heuristic**: A rule-based algorithm for inferring address ownership (e.g., common input ownership, change detection)
- **Entity Intelligence System**: The complete subsystem including labeling, clustering, scoring, APIs, and UI components
- **Label Source**: An external or internal data provider that supplies entity attributions (e.g., WalletExplorer, Arkham)
- **BigQuery**: Google Cloud's data warehouse storing blockchain data and entity intelligence tables
- **Entity Intelligence API**: FastAPI service providing entity resolution and statistics endpoints
- **Frontend**: Next.js application displaying entity information to users

## Requirements

### Requirement 1: Entity Label Registry

**User Story:** As a platform operator, I want to import and maintain entity labels from multiple sources, so that the system has comprehensive coverage of known Bitcoin entities.

#### Acceptance Criteria

1. WHEN a label source file is provided, THE Entity Intelligence System SHALL ingest the data into a versioned raw labels table within 5 minutes
2. THE Entity Intelligence System SHALL normalize address formats to checksummed strings with validation
3. THE Entity Intelligence System SHALL store label provenance including source name, source version, and ingestion timestamp
4. THE Entity Intelligence System SHALL support incremental updates without full reprocessing of historical labels
5. WHERE multiple sources provide conflicting labels for the same address, THE Entity Intelligence System SHALL retain all labels with source attribution

### Requirement 2: Address Clustering

**User Story:** As a blockchain analyst, I want addresses controlled by the same entity to be grouped together, so that I can track entity-level activity rather than individual addresses.

#### Acceptance Criteria

1. WHEN a Bitcoin transaction contains multiple inputs, THE Entity Intelligence System SHALL apply common input ownership heuristic to cluster those addresses
2. THE Entity Intelligence System SHALL detect change outputs using script type continuity and value patterns
3. THE Entity Intelligence System SHALL process new blocks incrementally and update clusters within 10 minutes of block arrival
4. THE Entity Intelligence System SHALL assign deterministic cluster identifiers that remain stable across updates
5. THE Entity Intelligence System SHALL store cluster membership with timestamps for audit trails

### Requirement 3: Label Confidence Scoring

**User Story:** As a user viewing entity information, I want to see confidence scores for entity attributions, so that I can assess the reliability of the information.

#### Acceptance Criteria

1. THE Entity Intelligence System SHALL compute confidence scores between 0.00 and 1.00 for every entity label
2. THE Entity Intelligence System SHALL incorporate source credibility, corroboration count, behavioral consistency, and recency into the confidence calculation
3. THE Entity Intelligence System SHALL provide human-readable reason codes explaining the confidence score
4. WHEN a label has not been observed in recent blockchain activity for 90 days, THE Entity Intelligence System SHALL apply recency decay to reduce confidence
5. THE Entity Intelligence System SHALL classify labels as verified (≥0.90), likely (0.70-0.89), or hint (0.50-0.69)

### Requirement 4: Entity Resolution API

**User Story:** As a developer integrating with utxoIQ, I want to resolve Bitcoin addresses to entities via API, so that I can build entity-aware applications.

#### Acceptance Criteria

1. THE Entity Intelligence API SHALL provide an endpoint that accepts a Bitcoin address and returns entity information within 300 milliseconds at p95
2. THE Entity Intelligence API SHALL return entity name, category, confidence score, reason codes, and cluster identifier
3. THE Entity Intelligence API SHALL support batch resolution of up to 1000 addresses in a single request
4. THE Entity Intelligence API SHALL implement Redis caching for frequently queried addresses
5. THE Entity Intelligence API SHALL enforce rate limits of 100 requests per minute for free tier users

### Requirement 5: Entity Statistics

**User Story:** As a trader, I want to see aggregate statistics for entities (inflows, outflows, balance), so that I can identify significant entity behaviors.

#### Acceptance Criteria

1. THE Entity Intelligence API SHALL provide entity statistics including total inflow, total outflow, net flow, and transaction count
2. THE Entity Intelligence API SHALL support time windows of 1 hour, 24 hours, 7 days, and 30 days
3. THE Entity Intelligence API SHALL compute statistics at the cluster level to capture all entity activity
4. THE Entity Intelligence API SHALL return top counterparty entities ranked by transaction value
5. THE Entity Intelligence API SHALL refresh statistics hourly for active entities

### Requirement 6: Entity UI Integration

**User Story:** As a utxoIQ user, I want to see entity badges on addresses and transactions in the interface, so that I can quickly identify who is involved in blockchain activity.

#### Acceptance Criteria

1. WHEN an address has an entity label with confidence ≥0.50, THE Frontend SHALL display an entity badge showing category and confidence
2. THE Frontend SHALL provide a tooltip explaining the confidence score and reason codes when hovering over entity badges
3. THE Frontend SHALL allow users to filter insights and alerts by entity category (exchanges, miners, whales, treasuries, mixers)
4. THE Frontend SHALL provide entity profile pages showing activity charts, statistics, and recent transactions
5. THE Frontend SHALL support CSV export of entity flow data for analysis

### Requirement 7: Entity Graph Visualization

**User Story:** As an analyst, I want to visualize entity relationships and fund flows, so that I can understand the network structure of Bitcoin activity.

#### Acceptance Criteria

1. THE Frontend SHALL render an interactive graph with entities as nodes and value flows as edges
2. THE Frontend SHALL weight edges by transaction value over the selected time window
3. THE Frontend SHALL support pan, zoom, and node search interactions
4. THE Frontend SHALL display entity details in a hover card when the user hovers over a node
5. THE Frontend SHALL allow filtering by minimum transaction value and entity category

### Requirement 8: Entity-Based Alerts

**User Story:** As a trader, I want to receive alerts when specific entities perform significant actions, so that I can react to market-moving events.

#### Acceptance Criteria

1. THE Entity Intelligence System SHALL support alert rules based on entity metrics (e.g., whale sends >100 BTC to exchange)
2. THE Entity Intelligence System SHALL evaluate alert conditions hourly against computed entity facts
3. THE Entity Intelligence System SHALL deliver alerts to the in-app feed within 5 minutes of condition trigger
4. THE Entity Intelligence System SHALL prevent duplicate alerts for the same condition within 24 hours
5. THE Entity Intelligence System SHALL allow users to subscribe to specific entity categories or individual entities

### Requirement 9: Machine Learning Classification

**User Story:** As a platform operator, I want unlabeled clusters to be automatically classified into categories, so that entity coverage expands beyond manually labeled addresses.

#### Acceptance Criteria

1. THE Entity Intelligence System SHALL extract structural, temporal, flow, UTXO, and fee features for each cluster
2. THE Entity Intelligence System SHALL train classification models weekly using high-confidence labeled entities as training data
3. THE Entity Intelligence System SHALL achieve ≥0.95 precision on exchange and miner categories in holdout evaluation
4. THE Entity Intelligence System SHALL assign predicted labels only when model confidence exceeds 0.70
5. THE Entity Intelligence System SHALL version models and store evaluation metrics in a model registry

### Requirement 10: Data Pipeline Orchestration

**User Story:** As a platform operator, I want entity intelligence data to be refreshed automatically on schedule, so that the system remains current without manual intervention.

#### Acceptance Criteria

1. THE Entity Intelligence System SHALL run hourly jobs for incremental clustering, label joins, feature aggregation, and alert evaluation
2. THE Entity Intelligence System SHALL run daily jobs for multi-day feature windows, graph edge computation, and confidence scoring refresh
3. THE Entity Intelligence System SHALL run weekly jobs for ML retraining, cluster compaction, and model promotion
4. THE Entity Intelligence System SHALL implement idempotency for all pipeline jobs to support safe retries
5. THE Entity Intelligence System SHALL publish pipeline metrics to Cloud Monitoring for observability

### Requirement 11: Cost Optimization

**User Story:** As a platform operator, I want BigQuery costs to remain predictable and controlled, so that the entity intelligence feature is economically sustainable.

#### Acceptance Criteria

1. THE Entity Intelligence System SHALL partition all tables by date to enable efficient time-range queries
2. THE Entity Intelligence System SHALL cluster tables by frequently filtered columns (script_type, category, entity_id)
3. THE Entity Intelligence System SHALL use materialized views for frequently accessed aggregate statistics
4. THE Entity Intelligence System SHALL validate query costs in CI pipelines before deployment
5. THE Entity Intelligence System SHALL process only incremental data in hourly and daily jobs

### Requirement 12: Security and Compliance

**User Story:** As a platform operator, I want entity intelligence data to be secured and auditable, so that the system meets security and compliance requirements.

#### Acceptance Criteria

1. THE Entity Intelligence System SHALL use read-only service accounts for accessing blockchain data
2. THE Entity Intelligence API SHALL validate API keys and enforce per-user rate limits
3. THE Entity Intelligence System SHALL log all label changes with timestamps and operator identifiers
4. THE Entity Intelligence System SHALL generate signed URLs for entity data exports with 1-hour expiration
5. THE Entity Intelligence System SHALL separate personally identifiable information into isolated projects if email alerts are implemented
