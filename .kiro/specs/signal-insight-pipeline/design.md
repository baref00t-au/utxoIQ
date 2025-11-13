# Design Document

## Overview

This design implements the end-to-end signal-to-insight pipeline that transforms Bitcoin blockchain data into actionable intelligence. The system connects three existing but isolated components: signal processors (compute blockchain metrics), BigQuery storage (persist data), and the insight generator (AI-powered analysis). The pipeline executes automatically when new blocks arrive, generating insights within 60 seconds.

The architecture follows a microservices pattern with clear separation between data ingestion (utxoiq-ingestion), signal computation, insight generation (insight-generator), and user-facing APIs (web-api). Services communicate via BigQuery tables and Cloud Pub/Sub for event-driven orchestration.

## Architecture

### System Components

```
┌─────────────────┐
│ Bitcoin Core    │
│ (RPC)           │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ utxoiq-ingestion Service                                │
│ ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐│
│ │Block Monitor│→ │Signal        │→ │Signal           ││
│ │             │  │Processors    │  │Persistence      ││
│ └─────────────┘  └──────────────┘  └─────────────────┘│
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ BigQuery: intel.signals                                 │
│ (signal_id, signal_type, block_height, confidence, ...) │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ insight-generator Service                               │
│ ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐│
│ │Signal       │→ │AI Provider   │→ │Insight          ││
│ │Polling      │  │Module        │  │Persistence      ││
│ └─────────────┘  └──────────────┘  └─────────────────┘│
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ BigQuery: intel.insights                                │
│ (insight_id, signal_id, category, headline, ...)        │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Block Detection**: Block Monitor detects new Bitcoin block via RPC polling
2. **Signal Generation**: Signal Processors analyze block data and compute signals
3. **Signal Persistence**: Signals written to BigQuery intel.signals table
4. **Signal Polling**: insight-generator queries for unprocessed signals
5. **Insight Generation**: AI Provider generates natural language insights
6. **Insight Persistence**: Insights written to BigQuery intel.insights table
7. **Signal Marking**: Source signals marked as processed

### Service Boundaries

**utxoiq-ingestion** (Python/FastAPI):
- Polls Bitcoin Core for new blocks
- Invokes signal processors
- Writes signals to BigQuery
- Handles blockchain data extraction

**insight-generator** (Python/FastAPI):
- Polls BigQuery for unprocessed signals
- Generates insights via AI providers
- Writes insights to BigQuery
- Marks signals as processed

**web-api** (Python/FastAPI):
- Serves insights to frontend via REST API
- Handles user authentication
- Manages alert configurations

## Components and Interfaces

### 1. Signal Persistence Module

**Location**: `services/utxoiq-ingestion/src/signal_persistence.py`

**Responsibilities**:
- Generate unique signal IDs (UUID format)
- Batch insert signals to BigQuery
- Handle persistence failures gracefully
- Log errors with correlation IDs

**Interface**:
```python
class SignalPersistenceModule:
    def __init__(self, bigquery_client: BigQueryClient):
        self.client = bigquery_client
        self.table_id = "intel.signals"
    
    async def persist_signals(
        self, 
        signals: List[Signal],
        correlation_id: str
    ) -> PersistenceResult:
        """
        Batch insert signals to BigQuery.
        Returns success/failure status with error details.
        """
        pass
    
    def generate_signal_id(self) -> str:
        """Generate UUID for signal identification."""
        return str(uuid.uuid4())
```

**Signal Schema** (BigQuery intel.signals):
```python
{
    "signal_id": "STRING",          # UUID
    "signal_type": "STRING",        # mempool|exchange|miner|whale|treasury|predictive
    "block_height": "INTEGER",
    "confidence": "FLOAT",          # 0.0 to 1.0
    "metadata": "JSON",             # Signal-specific data
    "created_at": "TIMESTAMP",
    "processed": "BOOLEAN",         # For insight generation tracking
    "processed_at": "TIMESTAMP"
}
```

### 2. Data Extraction Module

**Location**: `services/utxoiq-ingestion/src/data_extraction.py`

**Responsibilities**:
- Query Bitcoin Core RPC for mempool statistics
- Identify exchange addresses from known entities database
- Detect whale addresses (>1000 BTC)
- Track miner treasury addresses
- Query historical signal data from BigQuery

**Interface**:
```python
class DataExtractionModule:
    def __init__(
        self, 
        bitcoin_rpc: BitcoinRPC,
        bigquery_client: BigQueryClient
    ):
        self.rpc = bitcoin_rpc
        self.bq = bigquery_client
        self.known_entities = None  # Loaded on startup
    
    async def get_mempool_stats(self) -> MempoolStats:
        """Query Bitcoin Core for current mempool state."""
        pass
    
    async def identify_exchange_addresses(
        self, 
        addresses: List[str]
    ) -> Dict[str, EntityInfo]:
        """Match addresses against known entities database."""
        pass
    
    async def detect_whale_addresses(
        self, 
        outputs: List[TxOutput]
    ) -> List[WhaleAddress]:
        """Identify outputs to addresses with >1000 BTC balance."""
        pass
    
    async def get_historical_signals(
        self,
        signal_type: str,
        time_window: timedelta
    ) -> List[Signal]:
        """Query BigQuery for previous signal values."""
        pass
```

**Known Entities Schema** (BigQuery btc.known_entities):
```python
{
    "entity_id": "STRING",
    "entity_name": "STRING",        # "Coinbase", "Foundry USA", "MicroStrategy", etc.
    "entity_type": "STRING",        # "exchange" | "mining_pool" | "treasury"
    "addresses": "ARRAY<STRING>",
    "metadata": "JSON",             # For treasury: {"ticker": "MSTR", "known_holdings_btc": 152800}
    "updated_at": "TIMESTAMP"
}
```

### 3. Signal Processors

**Location**: `services/utxoiq-ingestion/src/processors/`

**Processor Types**:
- `mempool_processor.py` - Fee rate analysis
- `exchange_processor.py` - Exchange flow tracking
- `miner_processor.py` - Mining pool activity
- `whale_processor.py` - Large holder movements
- `treasury_processor.py` - Public company Bitcoin treasury movements
- `predictive_processor.py` - Fee forecasts and liquidity pressure

**Base Interface**:
```python
class SignalProcessor(ABC):
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.enabled = config.enabled
        self.confidence_threshold = config.confidence_threshold
    
    @abstractmethod
    async def process_block(
        self,
        block: BlockData,
        context: ProcessingContext
    ) -> List[Signal]:
        """
        Analyze block data and generate signals.
        Returns list of signals above confidence threshold.
        """
        pass
    
    def calculate_confidence(self, metrics: Dict) -> float:
        """Calculate confidence score (0.0 to 1.0)."""
        pass
```

**Signal Metadata Examples**:
```python
# Mempool Signal
{
    "fee_rate_median": 50.5,
    "fee_rate_change_pct": 25.3,
    "tx_count": 15000,
    "mempool_size_mb": 120.5,
    "comparison_window": "1h"
}

# Exchange Signal
{
    "entity_id": "coinbase_001",
    "entity_name": "Coinbase",
    "flow_type": "outflow",
    "amount_btc": 1250.5,
    "tx_count": 45,
    "addresses": ["bc1q...", "3FZbgi..."]
}

# Treasury Signal
{
    "entity_id": "microstrategy_001",
    "entity_name": "MicroStrategy",
    "company_ticker": "MSTR",
    "flow_type": "accumulation",
    "amount_btc": 500.0,
    "tx_count": 3,
    "addresses": ["bc1q...", "3FZbgi..."],
    "known_holdings_btc": 152800,
    "holdings_change_pct": 0.33
}

# Predictive Signal
{
    "prediction_type": "fee_forecast",
    "predicted_value": 55.2,
    "confidence_interval": [48.1, 62.3],
    "forecast_horizon": "1h",
    "model_version": "v1.2"
}
```


### 4. Signal Polling Module

**Location**: `services/insight-generator/src/signal_polling.py`

**Responsibilities**:
- Query BigQuery for unprocessed signals
- Filter by confidence threshold (≥0.7)
- Group signals by type and block height
- Mark signals as processed after insight generation

**Interface**:
```python
class SignalPollingModule:
    def __init__(self, bigquery_client: BigQueryClient):
        self.client = bigquery_client
        self.poll_interval = 10  # seconds
    
    async def poll_unprocessed_signals(self) -> List[SignalGroup]:
        """
        Query for signals where processed=false and confidence>=0.7.
        Returns signals grouped by signal_type and block_height.
        """
        pass
    
    async def mark_signal_processed(
        self,
        signal_id: str,
        processed_at: datetime
    ) -> bool:
        """Update signal record to mark as processed."""
        pass
```

**Query Pattern**:
```sql
SELECT *
FROM intel.signals
WHERE processed = false
  AND confidence >= 0.7
  AND signal_type IN ('mempool', 'exchange', 'miner', 'whale', 'treasury', 'predictive')
ORDER BY created_at ASC
LIMIT 100
```

### 5. AI Provider Module

**Location**: `services/insight-generator/src/ai_provider.py`

**Responsibilities**:
- Abstract interface for multiple AI providers
- Load provider configuration from environment
- Format prompts consistently across providers
- Parse and validate AI responses
- Handle provider failures gracefully

**Interface**:
```python
class AIProvider(ABC):
    @abstractmethod
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """Generate insight from signal using AI model."""
        pass

class VertexAIProvider(AIProvider):
    def __init__(self, project_id: str, location: str):
        self.client = aiplatform.gapic.PredictionServiceClient()
        self.model = "gemini-pro"
    
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """Use Vertex AI Gemini Pro for generation."""
        pass

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model  # "gpt-4-turbo"
    
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """Use OpenAI GPT for generation."""
        pass

class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model  # "claude-3-opus"
    
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """Use Anthropic Claude for generation."""
        pass

class GrokProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self.client = httpx.AsyncClient()
        self.api_key = api_key
        self.model = model  # "grok-beta"
    
    async def generate_insight(
        self,
        signal: Signal,
        prompt_template: str
    ) -> InsightContent:
        """Use xAI Grok for generation."""
        pass
```

**Provider Configuration** (Environment Variables):
```bash
AI_PROVIDER=vertex_ai  # vertex_ai|openai|anthropic|grok
VERTEX_AI_PROJECT=utxoiq-project
VERTEX_AI_LOCATION=us-central1
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229
GROK_API_KEY=xai-...
GROK_MODEL=grok-beta
```

**Prompt Templates** (`services/insight-generator/src/prompts/`):
```python
# mempool_prompt.py
MEMPOOL_TEMPLATE = """
You are a Bitcoin blockchain analyst. Generate a concise insight about this mempool signal.

Signal Data:
- Fee Rate: {fee_rate_median} sat/vB
- Change: {fee_rate_change_pct}% vs {comparison_window}
- Mempool Size: {mempool_size_mb} MB
- Transaction Count: {tx_count}

Provide:
1. Headline (max 80 chars)
2. Summary (2-3 sentences explaining why this matters)
3. Confidence Explanation (why this signal is reliable)

Format as JSON:
{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}
"""

# exchange_prompt.py
EXCHANGE_TEMPLATE = """
You are a Bitcoin blockchain analyst. Generate a concise insight about this exchange flow signal.

Signal Data:
- Exchange: {entity_name}
- Flow Type: {flow_type}
- Amount: {amount_btc} BTC
- Transaction Count: {tx_count}
- Block Height: {block_height}

Provide:
1. Headline (max 80 chars, mention exchange name)
2. Summary (2-3 sentences explaining market implications)
3. Confidence Explanation (why this signal is reliable)

Format as JSON:
{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}
"""

# treasury_prompt.py
TREASURY_TEMPLATE = """
You are a Bitcoin blockchain analyst. Generate a concise insight about this corporate treasury signal.

Signal Data:
- Company: {entity_name} ({company_ticker})
- Flow Type: {flow_type}
- Amount: {amount_btc} BTC
- Known Holdings: {known_holdings_btc} BTC
- Holdings Change: {holdings_change_pct}%
- Transaction Count: {tx_count}
- Block Height: {block_height}

Provide:
1. Headline (max 80 chars, mention company name and ticker)
2. Summary (2-3 sentences explaining corporate strategy implications and market impact)
3. Confidence Explanation (why this signal is reliable)

Format as JSON:
{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}
"""

# predictive_prompt.py
PREDICTIVE_TEMPLATE = """
You are a Bitcoin blockchain analyst. Generate a forward-looking insight about this predictive signal.

Signal Data:
- Prediction Type: {prediction_type}
- Predicted Value: {predicted_value}
- Confidence Interval: {confidence_interval}
- Forecast Horizon: {forecast_horizon}
- Current Value: {current_value}

Provide:
1. Headline (max 80 chars, emphasize forward-looking nature)
2. Summary (2-3 sentences explaining what to expect and why)
3. Confidence Explanation (model reliability and data quality)

Format as JSON:
{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}
"""
```

### 6. Insight Generation Module

**Location**: `services/insight-generator/src/insight_generation.py`

**Responsibilities**:
- Select appropriate prompt template based on signal type
- Invoke AI provider with formatted prompt
- Parse AI response and validate structure
- Extract blockchain evidence from signal metadata
- Create insight records with all required fields

**Interface**:
```python
class InsightGenerationModule:
    def __init__(
        self,
        ai_provider: AIProvider,
        prompt_loader: PromptLoader
    ):
        self.ai_provider = ai_provider
        self.prompts = prompt_loader
    
    async def generate_insight(
        self,
        signal: Signal
    ) -> Insight:
        """
        Generate insight from signal using AI provider.
        Returns complete insight record ready for persistence.
        """
        # Select prompt template
        template = self.prompts.get_template(signal.signal_type)
        
        # Generate content via AI
        content = await self.ai_provider.generate_insight(
            signal, template
        )
        
        # Extract evidence from signal metadata
        evidence = self._extract_evidence(signal)
        
        # Create insight record
        return Insight(
            insight_id=str(uuid.uuid4()),
            signal_id=signal.signal_id,
            category=signal.signal_type,
            headline=content.headline,
            summary=content.summary,
            confidence=signal.confidence,
            evidence=evidence,
            created_at=datetime.utcnow()
        )
    
    def _extract_evidence(self, signal: Signal) -> Evidence:
        """Extract block heights and tx IDs from signal metadata."""
        return Evidence(
            block_heights=[signal.block_height],
            transaction_ids=signal.metadata.get("tx_ids", [])
        )
```

### 7. Insight Persistence Module

**Location**: `services/insight-generator/src/insight_persistence.py`

**Responsibilities**:
- Write insights to BigQuery intel.insights table
- Handle persistence failures with retry logic
- Return insight_id for reference
- Set chart_url to null for later population

**Interface**:
```python
class InsightPersistenceModule:
    def __init__(self, bigquery_client: BigQueryClient):
        self.client = bigquery_client
        self.table_id = "intel.insights"
    
    async def persist_insight(
        self,
        insight: Insight,
        correlation_id: str
    ) -> PersistenceResult:
        """
        Write insight to BigQuery.
        Returns insight_id on success or error details on failure.
        """
        pass
```

**Insight Schema** (BigQuery intel.insights):
```python
{
    "insight_id": "STRING",         # UUID
    "signal_id": "STRING",          # Reference to source signal
    "category": "STRING",           # mempool|exchange|miner|whale|treasury|predictive
    "headline": "STRING",           # Max 80 chars
    "summary": "STRING",            # 2-3 sentences
    "confidence": "FLOAT",          # Inherited from signal
    "evidence": {
        "block_heights": "ARRAY<INTEGER>",
        "transaction_ids": "ARRAY<STRING>"
    },
    "chart_url": "STRING",          # Null initially, populated by chart-renderer
    "created_at": "TIMESTAMP"
}
```

### 8. Entity Identification Module

**Location**: `services/utxoiq-ingestion/src/entity_identification.py`

**Responsibilities**:
- Load known entities database on startup
- Match transaction addresses against entity database
- Identify exchanges (Coinbase, Kraken, Binance, etc.)
- Identify mining pools (Foundry USA, AntPool, F2Pool, etc.)
- Reload entity list periodically (every 5 minutes)

**Interface**:
```python
class EntityIdentificationModule:
    def __init__(self, bigquery_client: BigQueryClient):
        self.client = bigquery_client
        self.entities_cache = {}
        self.last_reload = None
        self.reload_interval = timedelta(minutes=5)
    
    async def load_known_entities(self) -> None:
        """Load entities from btc.known_entities table."""
        pass
    
    async def identify_entity(
        self,
        address: str
    ) -> Optional[EntityInfo]:
        """
        Match address against known entities.
        Returns entity info or None if unknown.
        """
        if self._should_reload():
            await self.load_known_entities()
        
        return self.entities_cache.get(address)
    
    async def identify_mining_pool(
        self,
        coinbase_tx: Transaction
    ) -> Optional[EntityInfo]:
        """Extract mining pool from coinbase transaction."""
        pass
    
    async def identify_treasury_company(
        self,
        address: str
    ) -> Optional[EntityInfo]:
        """
        Identify if address belongs to a public company treasury.
        Returns entity info with company ticker and known holdings.
        """
        entity = await self.identify_entity(address)
        if entity and entity.entity_type == "treasury":
            return entity
        return None
```

### 9. Predictive Analytics Module

**Location**: `services/utxoiq-ingestion/src/predictive_analytics.py`

**Responsibilities**:
- Generate fee forecast signals using exponential smoothing
- Generate liquidity pressure signals using z-score normalization
- Include prediction metadata (confidence interval, horizon, model version)
- Filter low-confidence predictions (<0.5)

**Interface**:
```python
class PredictiveAnalyticsModule:
    def __init__(self, bigquery_client: BigQueryClient):
        self.client = bigquery_client
        self.fee_model = ExponentialSmoothingModel()
        self.liquidity_model = ZScoreModel()
    
    async def generate_fee_forecast(
        self,
        current_mempool: MempoolStats,
        historical_data: List[MempoolStats]
    ) -> Optional[Signal]:
        """
        Predict future fee rates using exponential smoothing.
        Returns signal if confidence >= 0.5, else None.
        """
        pass
    
    async def generate_liquidity_pressure(
        self,
        exchange_flows: List[ExchangeFlow],
        historical_flows: List[ExchangeFlow]
    ) -> Optional[Signal]:
        """
        Predict liquidity pressure using z-score normalization.
        Returns signal if confidence >= 0.5, else None.
        """
        pass
```

**Predictive Signal Metadata**:
```python
{
    "prediction_type": "fee_forecast",  # or "liquidity_pressure"
    "predicted_value": 55.2,
    "confidence_interval": [48.1, 62.3],
    "forecast_horizon": "1h",
    "model_version": "v1.2",
    "current_value": 50.5,
    "historical_mean": 48.3,
    "historical_std": 5.2
}
```


### 10. Pipeline Orchestrator

**Location**: `services/utxoiq-ingestion/src/pipeline_orchestrator.py`

**Responsibilities**:
- Trigger signal generation within 5 seconds of block detection
- Trigger insight generation within 10 seconds of signal completion
- Log timing metrics for each stage with correlation IDs
- Handle failures without blocking subsequent blocks
- Emit success metrics to Cloud Monitoring

**Interface**:
```python
class PipelineOrchestrator:
    def __init__(
        self,
        signal_processors: List[SignalProcessor],
        signal_persistence: SignalPersistenceModule,
        monitoring: MonitoringModule
    ):
        self.processors = signal_processors
        self.persistence = signal_persistence
        self.monitoring = monitoring
    
    async def process_new_block(
        self,
        block: BlockData
    ) -> PipelineResult:
        """
        Execute complete pipeline for new block.
        Returns timing metrics and success/failure status.
        """
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Stage 1: Signal Generation
            signals = await self._generate_signals(block, correlation_id)
            signal_time = time.time() - start_time
            
            # Stage 2: Signal Persistence
            await self.persistence.persist_signals(signals, correlation_id)
            persist_time = time.time() - start_time - signal_time
            
            # Emit metrics
            await self.monitoring.emit_pipeline_metrics(
                correlation_id=correlation_id,
                block_height=block.height,
                signal_count=len(signals),
                signal_generation_ms=signal_time * 1000,
                signal_persistence_ms=persist_time * 1000,
                total_duration_ms=(time.time() - start_time) * 1000
            )
            
            return PipelineResult(success=True, signals=signals)
            
        except Exception as e:
            logger.error(
                f"Pipeline failed for block {block.height}",
                extra={"correlation_id": correlation_id, "error": str(e)}
            )
            return PipelineResult(success=False, error=str(e))
    
    async def _generate_signals(
        self,
        block: BlockData,
        correlation_id: str
    ) -> List[Signal]:
        """Run all enabled signal processors."""
        signals = []
        for processor in self.processors:
            if not processor.enabled:
                continue
            
            try:
                processor_signals = await processor.process_block(block)
                signals.extend(processor_signals)
            except Exception as e:
                logger.error(
                    f"Processor {processor.__class__.__name__} failed",
                    extra={
                        "correlation_id": correlation_id,
                        "block_height": block.height,
                        "error": str(e)
                    }
                )
        
        return signals
```

### 11. Configuration Module

**Location**: `services/utxoiq-ingestion/src/config.py`

**Responsibilities**:
- Load signal processor settings from environment variables
- Enable/disable processors dynamically
- Configure confidence thresholds
- Support hot-reload without service restart (poll every 5 minutes)

**Interface**:
```python
class ConfigurationModule:
    def __init__(self):
        self.config = self._load_config()
        self.last_reload = datetime.utcnow()
        self.reload_interval = timedelta(minutes=5)
    
    def _load_config(self) -> ProcessorConfig:
        """Load configuration from environment variables."""
        return ProcessorConfig(
            mempool_enabled=os.getenv("MEMPOOL_PROCESSOR_ENABLED", "true") == "true",
            exchange_enabled=os.getenv("EXCHANGE_PROCESSOR_ENABLED", "true") == "true",
            miner_enabled=os.getenv("MINER_PROCESSOR_ENABLED", "true") == "true",
            whale_enabled=os.getenv("WHALE_PROCESSOR_ENABLED", "true") == "true",
            treasury_enabled=os.getenv("TREASURY_PROCESSOR_ENABLED", "true") == "true",
            predictive_enabled=os.getenv("PREDICTIVE_PROCESSOR_ENABLED", "true") == "true",
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.7")),
            mempool_time_window=os.getenv("MEMPOOL_TIME_WINDOW", "1h"),
            exchange_time_window=os.getenv("EXCHANGE_TIME_WINDOW", "24h")
        )
    
    def should_reload(self) -> bool:
        """Check if config should be reloaded."""
        return datetime.utcnow() - self.last_reload > self.reload_interval
    
    def reload_config(self) -> None:
        """Hot-reload configuration from environment."""
        self.config = self._load_config()
        self.last_reload = datetime.utcnow()
        logger.info("Configuration reloaded", extra={"config": self.config})
```

**Environment Variables**:
```bash
# Signal Processor Toggles
MEMPOOL_PROCESSOR_ENABLED=true
EXCHANGE_PROCESSOR_ENABLED=true
MINER_PROCESSOR_ENABLED=true
WHALE_PROCESSOR_ENABLED=true
TREASURY_PROCESSOR_ENABLED=true
PREDICTIVE_PROCESSOR_ENABLED=true

# Thresholds
CONFIDENCE_THRESHOLD=0.7
WHALE_THRESHOLD_BTC=1000

# Time Windows
MEMPOOL_TIME_WINDOW=1h
EXCHANGE_TIME_WINDOW=24h
MINER_TIME_WINDOW=7d

# AI Provider
AI_PROVIDER=vertex_ai
VERTEX_AI_PROJECT=utxoiq-project
VERTEX_AI_LOCATION=us-central1
```

### 12. Error Handler

**Location**: `services/utxoiq-ingestion/src/error_handler.py`

**Responsibilities**:
- Log errors with context (block_height, signal_type, correlation_id)
- Implement exponential backoff retry (max 3 attempts)
- Emit alerts for signals unprocessed >1 hour
- Include correlation IDs in all log messages

**Interface**:
```python
class ErrorHandler:
    def __init__(self, monitoring: MonitoringModule):
        self.monitoring = monitoring
        self.max_retries = 3
        self.base_delay = 1  # seconds
    
    async def handle_processor_error(
        self,
        error: Exception,
        processor_name: str,
        block_height: int,
        correlation_id: str
    ) -> None:
        """Log processor error and continue processing."""
        logger.error(
            f"Signal processor failed: {processor_name}",
            extra={
                "correlation_id": correlation_id,
                "block_height": block_height,
                "processor": processor_name,
                "error": str(error),
                "error_type": type(error).__name__
            }
        )
        
        await self.monitoring.emit_error_metric(
            error_type="processor_failure",
            service_name="utxoiq-ingestion",
            processor=processor_name
        )
    
    async def retry_with_backoff(
        self,
        operation: Callable,
        operation_name: str,
        correlation_id: str
    ) -> Any:
        """Execute operation with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return await operation()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"Operation failed after {self.max_retries} attempts",
                        extra={
                            "correlation_id": correlation_id,
                            "operation": operation_name,
                            "error": str(e)
                        }
                    )
                    raise
                
                delay = self.base_delay * (2 ** attempt)
                logger.warning(
                    f"Operation failed, retrying in {delay}s",
                    extra={
                        "correlation_id": correlation_id,
                        "operation": operation_name,
                        "attempt": attempt + 1,
                        "error": str(e)
                    }
                )
                await asyncio.sleep(delay)
```

### 13. Historical Backfill Module

**Location**: `services/utxoiq-ingestion/src/historical_backfill.py`

**Responsibilities**:
- Query btc.blocks for historical blocks in date range
- Process blocks in chronological order
- Write signals with original block timestamps
- Mark signals as unprocessed for insight generation
- Implement rate limiting (max 100 blocks/minute)
- Support selective backfill by signal type or date range

**Interface**:
```python
class HistoricalBackfillModule:
    def __init__(
        self,
        bigquery_client: BigQueryClient,
        signal_processors: List[SignalProcessor],
        signal_persistence: SignalPersistenceModule
    ):
        self.client = bigquery_client
        self.processors = signal_processors
        self.persistence = signal_persistence
        self.rate_limit = 100  # blocks per minute
    
    async def backfill_date_range(
        self,
        start_date: date,
        end_date: date,
        signal_types: Optional[List[str]] = None
    ) -> BackfillResult:
        """
        Backfill signals for historical blocks in date range.
        Optionally filter by signal types.
        """
        # Query historical blocks
        blocks = await self._query_historical_blocks(start_date, end_date)
        
        # Process blocks with rate limiting
        total_signals = 0
        for block in blocks:
            signals = await self._process_historical_block(
                block, signal_types
            )
            total_signals += len(signals)
            
            # Rate limiting
            await asyncio.sleep(60 / self.rate_limit)
        
        return BackfillResult(
            blocks_processed=len(blocks),
            signals_generated=total_signals,
            start_date=start_date,
            end_date=end_date
        )
    
    async def _process_historical_block(
        self,
        block: BlockData,
        signal_types: Optional[List[str]]
    ) -> List[Signal]:
        """Process historical block with temporal context."""
        # Get surrounding blocks for context
        context = await self._get_historical_context(block)
        
        # Run processors
        signals = []
        for processor in self.processors:
            if signal_types and processor.signal_type not in signal_types:
                continue
            
            processor_signals = await processor.process_block(block, context)
            signals.extend(processor_signals)
        
        # Persist with original timestamp
        await self.persistence.persist_signals(signals, correlation_id="backfill")
        
        return signals
```

### 14. Treasury Processor

**Location**: `services/utxoiq-ingestion/src/processors/treasury_processor.py`

**Responsibilities**:
- Identify transactions involving public company treasury addresses
- Track accumulation and distribution patterns
- Calculate holdings changes relative to known positions
- Generate signals for significant treasury movements

**Interface**:
```python
class TreasuryProcessor(SignalProcessor):
    def __init__(
        self,
        config: ProcessorConfig,
        entity_module: EntityIdentificationModule
    ):
        super().__init__(config)
        self.entity_module = entity_module
        self.signal_type = "treasury"
    
    async def process_block(
        self,
        block: BlockData,
        context: ProcessingContext
    ) -> List[Signal]:
        """
        Analyze block for public company treasury movements.
        Returns treasury signals above confidence threshold.
        """
        signals = []
        
        # Scan all transactions for treasury addresses
        for tx in block.transactions:
            treasury_flows = await self._identify_treasury_flows(tx)
            
            for flow in treasury_flows:
                # Calculate confidence based on amount and entity reputation
                confidence = self._calculate_confidence(flow)
                
                if confidence >= self.config.confidence_threshold:
                    signal = Signal(
                        signal_id=str(uuid.uuid4()),
                        signal_type=self.signal_type,
                        block_height=block.height,
                        confidence=confidence,
                        metadata={
                            "entity_id": flow.entity.entity_id,
                            "entity_name": flow.entity.entity_name,
                            "company_ticker": flow.entity.metadata["ticker"],
                            "flow_type": flow.flow_type,  # accumulation|distribution
                            "amount_btc": flow.amount_btc,
                            "tx_count": 1,
                            "addresses": flow.addresses,
                            "known_holdings_btc": flow.entity.metadata["known_holdings_btc"],
                            "holdings_change_pct": self._calculate_holdings_change(
                                flow.amount_btc,
                                flow.entity.metadata["known_holdings_btc"]
                            )
                        },
                        created_at=datetime.utcnow()
                    )
                    signals.append(signal)
        
        return signals
    
    async def _identify_treasury_flows(
        self,
        tx: Transaction
    ) -> List[TreasuryFlow]:
        """Identify treasury company involvement in transaction."""
        flows = []
        
        # Check inputs for treasury addresses (distribution)
        for input_addr in tx.input_addresses:
            entity = await self.entity_module.identify_treasury_company(input_addr)
            if entity:
                flows.append(TreasuryFlow(
                    entity=entity,
                    flow_type="distribution",
                    amount_btc=tx.output_sum_btc,
                    addresses=[input_addr]
                ))
        
        # Check outputs for treasury addresses (accumulation)
        for output in tx.outputs:
            entity = await self.entity_module.identify_treasury_company(output.address)
            if entity:
                flows.append(TreasuryFlow(
                    entity=entity,
                    flow_type="accumulation",
                    amount_btc=output.value_btc,
                    addresses=[output.address]
                ))
        
        return flows
    
    def _calculate_confidence(self, flow: TreasuryFlow) -> float:
        """
        Calculate confidence based on:
        - Amount significance (larger = higher confidence)
        - Entity reputation (known companies = higher confidence)
        - Address confirmation (multiple sources = higher confidence)
        """
        # Base confidence from entity reputation
        confidence = 0.7
        
        # Boost for significant amounts (>100 BTC)
        if flow.amount_btc > 100:
            confidence += 0.1
        
        # Boost for very large amounts (>500 BTC)
        if flow.amount_btc > 500:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_holdings_change(
        self,
        amount_btc: float,
        known_holdings_btc: float
    ) -> float:
        """Calculate percentage change in holdings."""
        if known_holdings_btc == 0:
            return 0.0
        return (amount_btc / known_holdings_btc) * 100
```

**Treasury Companies to Track**:
- **MicroStrategy (MSTR)**: ~152,800 BTC (as of 2024)
- **Tesla (TSLA)**: ~9,720 BTC
- **Block (SQ)**: ~8,027 BTC
- **Marathon Digital (MARA)**: ~26,842 BTC
- **Riot Platforms (RIOT)**: ~9,334 BTC
- **Coinbase (COIN)**: ~9,000 BTC (corporate holdings)
- **Galaxy Digital (GLXY)**: ~15,449 BTC
- **Hut 8 Mining (HUT)**: ~9,102 BTC

**Signal Confidence Factors**:
- Amount >500 BTC: High confidence (0.9+)
- Amount 100-500 BTC: Medium-high confidence (0.8)
- Amount <100 BTC: Medium confidence (0.7)
- Known company with public disclosures: +0.1 confidence
- Multiple address confirmations: +0.05 confidence

### 15. Monitoring Module

**Location**: `services/utxoiq-ingestion/src/monitoring.py`

**Responsibilities**:
- Emit timing metrics to Cloud Monitoring
- Track signal counts by type and confidence bucket
- Track insight counts by category
- Track entity identification counts
- Track error counts by type and service
- Track AI provider latency by provider

**Interface**:
```python
class MonitoringModule:
    def __init__(self, monitoring_client: MonitoringClient):
        self.client = monitoring_client
        self.project_id = os.getenv("GCP_PROJECT_ID")
    
    async def emit_pipeline_metrics(
        self,
        correlation_id: str,
        block_height: int,
        signal_count: int,
        signal_generation_ms: float,
        signal_persistence_ms: float,
        total_duration_ms: float
    ) -> None:
        """Emit pipeline timing metrics."""
        metrics = [
            ("signal_generation_duration_ms", signal_generation_ms),
            ("signal_persistence_duration_ms", signal_persistence_ms),
            ("total_pipeline_duration_ms", total_duration_ms),
            ("signals_generated", signal_count)
        ]
        
        for metric_name, value in metrics:
            await self._write_metric(
                metric_name,
                value,
                labels={
                    "correlation_id": correlation_id,
                    "block_height": str(block_height)
                }
            )
    
    async def emit_signal_metrics(
        self,
        signal_type: str,
        confidence: float
    ) -> None:
        """Emit signal count metrics by type and confidence bucket."""
        confidence_bucket = self._get_confidence_bucket(confidence)
        
        await self._write_metric(
            "signals_by_type",
            1,
            labels={
                "signal_type": signal_type,
                "confidence_bucket": confidence_bucket
            }
        )
    
    async def emit_insight_metrics(
        self,
        category: str,
        confidence: float,
        generation_ms: float
    ) -> None:
        """Emit insight generation metrics."""
        confidence_bucket = self._get_confidence_bucket(confidence)
        
        await self._write_metric(
            "insight_generation_duration_ms",
            generation_ms,
            labels={"category": category}
        )
        
        await self._write_metric(
            "insights_by_category",
            1,
            labels={
                "category": category,
                "confidence_bucket": confidence_bucket
            }
        )
    
    async def emit_ai_provider_metrics(
        self,
        provider: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """Emit AI provider performance metrics."""
        await self._write_metric(
            "ai_provider_latency_ms",
            latency_ms,
            labels={
                "provider": provider,
                "success": str(success)
            }
        )
    
    def _get_confidence_bucket(self, confidence: float) -> str:
        """Categorize confidence into buckets."""
        if confidence >= 0.85:
            return "high"
        elif confidence >= 0.7:
            return "medium"
        else:
            return "low"
```

## Data Models

### Signal Model
```python
@dataclass
class Signal:
    signal_id: str
    signal_type: str  # mempool|exchange|miner|whale|treasury|predictive
    block_height: int
    confidence: float
    metadata: Dict[str, Any]
    created_at: datetime
    processed: bool = False
    processed_at: Optional[datetime] = None
```

### Insight Model
```python
@dataclass
class Insight:
    insight_id: str
    signal_id: str
    category: str  # mempool|exchange|miner|whale|treasury|predictive
    headline: str
    summary: str
    confidence: float
    evidence: Evidence
    chart_url: Optional[str] = None
    created_at: datetime

@dataclass
class Evidence:
    block_heights: List[int]
    transaction_ids: List[str]
```

### Entity Model
```python
@dataclass
class EntityInfo:
    entity_id: str
    entity_name: str
    entity_type: str  # exchange|mining_pool|treasury
    addresses: List[str]
    metadata: Dict[str, Any]  # For treasury: {"ticker": "MSTR", "known_holdings_btc": 152800}
```


## Error Handling

### Error Categories

**1. Signal Processing Errors**
- **Cause**: Bitcoin RPC failures, invalid block data, processor exceptions
- **Handling**: Log error with context, skip failed processor, continue with other processors
- **Recovery**: Processor failures don't block other signal types
- **Alerting**: Emit error metric to Cloud Monitoring

**2. BigQuery Write Errors**
- **Cause**: Network issues, quota limits, schema validation failures
- **Handling**: Exponential backoff retry (max 3 attempts)
- **Recovery**: If all retries fail, log error and continue processing next block
- **Alerting**: Alert if write failures exceed threshold (>5% of operations)

**3. AI Provider Errors**
- **Cause**: API rate limits, model failures, timeout errors
- **Handling**: Log error, mark signal as unprocessed for retry
- **Recovery**: Signal remains in queue for next polling cycle
- **Alerting**: Alert if unprocessed signals exceed 1 hour age

**4. Entity Identification Errors**
- **Cause**: Database query failures, cache corruption
- **Handling**: Label entity as "unknown", continue processing
- **Recovery**: Reload entity cache on next scheduled refresh
- **Alerting**: Log warning but don't block pipeline

### Error Response Patterns

**Graceful Degradation**:
- Signal processor failures don't block other processors
- AI provider failures don't block signal generation
- Entity identification failures default to "unknown"
- Chart rendering failures leave chart_url as null

**Retry Strategies**:
- BigQuery writes: Exponential backoff (1s, 2s, 4s)
- AI provider calls: Mark unprocessed, retry on next poll
- Entity cache reload: Automatic every 5 minutes
- Configuration reload: Automatic every 5 minutes

**Correlation IDs**:
- Every pipeline execution gets unique correlation_id
- All log messages include correlation_id
- Enables request tracing across services
- Format: UUID v4

### Logging Standards

```python
# Structured logging with correlation IDs
logger.info(
    "Signal generation completed",
    extra={
        "correlation_id": correlation_id,
        "block_height": block_height,
        "signal_count": len(signals),
        "duration_ms": duration
    }
)

logger.error(
    "BigQuery write failed",
    extra={
        "correlation_id": correlation_id,
        "table_id": table_id,
        "error": str(error),
        "retry_attempt": attempt
    }
)
```

## Testing Strategy

### Unit Tests

**Signal Processors** (`tests/test_processors.py`):
- Test signal calculation logic with mock block data
- Verify confidence score computation
- Test threshold filtering
- Validate metadata structure

**Data Extraction** (`tests/test_data_extraction.py`):
- Mock Bitcoin RPC responses
- Test entity identification with known addresses
- Test whale detection logic
- Verify historical query construction

**AI Provider** (`tests/test_ai_provider.py`):
- Mock AI provider responses
- Test prompt formatting
- Verify response parsing
- Test error handling for each provider

**Persistence Modules** (`tests/test_persistence.py`):
- Mock BigQuery client
- Test batch insert logic
- Verify retry behavior
- Test error handling

### Integration Tests

**End-to-End Pipeline** (`tests/integration/test_pipeline.py`):
- Use BigQuery emulator for local testing
- Mock Bitcoin Core RPC with test blocks
- Mock AI provider with deterministic responses
- Verify complete flow: block → signals → insights

**BigQuery Operations** (`tests/integration/test_bigquery.py`):
- Test actual BigQuery writes (dev environment)
- Verify schema compatibility
- Test query performance
- Validate partitioning and clustering

**AI Provider Integration** (`tests/integration/test_ai_providers.py`):
- Test each provider with real API calls (dev environment)
- Verify response format consistency
- Test error handling with invalid inputs
- Measure latency for each provider

### Performance Tests

**Signal Generation Latency**:
- Target: <5 seconds from block detection to signal persistence
- Test with various block sizes and transaction counts
- Measure each processor independently

**Insight Generation Latency**:
- Target: <10 seconds from signal creation to insight persistence
- Test with different AI providers
- Measure prompt formatting, API call, and persistence separately

**Backfill Performance**:
- Target: 100 blocks per minute
- Test rate limiting implementation
- Verify no data loss during high-volume processing

### Test Data

**Mock Blocks**:
- Small block (500 transactions)
- Large block (3000 transactions)
- Block with known exchange addresses
- Block with whale transactions
- Block with mining pool coinbase

**Mock Signals**:
- High confidence mempool signal (0.9)
- Medium confidence exchange signal (0.75)
- Low confidence whale signal (0.65)
- Predictive signal with confidence interval

**Mock AI Responses**:
- Valid JSON response
- Invalid JSON (test error handling)
- Timeout simulation
- Rate limit error

## Design Decisions and Rationales

### 1. BigQuery as Signal Storage

**Decision**: Use BigQuery intel.signals table instead of Cloud SQL or Pub/Sub.

**Rationale**:
- Signals are append-only, no updates needed (perfect for BigQuery)
- Historical analysis requires time-series queries (BigQuery strength)
- Integration with existing btc.blocks dataset
- Cost-effective for high-volume writes
- Native support for JSON metadata fields

**Trade-offs**:
- Eventual consistency (acceptable for 60-second SLA)
- No real-time updates (polling required)
- Higher latency than Pub/Sub (acceptable for use case)

### 2. Polling vs. Pub/Sub for Insight Generation

**Decision**: insight-generator polls BigQuery for unprocessed signals instead of Pub/Sub events.

**Rationale**:
- Simpler architecture (no event broker)
- Natural batching (process multiple signals per poll)
- Easier retry logic (signals remain in table until processed)
- No message loss risk (durable storage)
- Easier debugging (query signals directly)

**Trade-offs**:
- Higher latency (10-second poll interval)
- More BigQuery queries (acceptable cost)
- Less real-time than Pub/Sub (acceptable for 60-second SLA)

### 3. Multiple AI Provider Support

**Decision**: Abstract AI provider interface supporting Vertex AI, OpenAI, Anthropic, and xAI Grok.

**Rationale**:
- Vendor flexibility (avoid lock-in)
- Cost optimization (switch to cheaper provider)
- Redundancy (fallback if primary fails)
- A/B testing (compare quality across providers)
- Regional availability (some providers not in all regions)

**Trade-offs**:
- More complex implementation
- Need to maintain multiple API integrations
- Prompt engineering must work across providers

### 4. Confidence Threshold Filtering

**Decision**: Only process signals with confidence ≥0.7 for insight generation.

**Rationale**:
- Reduce AI costs (skip low-quality signals)
- Improve user experience (only show reliable insights)
- Reduce noise in insight feed
- Configurable threshold for tuning

**Trade-offs**:
- May miss interesting low-confidence signals
- Threshold is somewhat arbitrary
- Requires good confidence scoring in processors

### 5. Entity Database in BigQuery

**Decision**: Store known entities (exchanges, mining pools) in BigQuery btc.known_entities table.

**Rationale**:
- Centralized entity management
- Easy updates without code changes
- Queryable for analytics
- Cached in memory for performance
- Supports historical entity tracking

**Trade-offs**:
- Requires cache reload mechanism
- 5-minute cache delay for updates
- More complex than hardcoded lists

### 6. Predictive Signals as Separate Type

**Decision**: Treat predictive signals as distinct signal_type with special metadata.

**Rationale**:
- Clear separation of observations vs. predictions
- Different prompt templates for forward-looking insights
- Allows filtering predictive vs. observational insights
- Supports model versioning and A/B testing

**Trade-offs**:
- More complex signal schema
- Need separate prompt templates
- Requires model maintenance

### 7. Historical Backfill Rate Limiting

**Decision**: Limit backfill to 100 blocks per minute.

**Rationale**:
- Avoid overwhelming Bitcoin Core RPC
- Prevent BigQuery quota exhaustion
- Reduce AI provider costs during backfill
- Allow graceful degradation under load

**Trade-offs**:
- Slower backfill (30 days = ~4 hours)
- May need manual intervention for large backfills
- Rate limit may be too conservative

### 8. Correlation IDs for Request Tracing

**Decision**: Generate UUID correlation_id for each block processing run.

**Rationale**:
- Enables distributed tracing across services
- Simplifies debugging (grep logs by correlation_id)
- Supports performance analysis
- Industry standard practice

**Trade-offs**:
- Adds overhead to every log message
- Requires discipline to include in all logs
- UUID format may be overkill

### 9. Chart URL Populated Later

**Decision**: Set chart_url to null initially, populate by chart-renderer service later.

**Rationale**:
- Decouples insight generation from chart rendering
- Chart rendering is slower (can be async)
- Allows insights to be visible before charts ready
- Supports chart regeneration without insight changes

**Trade-offs**:
- Insights initially incomplete
- Requires separate chart rendering pipeline
- More complex frontend logic (handle null charts)

### 10. Hot-Reload Configuration

**Decision**: Poll environment variables every 5 minutes for configuration changes.

**Rationale**:
- Enable/disable processors without restart
- Tune thresholds in production
- Faster iteration during development
- Reduces deployment frequency

**Trade-offs**:
- 5-minute delay for config changes
- More complex configuration management
- Potential for inconsistent state during reload

## Performance Considerations

### Latency Targets

- **Block Detection → Signal Persistence**: <5 seconds
- **Signal Creation → Insight Generation**: <10 seconds
- **Total Pipeline (Block → Insight)**: <60 seconds
- **AI Provider API Call**: <3 seconds (per provider)
- **BigQuery Write (batch)**: <1 second

### Throughput Targets

- **Blocks Processed**: 1 block every ~10 minutes (Bitcoin block time)
- **Signals per Block**: 5-10 signals (varies by block content)
- **Insights per Block**: 3-7 insights (filtered by confidence)
- **Historical Backfill**: 100 blocks per minute

### Optimization Strategies

**1. Batch BigQuery Writes**:
- Collect all signals from a block
- Single batch insert instead of individual writes
- Reduces API calls and latency

**2. Parallel Signal Processing**:
- Run signal processors concurrently (asyncio)
- Each processor independent
- Reduces total processing time

**3. Entity Cache**:
- Load known entities once on startup
- Cache in memory for fast lookups
- Reload every 5 minutes (background task)

**4. Connection Pooling**:
- Reuse BigQuery client connections
- Reuse Bitcoin RPC connections
- Reduces connection overhead

**5. Async I/O**:
- Use asyncio for all I/O operations
- Non-blocking Bitcoin RPC calls
- Non-blocking BigQuery queries
- Non-blocking AI provider calls

### Scalability Considerations

**Horizontal Scaling**:
- utxoiq-ingestion: Single instance (block processing is sequential)
- insight-generator: Multiple instances (poll different signal batches)
- web-api: Multiple instances (stateless API)

**BigQuery Partitioning**:
- Partition intel.signals by created_at (daily)
- Partition intel.insights by created_at (daily)
- Improves query performance for time-range queries

**Rate Limiting**:
- Bitcoin Core RPC: Respect node limits
- AI Provider APIs: Stay within quota
- BigQuery: Batch writes to reduce API calls

## Security Considerations

### API Key Management

- Store AI provider API keys in Cloud Secret Manager
- Rotate keys regularly (quarterly)
- Use separate keys for dev/staging/prod
- Never log API keys

### Data Privacy

- No PII in signals or insights
- Bitcoin addresses are public data
- Transaction IDs are public data
- No user-specific data in pipeline

### Access Control

- BigQuery datasets: IAM roles for service accounts
- Cloud Secret Manager: Least privilege access
- Bitcoin Core RPC: Authenticated connections only
- AI Provider APIs: API key authentication

### Audit Logging

- Log all BigQuery writes
- Log all AI provider calls
- Log all configuration changes
- Include correlation IDs for tracing

## Deployment Strategy

### Service Deployment

**utxoiq-ingestion**:
- Deploy to Cloud Run (single instance)
- Environment: Python 3.12, FastAPI
- Resources: 2 CPU, 4GB RAM
- Timeout: 300 seconds (5 minutes)

**insight-generator**:
- Deploy to Cloud Run (auto-scaling)
- Environment: Python 3.12, FastAPI
- Resources: 1 CPU, 2GB RAM
- Timeout: 60 seconds
- Min instances: 1, Max instances: 5

### Configuration Management

- Environment variables via Cloud Run
- Secrets via Cloud Secret Manager
- Configuration hot-reload every 5 minutes
- Feature flags for gradual rollouts

### Monitoring and Alerting

**Key Metrics**:
- Pipeline latency (target: <60s)
- Signal generation rate
- Insight generation rate
- Error rates by service
- AI provider latency

**Alerts**:
- Pipeline latency >60 seconds
- Error rate >5%
- Unprocessed signals >1 hour old
- AI provider failures >10%
- BigQuery write failures

### Rollback Strategy

- Blue-green deployment for zero downtime
- Keep previous version running during deployment
- Monitor error rates for 10 minutes
- Automatic rollback if error rate >10%

## Future Enhancements

### Phase 2 Features

1. **Real-time WebSocket Updates**: Push insights to frontend without polling
2. **Chart Rendering Integration**: Populate chart_url automatically
3. **Multi-Signal Insights**: Combine multiple signals into single insight
4. **User Feedback Loop**: Learn from user reactions to improve confidence scoring
5. **Advanced Predictive Models**: ML models for better forecasts

### Phase 3 Features

1. **Custom Signal Processors**: User-defined signal logic
2. **Insight Personalization**: Tailor insights to user preferences
3. **Historical Insight Regeneration**: Reprocess old signals with new models
4. **Cross-Chain Signals**: Extend to Ethereum, other blockchains
5. **Insight Clustering**: Group related insights for better UX

