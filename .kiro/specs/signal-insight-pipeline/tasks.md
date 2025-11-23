# Implementation Plan

- [x] 1. Set up BigQuery schema and data models





  - Create intel.signals table with partitioning by created_at
  - Create intel.insights table with partitioning by created_at
  - Update btc.known_entities table to include treasury companies with metadata (ticker, known_holdings_btc)
  - Create Python Pydantic models for Signal, Insight, Evidence, and EntityInfo
  - _Requirements: 1.3, 4.2, 9.1_

- [x] 2. Implement Signal Persistence Module




  - [x] 2.1 Create SignalPersistenceModule class with BigQuery client integration


    - Implement generate_signal_id() method using UUID
    - Implement persist_signals() method with batch insert logic
    - Add error handling with correlation ID logging
    - _Requirements: 1.2, 1.3, 1.4_
  
  - [x] 2.2 Add retry logic for BigQuery write failures


    - Implement exponential backoff (1s, 2s, 4s) with max 3 attempts
    - Log retry attempts with correlation IDs
    - _Requirements: 6.2_

- [x] 3. Implement Data Extraction Module





  - [x] 3.1 Create DataExtractionModule class with Bitcoin RPC and BigQuery clients


    - Implement get_mempool_stats() method for Bitcoin Core RPC queries
    - Implement get_historical_signals() method for BigQuery time-series queries
    - _Requirements: 2.1, 2.5_
  
  - [x] 3.2 Implement entity identification methods


    - Implement identify_exchange_addresses() method with entity database lookup
    - Implement detect_whale_addresses() method for >1000 BTC balance detection
    - _Requirements: 2.2, 2.3, 2.4_

- [x] 4. Implement Entity Identification Module




  - [x] 4.1 Create EntityIdentificationModule class with caching


    - Implement load_known_entities() method to query btc.known_entities table
    - Implement identify_entity() method with in-memory cache lookup
    - Implement identify_mining_pool() method for coinbase transaction parsing
    - Implement identify_treasury_company() method for public company detection
    - _Requirements: 9.1, 9.2, 9.3, 9.5_
  
  - [x] 4.2 Add cache reload mechanism


    - Implement should_reload() check for 5-minute interval
    - Add background task for automatic cache refresh
    - _Requirements: 9.7_

- [x] 5. Implement Signal Processors





  - [x] 5.1 Create base SignalProcessor abstract class


    - Define process_block() abstract method
    - Implement calculate_confidence() helper method
    - Add enabled flag and confidence_threshold configuration
    - _Requirements: 1.1, 7.2, 7.3_
  
  - [x] 5.2 Implement MempoolProcessor


    - Analyze mempool fee rate changes vs historical data
    - Generate signals for significant fee spikes (>20% change)
    - Include metadata: fee_rate_median, fee_rate_change_pct, mempool_size_mb, tx_count
    - _Requirements: 2.1, 2.5_
  
  - [x] 5.3 Implement ExchangeProcessor


    - Detect exchange inflows and outflows using entity identification
    - Track per-exchange flow volumes
    - Include metadata: entity_id, entity_name, flow_type, amount_btc, tx_count
    - _Requirements: 2.2, 9.3, 9.4_
  
  - [x] 5.4 Implement MinerProcessor


    - Identify mining pool from coinbase transaction
    - Track miner treasury balance changes
    - Include metadata: pool_name, amount_btc, treasury_balance_change
    - _Requirements: 2.4, 9.5_
  
  - [x] 5.5 Implement WhaleProcessor


    - Detect transactions to/from addresses with >1000 BTC balance
    - Calculate whale movement significance
    - Include metadata: whale_address, amount_btc, balance_btc
    - _Requirements: 2.3_
  
  - [x] 5.6 Implement TreasuryProcessor


    - Identify public company treasury transactions using entity identification
    - Track accumulation and distribution patterns
    - Calculate holdings change percentage
    - Include metadata: entity_name, company_ticker, flow_type, amount_btc, known_holdings_btc, holdings_change_pct
    - _Requirements: 9.3, 9.6_

- [x] 6. Implement Predictive Analytics Module




  - [x] 6.1 Create PredictiveAnalyticsModule class


    - Implement generate_fee_forecast() using exponential smoothing
    - Implement generate_liquidity_pressure() using z-score normalization
    - Filter predictions with confidence <0.5
    - _Requirements: 10.1, 10.2, 10.6_
  
  - [x] 6.2 Add predictive signal metadata


    - Include prediction_type, predicted_value, confidence_interval, forecast_horizon, model_version
    - Set signal_type to "predictive" with prediction_type field
    - _Requirements: 10.3, 10.4_


- [x] 7. Implement Pipeline Orchestrator




  - [x] 7.1 Create PipelineOrchestrator class

    - Implement process_new_block() method with correlation ID generation
    - Implement _generate_signals() method to run all enabled processors in parallel
    - Add timing metrics for each stage (signal generation, persistence)
    - _Requirements: 5.1, 5.3_
  

  - [x] 7.2 Add error handling and monitoring

    - Log processor failures without blocking other processors
    - Emit success metrics to Cloud Monitoring with total execution time
    - Handle failures gracefully and continue processing subsequent blocks
    - _Requirements: 5.4, 6.1_

- [x] 8. Implement Configuration Module





  - [x] 8.1 Create ConfigurationModule class

    - Load processor settings from environment variables (enabled flags, thresholds, time windows)
    - Implement should_reload() check for 5-minute interval
    - Implement reload_config() method for hot-reload
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 9. Integrate signal generation into utxoiq-ingestion service





  - [x] 9.1 Wire Pipeline Orchestrator into block monitor


    - Trigger signal generation within 5 seconds of block detection
    - Pass block data to orchestrator
    - _Requirements: 5.1_
  
  - [x] 9.2 Add signal persistence after generation


    - Call SignalPersistenceModule with generated signals
    - Log correlation IDs for tracing
    - _Requirements: 1.5, 5.3_

- [x] 10. Implement AI Provider Module





  - [x] 10.1 Create AIProvider abstract base class


    - Define generate_insight() abstract method
    - _Requirements: 8.1, 8.6_
  
  - [x] 10.2 Implement VertexAIProvider

    - Initialize Vertex AI client with Gemini Pro model
    - Format prompts and parse JSON responses
    - _Requirements: 8.2_
  
  - [x] 10.3 Implement OpenAIProvider

    - Initialize OpenAI client with configured GPT model
    - Format prompts and parse JSON responses
    - _Requirements: 8.3_
  
  - [x] 10.4 Implement AnthropicProvider

    - Initialize Anthropic client with configured Claude model
    - Format prompts and parse JSON responses
    - _Requirements: 8.4_
  
  - [x] 10.5 Implement GrokProvider

    - Initialize xAI client with configured Grok model
    - Format prompts and parse JSON responses
    - _Requirements: 8.5_
  
  - [x] 10.6 Add provider configuration loading

    - Load AI_PROVIDER, API keys, and model names from environment variables
    - Implement provider factory to instantiate correct provider
    - _Requirements: 8.1_
  
  - [x] 10.7 Add error handling for AI provider failures

    - Log errors with signal_id context
    - Return error status without switching providers
    - _Requirements: 8.7_

- [x] 11. Create AI prompt templates





  - [x] 11.1 Create mempool_prompt.py with MEMPOOL_TEMPLATE


    - Include fields: fee_rate_median, fee_rate_change_pct, mempool_size_mb, tx_count
    - Request JSON output: headline, summary, confidence_explanation
    - _Requirements: 3.3_
  
  - [x] 11.2 Create exchange_prompt.py with EXCHANGE_TEMPLATE


    - Include fields: entity_name, flow_type, amount_btc, tx_count, block_height
    - Request JSON output with exchange name in headline
    - _Requirements: 3.3_
  
  - [x] 11.3 Create miner_prompt.py with MINER_TEMPLATE


    - Include fields: pool_name, amount_btc, treasury_balance_change
    - Request JSON output emphasizing mining pool activity
    - _Requirements: 3.3_
  
  - [x] 11.4 Create whale_prompt.py with WHALE_TEMPLATE


    - Include fields: whale_address, amount_btc, balance_btc
    - Request JSON output emphasizing large holder movements
    - _Requirements: 3.3_
  
  - [x] 11.5 Create treasury_prompt.py with TREASURY_TEMPLATE


    - Include fields: entity_name, company_ticker, flow_type, amount_btc, known_holdings_btc, holdings_change_pct
    - Request JSON output mentioning company name and ticker
    - _Requirements: 3.3_
  
  - [x] 11.6 Create predictive_prompt.py with PREDICTIVE_TEMPLATE


    - Include fields: prediction_type, predicted_value, confidence_interval, forecast_horizon, current_value
    - Request JSON output emphasizing forward-looking nature
    - _Requirements: 10.5_

- [x] 12. Implement Signal Polling Module





  - [x] 12.1 Create SignalPollingModule class


    - Implement poll_unprocessed_signals() method to query BigQuery for processed=false and confidence>=0.7
    - Group signals by signal_type and block_height for batch processing
    - _Requirements: 3.1, 3.2_
  
  - [x] 12.2 Implement signal marking logic

    - Implement mark_signal_processed() method to update processed=true and processed_at timestamp
    - _Requirements: 3.5_

- [ ] 13. Implement Insight Generation Module




  - [x] 13.1 Create InsightGenerationModule class

    - Implement generate_insight() method to select prompt template based on signal_type
    - Invoke AI provider with formatted prompt
    - Parse AI response and validate JSON structure
    - _Requirements: 3.3, 3.4_
  
  - [x] 13.2 Implement evidence extraction

    - Implement _extract_evidence() method to extract block_heights and transaction_ids from signal metadata
    - _Requirements: 4.2_

- [x] 14. Implement Insight Persistence Module




  - [x] 14.1 Create InsightPersistenceModule class


    - Implement persist_insight() method to write to intel.insights table
    - Set chart_url to null initially
    - Return insight_id on success
    - _Requirements: 4.1, 4.3, 4.5_
  
  - [x] 14.2 Add error handling for persistence failures


    - Log errors with signal_id context
    - Mark signal as unprocessed for retry
    - _Requirements: 4.4_

- [x] 15. Create insight-generator service main application




  - [x] 15.1 Set up FastAPI application structure


    - Create main.py with FastAPI app initialization
    - Add health check endpoint
    - _Requirements: 3.1_
  
  - [x] 15.2 Implement polling loop

    - Create background task to poll for unprocessed signals every 10 seconds
    - Trigger insight generation for each signal group
    - Mark signals as processed after successful insight creation
    - _Requirements: 3.1, 3.2, 3.5_
  
  - [x] 15.3 Wire together all insight generation components

    - Initialize SignalPollingModule, InsightGenerationModule, InsightPersistenceModule
    - Connect AI provider based on configuration
    - Add correlation ID logging throughout
    - _Requirements: 5.2_

- [x] 16. Implement Error Handler




  - [x] 16.1 Create ErrorHandler class

    - Implement handle_processor_error() method with context logging
    - Implement retry_with_backoff() method with exponential backoff (max 3 attempts)
    - _Requirements: 6.1, 6.2_
  
  - [x] 16.2 Add alerting for stale signals

    - Emit alert to Cloud Monitoring if signals remain unprocessed >1 hour
    - _Requirements: 6.4_
  
  - [x] 16.3 Add correlation ID logging

    - Include correlation_id in all error log messages
    - _Requirements: 6.5_
-

- [ ] 17. Implement Monitoring Module



  - [x] 17.1 Create MonitoringModule class


    - Implement emit_pipeline_metrics() for timing metrics (signal_generation_duration_ms, total_pipeline_duration_ms)
    - Implement emit_signal_metrics() for signal counts by type and confidence bucket
    - Implement emit_insight_metrics() for insight counts by category and confidence bucket
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [x] 17.2 Add entity and error metrics

    - Implement emit_entity_metrics() for entity identification counts by entity_name
    - Implement emit_error_metrics() for error counts by error_type, service_name
    - _Requirements: 12.4, 12.5_
  
  - [x] 17.3 Add AI provider and backfill metrics

    - Implement emit_ai_provider_metrics() for latency by provider
    - Add counters for total_blocks_processed and total_insights_generated
    - _Requirements: 12.6, 12.7, 12.8_



- [x] 18. Implement Historical Backfill Module






  - [x] 18.1 Create HistoricalBackfillModule class


    - Implement backfill_date_range() method to query btc.blocks for historical blocks
    - Process blocks in chronological order
    - _Requirements: 11.1, 11.4_
  
  - [x] 18.2 Add historical context processing


    - Implement _get_historical_context() method to query surrounding blocks
    - Write signals with original block timestamps
    - Mark signals as processed=false for insight generation
    - _Requirements: 11.2, 11.3, 11.5_
  
  - [x] 18.3 Add rate limiting and selective backfill


    - Implement rate limiting (max 100 blocks per minute)
    - Support selective backfill by signal_types parameter
    - _Requirements: 11.6, 11.7_

-

- [x] 19. Populate known entities database







  - [x] 19.1 Create script to populate btc.known_entities table

    - Add exchange entities (Coinbase, Kraken, Binance, Gemini, Bitstamp) with known addresses
    - Add mining pool entities (Foundry USA, AntPool, F2Pool, ViaBTC, Binance Pool) with known addresses
    - Add treasury company entities (MicroStrategy/MSTR, Tesla/TSLA, Block/SQ, Marathon/MARA, Riot/RIOT) with known addresses and holdings metadata

    - _Requirements: 9.1, 9.2_

- [x] 20. Add environment variable configuration



  - [x] 20.1 Document all required environment variables

    - Signal processor toggles (MEMPOOL_PROCESSOR_ENABLED, EXCHANGE_PROCESSOR_ENABLED, etc.)
    - Thresholds (CONFIDENCE_THRESHOLD, WHALE_THRESHOLD_BTC)
    - Time windows (MEMPOOL_TIME_WINDOW, EXCHANGE_TIME_WINDOW, MINER_TIME_WINDOW)
    - AI provider settings (AI_PROVIDER, API keys, model names)
    - _Requirements: 7.1, 8.1_
  
  - [x] 20.2 Create .env.example files for both services

    - Create services/utxoiq-ingestion/.env.example
    - Create services/insight-generator/.env.example
    - _Requirements: 7.1, 8.1_

- [x] 21. Deploy services to Cloud Run






  - [x] 21.1 Create Dockerfile for utxoiq-ingestion service


    - Use Python 3.12 base image
    - Install dependencies from requirements.txt
    - Set up FastAPI with uvicorn
    - _Requirements: 5.5_
  
  - [x] 21.2 Create Dockerfile for insight-generator service


    - Use Python 3.12 base image
    - Install dependencies from requirements.txt
    - Set up FastAPI with uvicorn
    - _Requirements: 5.5_
  
  - [x] 21.3 Deploy both services to Cloud Run


    - Configure environment variables via Cloud Run
    - Set up Cloud Secret Manager for API keys
    - Configure auto-scaling and resource limits
    - _Requirements: 5.5_

- [ ] 22. End-to-end pipeline testing
  - [ ] 22.1 Test signal generation with mock block data
    - Verify all processors generate signals correctly
    - Verify signals are persisted to BigQuery
    - Verify correlation IDs are logged
    - _Requirements: 1.1, 1.3, 5.3_
  
  - [ ] 22.2 Test insight generation with real signals
    - Verify signals are polled correctly
    - Verify AI providers generate insights
    - Verify insights are persisted to BigQuery
    - Verify signals are marked as processed
    - _Requirements: 3.1, 3.4, 4.1, 3.5_
  
  - [ ] 22.3 Test complete pipeline end-to-end
    - Trigger pipeline with new block
    - Verify signals generated within 5 seconds
    - Verify insights generated within 60 seconds total
    - Verify all metrics are emitted to Cloud Monitoring
    - _Requirements: 5.1, 5.2, 5.5_
  
  - [ ] 22.4 Test error handling and resilience
    - Test processor failures don't block other processors
    - Test BigQuery write failures trigger retries
    - Test AI provider failures mark signals as unprocessed
    - Test stale signal alerting
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
