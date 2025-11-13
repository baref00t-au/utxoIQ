# Requirements Document

## Introduction

This specification addresses the critical missing components in the utxoIQ intelligence pipeline. Currently, signal processors compute blockchain signals but never persist them to BigQuery, and the insight generator operates in isolation without consuming actual signal data. This creates a broken pipeline where blocks are ingested but no intelligence is extracted or surfaced to users.

The goal is to wire together the existing signal processors, insight generator, and data storage layers into a functioning end-to-end pipeline that transforms Bitcoin blocks into actionable insights within 60 seconds.

## Glossary

- **Signal**: A computed metric or pattern detected from blockchain data (e.g., mempool fee spike, exchange outflow, miner accumulation)
- **Signal Processor**: Python class that analyzes blockchain data and computes signals with confidence scores
- **Insight**: AI-generated human-readable explanation of why a signal matters, including blockchain evidence
- **Insight Generator**: Service using AI (Vertex AI, OpenAI, Anthropic, or xAI Grok) to transform signals into natural language insights
- **AI Provider**: Pluggable interface for different LLM providers (Vertex AI Gemini, OpenAI GPT, Anthropic Claude, xAI Grok)
- **utxoiq-ingestion**: Service that polls Bitcoin Core and writes blocks to BigQuery
- **intel.signals**: BigQuery table storing computed signals with metadata
- **intel.insights**: BigQuery table storing AI-generated insights with confidence scores
- **Block Monitor**: Component within utxoiq-ingestion that detects new Bitcoin blocks
- **Pipeline**: The complete flow from block detection → signal generation → insight creation → user delivery
- **Known Entity**: Identified exchange (Coinbase, Kraken, Binance) or mining pool (Foundry USA, AntPool, F2Pool) with tracked addresses
- **Entity Database**: BigQuery table (btc.known_entities) storing identified exchange and miner addresses with metadata
- **Predictive Signal**: Forward-looking signal that forecasts future blockchain metrics (fee rates, liquidity pressure)
- **Historical Backfill**: Process of generating signals and insights for past blocks to populate historical data

## Requirements

### Requirement 1: Signal Persistence

**User Story:** As a platform operator, I want signals to be persisted to BigQuery after computation, so that they can be queried for insight generation and historical analysis.

#### Acceptance Criteria

1. WHEN the utxoiq-ingestion service processes a Bitcoin block, THE Signal Persistence Module SHALL invoke all registered signal processors (mempool, exchange, miner, whale)
2. WHEN a signal processor computes a signal, THE Signal Persistence Module SHALL generate a unique signal ID using UUID format
3. WHEN signal computation completes, THE Signal Persistence Module SHALL write the signal record to the intel.signals BigQuery table with all required fields (signal_id, signal_type, block_height, confidence, metadata, created_at)
4. IF signal persistence fails, THEN THE Signal Persistence Module SHALL log the error with correlation ID and continue processing without blocking block ingestion
5. WHEN multiple signals are generated from a single block, THE Signal Persistence Module SHALL batch insert all signals in a single BigQuery operation

### Requirement 2: Signal Data Extraction

**User Story:** As a signal processor, I need structured blockchain data extracted from blocks and Bitcoin Core RPC, so that I can compute meaningful signals.

#### Acceptance Criteria

1. WHEN a new block is ingested, THE Data Extraction Module SHALL query Bitcoin Core RPC for mempool statistics (fee rates, transaction count, size)
2. WHEN processing block transactions, THE Data Extraction Module SHALL identify exchange addresses by matching against a known exchange address list stored in BigQuery
3. WHEN analyzing transaction outputs, THE Data Extraction Module SHALL detect whale addresses where the total balance exceeds 1000 BTC
4. WHEN computing miner signals, THE Data Extraction Module SHALL track miner treasury addresses and calculate balance changes
5. WHEN historical comparison is needed, THE Data Extraction Module SHALL query BigQuery for previous signal values within the specified time window (1 hour, 24 hours, 7 days)

### Requirement 3: Signal-Triggered Insight Generation

**User Story:** As the insight generator service, I want to poll for new unprocessed signals and generate insights from them, so that users receive timely blockchain intelligence.

#### Acceptance Criteria

1. WHEN the insight-generator service starts, THE Signal Polling Module SHALL query intel.signals for records where processed equals false and confidence is greater than or equal to 0.7 and signal_type is in the list (mempool, exchange, miner, whale, predictive)
2. WHEN new signals are found, THE Signal Polling Module SHALL group signals by signal_type and block_height for batch processing
3. WHEN generating an insight, THE Insight Generation Module SHALL pass the signal metadata to the appropriate AI prompt template based on signal_type (mempool, exchange, miner, whale, or predictive)
4. WHEN the AI provider returns generated content, THE Insight Generation Module SHALL create an insight record with signal_id reference, category matching signal_type, headline, summary, confidence score, and blockchain evidence
5. WHEN an insight is successfully created, THE Signal Polling Module SHALL update the source signal record setting processed equals true and processed_at equals current timestamp

### Requirement 4: Insight Persistence and Metadata

**User Story:** As the insight generator, I want to persist generated insights with complete metadata and blockchain citations, so that users can verify and explore the underlying data.

#### Acceptance Criteria

1. WHEN an insight is generated, THE Insight Persistence Module SHALL write the insight record to intel.insights BigQuery table with all required fields (insight_id, signal_id, category, headline, summary, confidence, evidence, created_at)
2. WHEN writing insight evidence, THE Insight Persistence Module SHALL include block heights as an array and transaction IDs as an array extracted from the signal metadata
3. WHEN insight persistence succeeds, THE Insight Persistence Module SHALL return the insight_id to the caller for reference
4. IF insight persistence fails, THEN THE Insight Persistence Module SHALL log the error with signal_id context and mark the signal as unprocessed for retry
5. WHEN an insight is created, THE Insight Persistence Module SHALL set the chart_url field to null for later population by the chart renderer

### Requirement 5: End-to-End Pipeline Orchestration

**User Story:** As a platform operator, I want the complete pipeline to execute automatically when new blocks arrive, so that insights are generated within 60 seconds of block detection.

#### Acceptance Criteria

1. WHEN the block monitor detects a new Bitcoin block, THE Pipeline Orchestrator SHALL trigger the signal generation workflow within 5 seconds
2. WHEN signal generation completes, THE Pipeline Orchestrator SHALL trigger the insight generation workflow within 10 seconds
3. WHEN the complete pipeline executes, THE Pipeline Orchestrator SHALL log timing metrics for each stage (block ingestion, signal generation, insight generation) with correlation ID
4. IF any pipeline stage fails, THEN THE Pipeline Orchestrator SHALL log the failure with context and continue processing subsequent blocks without blocking
5. WHEN pipeline execution completes, THE Pipeline Orchestrator SHALL emit a success metric to Cloud Monitoring with total execution time

### Requirement 6: Error Handling and Resilience

**User Story:** As a platform operator, I want the pipeline to handle failures gracefully without data loss, so that temporary issues don't break the intelligence generation process.

#### Acceptance Criteria

1. WHEN a signal processor raises an exception, THE Error Handler SHALL log the error with block_height and signal_type context and continue processing other signal types
2. WHEN BigQuery write operations fail, THE Error Handler SHALL implement exponential backoff retry with a maximum of 3 attempts
3. WHEN Vertex AI API calls fail, THE Error Handler SHALL log the error and mark the signal as unprocessed for later retry
4. IF a signal remains unprocessed for more than 1 hour, THEN THE Error Handler SHALL emit an alert to Cloud Monitoring
5. WHEN errors occur, THE Error Handler SHALL include correlation IDs in all log messages for request tracing across services

### Requirement 7: Signal Processing Configuration

**User Story:** As a platform operator, I want to configure which signal processors run and their thresholds, so that I can tune the system without code changes.

#### Acceptance Criteria

1. WHEN the utxoiq-ingestion service starts, THE Configuration Module SHALL load signal processor settings from environment variables (enabled processors, confidence thresholds, time windows)
2. WHEN processing blocks, THE Configuration Module SHALL only invoke signal processors where enabled equals true in the configuration
3. WHEN computing signals, THE Configuration Module SHALL apply the configured confidence threshold to filter low-quality signals before persistence
4. WHEN configuration changes, THE Configuration Module SHALL allow hot-reload without service restart by polling configuration every 5 minutes
5. WHERE a signal processor is disabled, THE Configuration Module SHALL skip that processor and log the skip event for audit purposes

### Requirement 8: AI Provider Configuration

**User Story:** As a platform operator, I want to configure which AI provider to use for insight generation, so that I can switch between Vertex AI, OpenAI, Anthropic, or xAI Grok without code changes.

#### Acceptance Criteria

1. WHEN the insight-generator service starts, THE AI Provider Module SHALL load the provider configuration from environment variables (AI_PROVIDER, API_KEY, MODEL_NAME)
2. WHERE AI_PROVIDER equals "vertex_ai", THE AI Provider Module SHALL initialize the Vertex AI client with Gemini Pro model
3. WHERE AI_PROVIDER equals "openai", THE AI Provider Module SHALL initialize the OpenAI client with the configured GPT model
4. WHERE AI_PROVIDER equals "anthropic", THE AI Provider Module SHALL initialize the Anthropic client with the configured Claude model
5. WHERE AI_PROVIDER equals "grok", THE AI Provider Module SHALL initialize the xAI client with the configured Grok model
6. WHEN generating insights, THE AI Provider Module SHALL use the configured provider's API with consistent prompt formatting across all providers
7. IF the configured AI provider fails, THEN THE AI Provider Module SHALL log the error and mark the signal as unprocessed for retry without switching providers
8. WHEN AI provider responses are received, THE AI Provider Module SHALL parse and validate the response format (headline, summary, confidence_explanation) regardless of provider

### Requirement 9: Known Entity Identification

**User Story:** As a signal processor, I want to identify specific exchanges and mining pools by name, so that insights can reference recognizable entities like "Coinbase" or "Foundry USA" instead of anonymous addresses.

#### Acceptance Criteria

1. WHEN the utxoiq-ingestion service starts, THE Entity Identification Module SHALL load the known entities database from btc.known_entities BigQuery table containing exchange and miner addresses with entity names
2. WHEN processing block transactions, THE Entity Identification Module SHALL match transaction addresses against the known entities database to identify exchanges (Coinbase, Kraken, Binance, Gemini, Bitstamp) and mining pools (Foundry USA, AntPool, F2Pool, ViaBTC, Binance Pool)
3. WHEN an entity is identified, THE Entity Identification Module SHALL include the entity_id and entity_name in the signal metadata for reference in insights
4. WHEN generating exchange signals, THE Entity Identification Module SHALL group flows by entity_name to track per-exchange metrics
5. WHEN generating miner signals, THE Entity Identification Module SHALL identify the mining pool from the coinbase transaction and include pool_name in the signal metadata
6. WHERE an address is not in the known entities database, THE Entity Identification Module SHALL label it as "unknown" and continue processing
7. WHEN the known entities database is updated, THE Entity Identification Module SHALL reload the entity list within 5 minutes without service restart

### Requirement 10: Predictive Signal Processing

**User Story:** As a platform operator, I want to generate predictive signals for fee forecasts and liquidity pressure, so that users receive forward-looking intelligence in addition to current observations.

#### Acceptance Criteria

1. WHEN the utxoiq-ingestion service processes a block, THE Predictive Analytics Module SHALL generate fee forecast signals using exponential smoothing on historical mempool data
2. WHEN exchange flow signals are computed, THE Predictive Analytics Module SHALL generate liquidity pressure signals using z-score normalization on historical flow patterns
3. WHEN predictive signals are generated, THE Predictive Analytics Module SHALL include prediction value, confidence interval, forecast horizon, and model version in the signal metadata
4. WHEN persisting predictive signals, THE Signal Persistence Module SHALL set signal_type to "predictive" and include the prediction_type field (fee_forecast or liquidity_pressure)
5. WHEN generating insights from predictive signals, THE Insight Generation Module SHALL use predictive-specific prompt templates that emphasize forward-looking implications
6. WHEN predictive signal confidence is below 0.5, THE Predictive Analytics Module SHALL not persist the signal to avoid low-quality predictions

### Requirement 11: Historical Signal Backfill

**User Story:** As a platform operator, I want to backfill historical signals for recent blocks, so that the platform has baseline data for comparison and the Daily Brief can show historical context.

#### Acceptance Criteria

1. WHEN the backfill process is initiated, THE Historical Backfill Module SHALL query btc.blocks for blocks within the specified date range (default: last 30 days)
2. WHEN processing historical blocks, THE Historical Backfill Module SHALL invoke signal processors with historical context data from surrounding blocks for accurate signal computation
3. WHEN generating signals from historical blocks, THE Historical Backfill Module SHALL write signals to intel.signals with the original block timestamp, not the backfill execution time
4. WHEN backfilling signals, THE Historical Backfill Module SHALL process blocks in chronological order to maintain temporal consistency for time-series analysis
5. WHEN backfill completes for a date range, THE Historical Backfill Module SHALL mark signals as processed equals false to trigger insight generation
6. WHERE AI costs are a concern, THE Historical Backfill Module SHALL support selective backfill for specific signal types or date ranges via configuration
7. WHEN backfilling, THE Historical Backfill Module SHALL implement rate limiting (maximum 100 blocks per minute) to avoid overwhelming BigQuery and Bitcoin Core RPC

### Requirement 12: Monitoring and Observability

**User Story:** As a platform operator, I want visibility into pipeline performance and health, so that I can identify bottlenecks and failures quickly.

#### Acceptance Criteria

1. WHEN each pipeline stage completes, THE Monitoring Module SHALL emit timing metrics to Cloud Monitoring (signal_generation_duration_ms, insight_generation_duration_ms, total_pipeline_duration_ms)
2. WHEN signals are generated, THE Monitoring Module SHALL emit count metrics by signal_type (mempool, exchange, miner, whale, predictive) and confidence_bucket (high, medium, low)
3. WHEN insights are created, THE Monitoring Module SHALL emit count metrics by category (mempool, exchange, miner, whale, predictive) and confidence_bucket
4. WHEN entities are identified, THE Monitoring Module SHALL emit count metrics by entity_name for exchanges and mining pools
5. WHEN errors occur, THE Monitoring Module SHALL emit error count metrics by error_type, service_name, and ai_provider
6. WHEN the pipeline processes blocks, THE Monitoring Module SHALL maintain a counter for total_blocks_processed and total_insights_generated for dashboard display
7. WHEN AI provider API calls complete, THE Monitoring Module SHALL emit latency metrics by provider (vertex_ai, openai, anthropic, grok) for performance comparison
8. WHEN historical backfill runs, THE Monitoring Module SHALL emit progress metrics (blocks_backfilled, signals_generated, estimated_completion_time)
