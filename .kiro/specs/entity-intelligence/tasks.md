# Implementation Plan

- [ ] 1. Entity Labeling MVP
  - Create BigQuery schema for label tables and entity registry
  - Implement label ingestion connectors for external sources
  - Build normalization and validation pipeline
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 1.1 Create BigQuery schema and tables
  - Write SQL DDL for `labels_raw_v1`, `entities`, `address_labels`, `label_versions` tables
  - Configure partitioning by date and clustering by source_name, category
  - Add table descriptions and column comments for documentation
  - _Requirements: 1.1, 1.3_

- [ ] 1.2 Implement WalletExplorer connector
  - Write Cloud Function to fetch WalletExplorer CSV exports
  - Parse CSV and validate Bitcoin addresses with checksum verification
  - Transform to `RawLabel` schema with source provenance
  - Handle incremental updates and version tracking
  - _Requirements: 1.1, 1.2_

- [ ] 1.3 Implement Arkham Intelligence connector
  - Write Cloud Function to fetch Arkham open dataset via API
  - Parse JSON response and extract entity labels
  - Normalize entity names and categories to standard taxonomy
  - Store with source attribution and ingestion timestamp
  - _Requirements: 1.1, 1.2_

- [ ] 1.4 Implement Bitrawr connector
  - Write Cloud Function to fetch Bitrawr label lists
  - Parse format and validate addresses
  - Deduplicate labels within source
  - Write to `labels_raw_v1` with versioning
  - _Requirements: 1.1, 1.2_

- [ ] 1.5 Build label normalization pipeline
  - Create Cloud Run Job to process `labels_raw_vX` into `address_labels`
  - Implement address checksum validation and normalization
  - Deduplicate across sources while preserving provenance
  - Generate or update entity records in `entities` table
  - Implement SCD-2 pattern for tracking label history
  - _Requirements: 1.3, 1.4, 1.5_

- [ ] 1.6 Write unit tests for label ingestion

  - Test address validation with valid and invalid addresses
  - Test entity name normalization edge cases
  - Test deduplication logic across sources
  - Test version tracking and incremental updates
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Heuristic Clustering Engine
  - Implement clustering algorithms for address grouping
  - Build incremental update pipeline for new blocks
  - Create cluster management and compaction jobs
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 2.1 Create clustering schema in BigQuery
  - Write SQL DDL for `clusters`, `cluster_addresses`, `cluster_events` tables
  - Configure appropriate partitioning and clustering
  - Add indexes for efficient cluster lookups
  - _Requirements: 2.4_

- [ ] 2.2 Implement common input ownership heuristic
  - Write BigQuery UDF to identify co-spent addresses in transactions
  - Add exclusion list for known mixing services
  - Handle coinbase transactions separately
  - Generate address pairs for clustering
  - _Requirements: 2.1_

- [ ] 2.3 Implement change detection heuristic
  - Write Python function to analyze transaction outputs
  - Detect change using script type continuity
  - Apply value pattern analysis (non-round amounts)
  - Check for novel addresses (first appearance)
  - Return most likely change output per transaction
  - _Requirements: 2.2_

- [ ] 2.4 Build cluster merge algorithm
  - Implement Union-Find data structure for connected components
  - Generate deterministic cluster IDs using SHA256 of sorted addresses
  - Handle cluster splits and merges with stable ID assignment
  - Write cluster membership to `cluster_addresses` table
  - _Requirements: 2.4, 2.5_

- [ ] 2.5 Create incremental clustering job
  - Write Cloud Run Job to process new blocks hourly
  - Query new transactions from `btc.transactions` since last run
  - Apply heuristics and update cluster graph
  - Merge new addresses into existing clusters or create new ones
  - Update `clusters` table with size and feature summaries
  - _Requirements: 2.3, 2.4, 2.5_

- [ ] 2.6 Implement weekly cluster compaction
  - Write job to merge micro-clusters (size < 5) with behavioral similarity
  - Reassign cluster IDs while maintaining stable mapping
  - Archive old cluster assignments in `cluster_events`
  - Update all dependent tables with new cluster IDs
  - _Requirements: 2.3, 2.4_

- [ ] 2.7 Write unit tests for clustering algorithms

  - Test common input heuristic with known transaction patterns
  - Test change detection with various output configurations
  - Test cluster merging with graph edge cases
  - Test deterministic ID generation
  - _Requirements: 2.1, 2.2, 2.4_

- [ ] 3. Label Confidence Scoring
  - Implement confidence calculation with weighted formula
  - Generate transparent reason codes
  - Build scoring pipeline with recency decay
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3.1 Create label_scores schema
  - Write SQL DDL for `label_scores` table
  - Configure partitioning and clustering for efficient queries
  - Add indexes for subject_id and entity_id lookups
  - _Requirements: 3.1_

- [ ] 3.2 Implement confidence scoring library
  - Write Python module with confidence calculation function
  - Implement weighted formula (source_weight, match_strength, behavioral_consistency, recency_decay)
  - Define source credibility weights (WalletExplorer: 0.7, Arkham: 0.6, manual: 1.0)
  - Calculate match strength from corroborating source count
  - Compute behavioral consistency from transaction pattern matching
  - _Requirements: 3.1, 3.2_

- [ ] 3.3 Implement reason code generator
  - Define ReasonCode enum with all supported codes
  - Write function to generate reason codes based on scoring inputs
  - Include SRC_MATCH, COSPEND, CHANGE_HEURISTIC, PATTERN_FANIN, RECENT_ACTIVITY, MULTI_SOURCE, ML_PREDICTION
  - Return human-readable descriptions for each code
  - _Requirements: 3.3_

- [ ] 3.4 Implement recency decay function
  - Write function to calculate decay factor based on days since last activity
  - Apply exponential decay: e^(-days/90)
  - Return 1.0 for activity within 30 days
  - Return 0.5 at 90 days, near-zero at 180+ days
  - _Requirements: 3.4_

- [ ] 3.5 Build confidence scoring job
  - Write Cloud Run Job to compute scores for all labels
  - Query address_labels and cluster_labels with entity activity data
  - Calculate confidence for each subject-entity pair
  - Generate reason codes and store in reasons_json
  - Write results to `label_scores` table
  - Classify into verified (≥0.9), likely (0.7-0.89), hint (0.5-0.69) tiers
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3.6 Create backfill job for historical labels
  - Write one-time job to score all existing labels
  - Process in batches to manage BigQuery costs
  - Track progress and support resumption on failure
  - _Requirements: 3.1, 3.2_

- [ ] 3.7 Write unit tests for confidence scoring

  - Test confidence formula with various input combinations
  - Test reason code generation for different scenarios
  - Test recency decay at key thresholds (30d, 90d, 180d)
  - Test tier classification boundaries
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 4. Entity Intelligence API
  - Build FastAPI service with entity resolution endpoints
  - Implement caching and rate limiting
  - Add authentication and observability
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 4.1 Set up FastAPI project structure
  - Create service directory `services/entity-intelligence-api/`
  - Set up FastAPI application with routers
  - Configure Pydantic models for request/response schemas
  - Add CORS middleware for frontend integration
  - Create Dockerfile for Cloud Run deployment
  - _Requirements: 4.1, 4.2_

- [ ] 4.2 Implement entity resolution endpoint
  - Create GET `/v1/entity/resolve` endpoint accepting address parameter
  - Query BigQuery for address_labels and cluster_labels
  - Join with entities table for entity details
  - Join with label_scores for confidence and reasons
  - Return EntityResolveResponse with all fields
  - _Requirements: 4.1, 4.2_

- [ ] 4.3 Implement batch resolution endpoint
  - Create POST `/v1/entity/resolve/batch` endpoint accepting address list
  - Validate maximum 1000 addresses per request
  - Use BigQuery array operations for efficient batch query
  - Return array of EntityResolveResponse objects
  - _Requirements: 4.3_

- [ ] 4.4 Implement entity statistics endpoint
  - Create GET `/v1/entity/{entity_id}/stats` endpoint with window parameter
  - Support time windows: 1h, 24h, 7d, 30d
  - Query entity inflows, outflows, net flow, transaction count
  - Compute top counterparties by transaction value
  - Return EntityStatsResponse with computed metrics
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 4.5 Implement cluster info endpoint
  - Create GET `/v1/cluster/{cluster_id}` endpoint
  - Query cluster details from clusters table
  - Retrieve all addresses in cluster from cluster_addresses
  - Include cluster features and labels
  - Return ClusterResponse with complete information
  - _Requirements: 4.2_

- [ ] 4.6 Implement entity search endpoint
  - Create GET `/v1/search` endpoint with query and type parameters
  - Implement fuzzy matching on entity names using BigQuery LIKE
  - Support search by entity or cluster type
  - Limit results to configurable maximum (default 20)
  - Return list of EntitySearchResult objects
  - _Requirements: 4.1_

- [ ] 4.7 Add Redis caching layer
  - Set up Redis (Memorystore) connection
  - Implement cache-aside pattern for entity resolution
  - Set 1-hour TTL for cached resolutions
  - Add cache hit/miss metrics
  - _Requirements: 4.4_

- [ ] 4.8 Implement authentication and rate limiting
  - Add API key validation middleware
  - Query user tier from database based on API key
  - Implement rate limiting with slowapi (100/min for free tier)
  - Return 401 for invalid keys, 429 for rate limit exceeded
  - _Requirements: 4.5_

- [ ] 4.9 Add observability and logging
  - Implement structured logging with correlation IDs
  - Add OpenTelemetry tracing for request flows
  - Export metrics to Cloud Monitoring (latency, error rate, cache hit rate)
  - Create health check endpoint for Cloud Run
  - _Requirements: 4.1, 4.2_

- [ ] 4.10 Create OpenAPI specification
  - Generate OpenAPI 3.0 spec from FastAPI routes
  - Add detailed descriptions and examples for all endpoints
  - Document error responses and status codes
  - Export spec for client generation
  - _Requirements: 4.1_

- [ ] 4.11 Write API integration tests

  - Test entity resolution with known addresses
  - Test batch resolution with multiple addresses
  - Test entity stats with various time windows
  - Test rate limiting behavior
  - Test authentication with valid and invalid keys
  - Test error handling for invalid inputs
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 5. Dashboard and UI Integration
  - Add entity badges to existing pages
  - Build entity profile pages
  - Implement entity filtering
  - Add CSV export functionality
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 5.1 Create EntityBadge component
  - Build React component with entity name, category, and confidence
  - Add category-specific color coding (exchange: sky, miner: emerald, whale: violet, treasury: amber, mixer: red)
  - Implement confidence color coding (≥0.9: green, 0.7-0.89: amber, <0.7: neutral)
  - Add tooltip showing confidence percentage and reason codes
  - Use shadcn/ui Badge and Tooltip components
  - _Requirements: 6.1, 6.2_

- [ ] 5.2 Integrate entity badges into insight cards
  - Query entity data for addresses mentioned in insights
  - Display EntityBadge when confidence ≥ 0.5
  - Add to InsightCard component in feed and detail pages
  - Handle loading and error states gracefully
  - _Requirements: 6.1_

- [ ] 5.3 Create EntityStats component
  - Build component to display inflow, outflow, net flow, and transaction count
  - Format BTC values with appropriate precision
  - Add sparklines for trend visualization
  - Use Recharts for inline charts
  - _Requirements: 6.4_

- [ ] 5.4 Create EntityActivityChart component
  - Build time-series chart showing entity activity over selected window
  - Display inflows and outflows as separate series
  - Support window selection (1h, 24h, 7d, 30d)
  - Use Recharts AreaChart with gradient fills
  - _Requirements: 6.4_

- [ ] 5.5 Create EntityCounterparties component
  - Build table showing top counterparty entities
  - Display entity name, category badge, and transaction value
  - Sort by value descending
  - Add click-through to counterparty entity profiles
  - Use TanStack Table for sorting and pagination
  - _Requirements: 6.4_

- [ ] 5.6 Build entity profile page
  - Create `/entity/[id]/page.tsx` route in Next.js
  - Fetch entity details and stats using TanStack Query
  - Display entity name, category, and confidence badge
  - Render EntityStats, EntityActivityChart, and EntityCounterparties components
  - Add breadcrumb navigation
  - Implement ISR for public entity profiles
  - _Requirements: 6.4_

- [ ] 5.7 Create EntityFilter component
  - Build filter panel with category tabs (All, Exchange, Miner, Whale, Treasury, Mixer)
  - Add "High confidence only" toggle switch
  - Implement time range selector for future use
  - Use shadcn/ui Tabs and Switch components
  - Emit filter change events to parent components
  - _Requirements: 6.3_

- [ ] 5.8 Integrate entity filtering into insight feed
  - Add EntityFilter to left rail on feed page
  - Filter insights by selected entity categories
  - Apply confidence threshold when toggle enabled
  - Update URL query params to preserve filter state
  - _Requirements: 6.3_

- [ ] 5.9 Implement CSV export for entity flows
  - Add export button to entity profile page
  - Generate CSV with columns: date, counterparty, category, inflow, outflow, net_flow
  - Use browser download API to save file
  - Format filename as `entity-{name}-flows-{date}.csv`
  - _Requirements: 6.5_

- [ ] 5.10 Write E2E tests for entity UI

  - Test entity badge displays on insight cards
  - Test badge tooltip shows confidence and reasons
  - Test clicking badge navigates to entity profile
  - Test entity profile loads and displays charts
  - Test entity filtering updates feed
  - Test CSV export downloads file
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 6. Entity Graph Visualization
  - Build graph data pipeline
  - Create graph API endpoint
  - Implement interactive graph UI
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 6.1 Create entity_edges_daily schema
  - Write SQL DDL for `entity_edges_daily` table
  - Configure partitioning by edge_date
  - Cluster by src_entity_id and dst_entity_id
  - Add indexes for efficient graph queries
  - _Requirements: 7.1_

- [ ] 6.2 Build entity graph computation job
  - Write Cloud Run Job to compute daily entity flows
  - Join transactions with cluster_addresses to attribute flows
  - Join with cluster_labels to get entity IDs
  - Aggregate flows by entity pair and date
  - Filter out self-loops and flows below minimum threshold (0.1 BTC)
  - Write to `entity_edges_daily` table
  - _Requirements: 7.1, 7.2_

- [ ] 6.3 Implement graph API endpoint
  - Create GET `/v1/graph` endpoint with window, min_btc, and categories parameters
  - Query entity_edges_daily for specified time window
  - Aggregate edges across days in window
  - Filter by minimum BTC value and entity categories
  - Compute node values (total flow per entity)
  - Return GraphResponse with nodes and edges arrays
  - _Requirements: 7.2_

- [ ] 6.4 Create EntityGraph component
  - Build React component using react-force-graph library
  - Fetch graph data using TanStack Query
  - Transform API response to graph format (nodes, links)
  - Configure node colors by category
  - Size nodes by total value (sqrt scale)
  - Weight edges by transaction value
  - Add directional particles for flow visualization
  - _Requirements: 7.1, 7.3_

- [ ] 6.5 Add graph interactivity
  - Implement node hover to show entity details
  - Display hover card with entity name, category, and total value
  - Add pan and zoom controls
  - Implement node search/filter input
  - Add click handler to navigate to entity profile
  - _Requirements: 7.3, 7.4_

- [ ] 6.6 Create graph page
  - Create `/graph/page.tsx` route in Next.js
  - Add EntityGraph component with full-screen layout
  - Add controls for window selection, minimum BTC filter, and category filter
  - Implement loading and error states
  - _Requirements: 7.1, 7.3_

- [ ] 6.7 Write tests for graph visualization

  - Test graph data computation with sample transactions
  - Test graph API returns correct nodes and edges
  - Test graph component renders without errors
  - Test node hover displays entity information
  - Test filtering updates graph
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 7. Alert Engine
  - Build alert facts computation pipeline
  - Implement alert rule evaluation
  - Create alert delivery system
  - Add alert UI components
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 7.1 Create alerts schema in BigQuery
  - Write SQL DDL for `alerts_rules`, `alerts_facts`, `alerts_events` tables
  - Configure partitioning and clustering
  - Add indexes for efficient rule evaluation
  - _Requirements: 8.1, 8.2_

- [ ] 7.2 Build alert facts computation job
  - Write Cloud Run Job to compute entity metrics hourly
  - Calculate inflow_1h, inflow_24h, outflow_1h, outflow_24h, net_flow_24h
  - Compute outflow_spike_vs_30d (compare to 30-day baseline)
  - Write metrics to `alerts_facts` table
  - Support incremental computation for efficiency
  - _Requirements: 8.2_

- [ ] 7.3 Implement alert rule evaluator
  - Write function to query active alert rules
  - Parse rule parameters (metric, threshold, entity filters)
  - Query matching facts from `alerts_facts` table
  - Check for condition matches
  - Implement 24-hour deduplication window
  - Create alert events for matches
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 7.4 Build alert delivery system
  - Write function to deliver alerts via configured channels
  - Implement in-app feed delivery (publish to user feed)
  - Implement email delivery using SendGrid or similar
  - Add webhook delivery for external integrations
  - Update alert event status (pending → delivered/failed)
  - Implement retry logic for failed deliveries
  - _Requirements: 8.3_

- [ ] 7.5 Create alert configuration API endpoints
  - Create POST `/v1/alerts/rules` endpoint to create alert rules
  - Create GET `/v1/alerts/rules` endpoint to list user's rules
  - Create PATCH `/v1/alerts/rules/{id}` endpoint to update rules
  - Create DELETE `/v1/alerts/rules/{id}` endpoint to delete rules
  - Validate rule parameters and thresholds
  - _Requirements: 8.1, 8.5_

- [ ] 7.6 Create alerts feed API endpoint
  - Create GET `/v1/alerts` endpoint to retrieve user's alert events
  - Support pagination and filtering by status
  - Sort by created_at descending
  - Return alert details with entity information
  - _Requirements: 8.3_

- [ ] 7.7 Build AlertRuleForm component
  - Create form for configuring alert rules
  - Add metric selector (inflow, outflow, net flow, spike)
  - Add threshold input with BTC unit
  - Add entity category filter (optional)
  - Add channel selection (in-app, email, webhook)
  - Use react-hook-form and zod for validation
  - _Requirements: 8.1, 8.5_

- [ ] 7.8 Build AlertsList component
  - Create component to display user's configured alert rules
  - Show metric, threshold, entity filter, and status
  - Add toggle to enable/disable rules
  - Add edit and delete actions
  - Display last triggered timestamp
  - _Requirements: 8.5_

- [ ] 7.9 Build AlertsFeed component
  - Create component to display triggered alerts
  - Show entity name, metric, value, and timestamp
  - Add category badge for entity
  - Implement real-time updates with polling or WebSocket
  - Add mark as read functionality
  - _Requirements: 8.3_

- [ ] 7.10 Create alerts page
  - Create `/alerts/page.tsx` route in Next.js
  - Add two-column layout: AlertRuleForm (left) and AlertsList (right)
  - Add AlertsFeed section below
  - Implement empty states for no rules and no alerts
  - _Requirements: 8.1, 8.3, 8.5_

- [ ] 7.11 Write tests for alert engine

  - Test alert facts computation with sample entity data
  - Test rule evaluation matches correct conditions
  - Test deduplication prevents duplicate alerts
  - Test alert delivery to different channels
  - Test alert UI components render correctly
  - Test creating and managing alert rules
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 8. Machine Learning Classification
  - Build feature extraction pipeline
  - Implement model training workflow
  - Create prediction and labeling system
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 8.1 Create ml_features_daily schema
  - Write SQL DDL for `ml_features_daily` table
  - Include structural, temporal, flow, UTXO, and fee feature columns
  - Configure partitioning by feature_date
  - Cluster by cluster_id for efficient queries
  - _Requirements: 9.1_

- [ ] 8.2 Implement feature extraction job
  - Write Cloud Run Job to extract features for all clusters
  - Compute structural features (avg inputs/outputs, script diversity, reuse rate)
  - Compute temporal features (tx frequency, burstiness, diurnal patterns)
  - Compute flow features (fanin/fanout entropy, counterparty diversity, self-churn)
  - Compute UTXO features (age distribution, coin days destroyed)
  - Compute fee features (avg fee rate, fee vs mempool baseline)
  - Support 1d, 7d, and 30d rolling windows
  - Write features to `ml_features_daily` table
  - _Requirements: 9.1_

- [ ] 8.3 Build BigQuery ML training pipeline
  - Write SQL to create logistic regression model using BigQuery ML
  - Use high-confidence labeled clusters (confidence ≥ 0.9) as training data
  - Apply auto class weights for balanced training
  - Train on features from last 90 days
  - Version models with timestamp suffix
  - _Requirements: 9.2, 9.3_

- [ ] 8.4 Implement model evaluation
  - Write SQL to evaluate model on 10% holdout set
  - Compute precision, recall, F1 score per category
  - Store evaluation metrics in GCS as JSON
  - Generate confusion matrix for analysis
  - _Requirements: 9.3_

- [ ] 8.5 Build model promotion logic
  - Write function to compare new model to current production model
  - Check precision ≥ 0.95 for exchange and miner categories
  - Promote model if it meets criteria and outperforms current
  - Update model alias to point to new version
  - Log promotion decision and metrics
  - _Requirements: 9.3_

- [ ] 8.6 Implement prediction job
  - Write Cloud Run Job to classify unlabeled clusters
  - Query clusters without high-confidence labels
  - Extract features and run ML.PREDICT on current model
  - Filter predictions to confidence ≥ 0.70
  - Write predicted labels to `cluster_labels` with method='ml_model'
  - _Requirements: 9.4_

- [ ] 8.7 Create ML model registry
  - Set up GCS bucket for model artifacts and evaluation reports
  - Store model metadata (version, training date, metrics) in BigQuery table
  - Implement versioning scheme (YYYYMMDD_HHMMSS)
  - Add model lineage tracking (training data version, feature version)
  - _Requirements: 9.5_

- [ ] 8.8 Write tests for ML pipeline

  - Test feature extraction with sample cluster data
  - Test model training completes without errors
  - Test evaluation metrics are computed correctly
  - Test promotion logic with various metric scenarios
  - Test prediction generates valid labels
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 9. Data Pipeline Orchestration
  - Set up Cloud Scheduler for job triggers
  - Implement job monitoring and alerting
  - Create pipeline dashboards
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 9.1 Configure Cloud Scheduler jobs
  - Create hourly schedule for clustering, label joins, feature aggregation (1d), alert facts, alert evaluation
  - Create daily schedule for 7d/30d features, graph edges, confidence scoring
  - Create weekly schedule for ML training, cluster compaction
  - Set appropriate timeouts and retry policies
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 9.2 Implement job idempotency
  - Add idempotency keys to all pipeline jobs
  - Use date-based keys for daily/weekly jobs
  - Check for existing results before processing
  - Support safe retries without duplicate work
  - _Requirements: 10.4_

- [ ] 9.3 Add pipeline monitoring
  - Export job execution metrics to Cloud Monitoring (duration, success/failure, rows processed)
  - Create custom metrics for data quality (label coverage, cluster size distribution)
  - Set up log-based metrics for errors and warnings
  - _Requirements: 10.5_

- [ ] 9.4 Create pipeline alerting
  - Set up alerts for job failures
  - Alert on BigQuery cost spikes (> $100/day)
  - Alert on data freshness issues (no updates in 2+ hours)
  - Alert on ML model performance degradation
  - Configure notification channels (email, Slack)
  - _Requirements: 10.5_

- [ ] 9.5 Build pipeline dashboard
  - Create Cloud Monitoring dashboard for Entity Intelligence
  - Add charts for job execution status and duration
  - Add charts for data volume metrics (labels, clusters, entities)
  - Add charts for API performance (latency, cache hit rate)
  - Add charts for BigQuery costs
  - _Requirements: 10.5_

- [ ] 10. Cost Optimization
  - Implement BigQuery cost controls
  - Create materialized views for hot queries
  - Add query cost validation
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 10.1 Configure table partitioning and clustering
  - Verify all tables are partitioned by date column
  - Verify clustering on frequently filtered columns
  - Add partition expiration for temporary tables (90 days)
  - Document partitioning strategy in schema comments
  - _Requirements: 11.1, 11.2_

- [ ] 10.2 Create materialized views for entity stats
  - Create MV for 24h entity statistics (refreshed hourly)
  - Create MV for 7d entity statistics (refreshed daily)
  - Use MVs in API queries instead of computing on-demand
  - Monitor MV refresh costs and performance
  - _Requirements: 11.3_

- [ ] 10.3 Implement incremental processing
  - Modify all jobs to process only new data since last run
  - Use watermark tables to track last processed timestamp
  - Avoid full table scans in recurring jobs
  - _Requirements: 11.5_

- [ ] 10.4 Add query cost validation to CI
  - Write script to dry-run all production queries
  - Assert query costs are below thresholds
  - Fail CI if queries exceed cost limits
  - Generate cost report for review
  - _Requirements: 11.4_

- [ ] 10.5 Implement query result caching
  - Enable BigQuery query result caching (24-hour TTL)
  - Use cached results for repeated queries
  - Monitor cache hit rate
  - _Requirements: 11.3_

- [ ] 11. Security and Compliance
  - Configure service account permissions
  - Implement audit logging
  - Add data export security
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 11.1 Create service accounts with least privilege
  - Create read-only service account for blockchain data access
  - Create service account for entity intelligence writes
  - Create service account for API service
  - Grant only necessary BigQuery and GCS permissions
  - Document permission requirements
  - _Requirements: 12.1_

- [ ] 11.2 Implement API authentication
  - Add API key validation to all protected endpoints
  - Store API keys securely in Cloud SQL with hashing
  - Implement key rotation mechanism
  - Add user tier lookup for rate limiting
  - _Requirements: 12.2_

- [ ] 11.3 Add audit logging for label changes
  - Log all inserts/updates to label tables
  - Include operator identifier, timestamp, and change details
  - Write audit logs to separate BigQuery dataset
  - Implement log retention policy (7 years)
  - _Requirements: 12.3_

- [ ] 11.4 Implement signed URLs for exports
  - Generate signed GCS URLs for CSV exports
  - Set 1-hour expiration on signed URLs
  - Validate user authorization before generating URLs
  - Log all export requests
  - _Requirements: 12.4_

- [ ] 11.5 Configure PII isolation
  - Create separate GCP project for PII data if email alerts are implemented
  - Ensure entity intelligence data contains no PII
  - Document data classification and handling procedures
  - _Requirements: 12.5_

- [ ] 12. Documentation and Deployment
  - Write API documentation
  - Create operational runbooks
  - Build deployment automation
  - Conduct acceptance testing

- [ ] 12.1 Write API documentation
  - Document all API endpoints with examples
  - Include authentication and rate limiting details
  - Provide code samples in Python and TypeScript
  - Document error codes and responses
  - Publish to developer portal

- [ ] 12.2 Create operational runbooks
  - Write runbook for label source failures
  - Write runbook for clustering job failures
  - Write runbook for ML model issues
  - Write runbook for API performance degradation
  - Document escalation procedures

- [ ] 12.3 Build deployment scripts
  - Create Terraform configurations for all GCP resources
  - Write deployment script for API service
  - Write deployment script for Cloud Run Jobs
  - Configure Cloud Build triggers for CI/CD
  - Document deployment process

- [ ] 12.4 Create monitoring dashboard
  - Build comprehensive dashboard in Cloud Monitoring
  - Add SLO tracking for API latency and availability
  - Add data quality metrics
  - Add cost tracking charts
  - Share dashboard with team

- [ ] 12.5 Conduct acceptance testing
  - Test: Given known Binance address, resolve returns entity Binance, category exchange, confidence ≥0.9
  - Test: Two addresses co-spent in N transactions merge to one cluster with deterministic ID
  - Test: Removing source records lowers confidence score within one daily cycle
  - Test: API p95 latency < 300ms with warm cache
  - Test: UI filters exclude mixers from all charts when enabled
  - Test: 7d graph view shows top 20 entity edges matching BigQuery snapshot within 1%
  - Test: Simulated whale deposit triggers alert exactly once, status transitions to delivered
  - Document test results and sign-off

- [ ] 12.6 Prepare beta release
  - Enable feature flags for beta users (10% traffic)
  - Monitor metrics and error rates
  - Collect user feedback
  - Fix critical issues
  - Prepare for general availability rollout
