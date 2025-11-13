# Design Document

## Overview

The utxoIQ platform is designed as a cloud-native, event-driven system that processes Bitcoin blockchain data in real-time to generate AI-powered insights. The architecture follows a microservices pattern with clear separation between data ingestion, processing, AI inference, and presentation layers.

This v2 design extends the MVP with global-ready infrastructure including WebSocket streaming, edge caching, predictive analytics, and multi-channel distribution. The system processes approximately 144 blocks per day (10-minute average) with sub-60-second latency from block mining to insight publication, achieving P95 latency below 200ms globally through CDN integration.

The platform serves multiple interfaces including a PWA-optimized web dashboard, auto-generated SDKs, real-time WebSocket connections, TradingView integration, Telegram bot, and automated email/social media distribution.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    A[Bitcoin Core Node] --> B[Cloud Pub/Sub]
    B --> C[Dataflow Pipeline]
    C --> D[BigQuery Storage - Partitioned/Clustered]
    D --> E[Feature Engine + Predictive Models]
    E --> F[Vertex AI Summarizer + Explainability]
    F --> G[Chart Renderer]
    G --> H[Cloud Storage]
    E --> I[Insight Database]
    I --> J[Web API + WebSocket Server]
    J --> K[Cloud CDN / Edge Cache]
    K --> L[Next.js PWA Frontend]
    K --> M[Auto-Generated SDKs]
    I --> N[X Bot]
    I --> O[Email Service]
    R[Firebase Auth] --> J
    S[Stripe Billing] --> J
    T[Grafana Dashboard] --> J
    T --> D
    T --> E
    U[User Feedback Loop] --> F
```

### Data Flow Architecture

1. **Ingestion Layer**: Bitcoin Core node streams block/transaction data to Cloud Pub/Sub
2. **Processing Layer**: Dataflow normalizes and enriches data, storing in BigQuery
3. **Intelligence Layer**: Feature Engine computes signals, Vertex AI generates insights
4. **Presentation Layer**: Web API serves insights to frontend and external consumers
5. **Distribution Layer**: X Bot and notification services distribute insights

## Components and Interfaces

### 1. Data Ingestion Service

**Technology**: Cloud Pub/Sub + Dataflow
**Responsibility**: Real-time blockchain data ingestion and normalization

**Key Interfaces**:
- Bitcoin Core RPC connection for block/transaction streaming
- Pub/Sub topics: `btc.blocks`, `btc.transactions`, `btc.mempool`
- BigQuery datasets: `btc.blocks`, `btc.transactions`, `btc.entities`

**Processing Logic**:
- Parse raw Bitcoin data into structured format
- Entity resolution for known addresses (exchanges, miners)
- Data validation and anomaly detection
- 6-block confirmation policy for major signals

### 2. Feature Engine Service

**Technology**: Cloud Run (Python/FastAPI)
**Responsibility**: Signal computation, insight triggering, and predictive analytics

**Key Interfaces**:
```python
class SignalProcessor:
    def compute_mempool_signals(self, block_data: BlockData) -> List[Signal]
    def detect_exchange_flows(self, tx_data: List[Transaction]) -> List[Signal]
    def analyze_miner_treasury(self, entity_data: EntityData) -> List[Signal]
    def track_whale_accumulation(self, address_data: AddressData) -> List[Signal]
    
class PredictiveAnalytics:
    def forecast_next_block_fees(self, historical_data: MempoolHistory) -> Prediction
    def compute_liquidity_pressure_index(self, flow_data: ExchangeFlows) -> float
    def predict_signal_trends(self, signal_history: List[Signal]) -> TrendForecast
```

**Signal Types**:
- Mempool Nowcast: Fee quantiles and inclusion estimates
- Exchange Inflow Spike: Anomaly detection on tagged entities
- Miner Treasury Delta: Daily balance changes per mining entity
- Whale Accumulation: 7-day rolling accumulation patterns
- **Predictive Signals** (v2):
  - Next Block Fee Forecast: Temporal model predictions
  - Exchange Liquidity Pressure Index: Flow pattern analysis

### 3. AI Insight Generator

**Technology**: Vertex AI (Gemini Pro)
**Responsibility**: Convert signals into human-readable insights with explainability

**Key Interfaces**:
```python
class InsightGenerator:
    def generate_insight(self, signal: Signal) -> Insight
    def calculate_confidence(self, signal: Signal, context: Context) -> float
    def generate_headline(self, insight: Insight) -> str
    def create_evidence_citations(self, signal: Signal) -> List[Citation]
    def explain_confidence_score(self, insight: Insight) -> ExplainabilitySummary
    def incorporate_user_feedback(self, feedback: UserFeedback) -> None
```

**Prompt Engineering**:
- Context-aware prompts with blockchain domain knowledge
- Confidence scoring based on signal strength and historical accuracy
- Evidence citation requirements for transparency
- Tone guidelines for different user personas
- **Explainability Layer** (v2): Generate "Why Confidence = X%" summaries
- **Feedback Loop** (v2): Store user ratings for model retraining

### 4. Chart Generation Service

**Technology**: Cloud Run (Python/Matplotlib)
**Responsibility**: Generate visual representations of insights

**Key Interfaces**:
```python
class ChartRenderer:
    def render_mempool_chart(self, data: MempoolData) -> bytes
    def render_flow_chart(self, data: FlowData) -> bytes
    def render_accumulation_chart(self, data: AccumulationData) -> bytes
    def upload_to_storage(self, chart: bytes) -> str  # Returns GCS URL
```

### 5. Web API Service

**Technology**: FastAPI + Cloud Run + OpenAPI v3 + WebSocket
**Responsibility**: RESTful API and real-time WebSocket streaming with comprehensive OpenAPI documentation

**OpenAPI v3 Integration**:
- Automatic schema generation via FastAPI's native OpenAPI 3.0 support
- Interactive documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- Exportable schema at `/openapi.json` for SDK generation and contract testing
- Comprehensive Pydantic models for request/response validation
- Security schemes for Firebase Auth JWT and API key authentication
- **SDK Auto-Generation** (v2): Python and JavaScript SDKs from OpenAPI spec

**Key Endpoints**:
```python
# Public endpoints
GET /insights/latest?limit=20&category=mempool
GET /insight/{insight_id}
GET /daily-brief/{date}
GET /openapi.json  # OpenAPI v3 schema export

# Guest Mode (v2)
GET /insights/public?limit=20  # No auth required, limited to 20 recent

# Authenticated endpoints  
POST /alerts
GET /alerts/user/{user_id}
PUT /alerts/{alert_id}
POST /chat/query
GET /billing/subscription

# User Feedback (v2)
POST /insights/{id}/feedback
GET /insights/accuracy-leaderboard

# White-Label API (v2)
GET /api/v1/custom/{client_id}/insights  # Custom branded endpoints

# Documentation endpoints (auto-generated)
GET /docs  # Swagger UI
GET /redoc  # ReDoc UI
```

**WebSocket Integration** (v2):
```python
# Real-time streaming
WS /ws/insights  # Live insight stream
WS /ws/mempool   # Live mempool updates

class WebSocketManager:
    def broadcast_insight(self, insight: Insight) -> None
    def handle_client_connection(self, client_id: str) -> None
    def manage_reconnection(self, client_id: str) -> None
```

**OpenAPI Configuration**:
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="utxoIQ API",
    version="1.0.0",
    description="AI-powered Bitcoin blockchain intelligence platform",
    contact={
        "name": "utxoIQ Support",
        "url": "https://utxoiq.com/support",
        "email": "api@utxoiq.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://utxoiq.com/terms"
    }
)

# Security schemes for OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "FirebaseAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 6. Frontend Application

**Technology**: Next.js 16 + TypeScript + PWA
**Responsibility**: User interface and experience with mobile optimization

**Key Components**:
- InsightFeed: Real-time insight display with infinite scroll and WebSocket updates
- InsightDetail: Full insight view with charts, evidence, and explainability
- DailyBrief: Curated daily summary page
- AlertsManager: User alert configuration interface
- ChatInterface: AI-powered blockchain query interface
- BillingPortal: Subscription management via Stripe
- **GuestMode** (v2): Public demo feed without authentication
- **OnboardingTour** (v2): Interactive guided tour for new users
- **FeedbackWidget** (v2): User accuracy rating interface
- **ExplainabilityPanel** (v2): Confidence score breakdown display

**PWA Features** (v2):
- Service worker for offline support
- Mobile-optimized chart rendering
- Touch gesture support for interactions
- Push notifications for alerts
- App manifest for installability
- Lighthouse performance score > 90

### 7. X Bot Service

**Technology**: Cloud Run + Cloud Scheduler
**Responsibility**: Automated social media posting

**Key Features**:
- Hourly insight polling with confidence filtering (≥0.7)
- Tweet composition with 280-character headlines
- Chart image attachment via X API v2
- Daily "Bitcoin Pulse" thread generation
- Duplicate prevention within 15-minute windows

### 8. Email Service

**Technology**: Cloud Run + SendGrid/Mailgun
**Responsibility**: Automated email delivery for Daily Briefs

**Key Features**:
- Scheduled Daily Brief emails at 07:00 UTC
- Responsive HTML email templates with embedded charts
- User preference management (frequency, content filters)
- Email engagement tracking (open rates, click-through)
- Unsubscribe management and compliance

**Key Interfaces**:
```python
class EmailService:
    def send_daily_brief(self, user: User, brief: DailyBrief) -> None
    def format_email_template(self, brief: DailyBrief) -> str
    def track_engagement(self, email_id: str, event: EmailEvent) -> None
    def manage_preferences(self, user_id: str, prefs: EmailPreferences) -> None
```

### 9. SDK Generation Service

**Technology**: OpenAPI Generator + GitHub Actions
**Responsibility**: Auto-generate and publish client SDKs

**Supported Languages**:
- Python SDK (published to PyPI)
- JavaScript/TypeScript SDK (published to npm)

**SDK Features**:
- Type-safe API clients
- Authentication helpers (Firebase Auth, API keys)
- Error handling and retry logic
- Request/response validation
- Comprehensive documentation and examples

**Generation Pipeline**:
```bash
# Automated via GitHub Actions
1. Export OpenAPI spec from /openapi.json
2. Generate Python SDK using openapi-generator
3. Generate JS/TS SDK using openapi-generator
4. Run tests on generated SDKs
5. Publish to PyPI and npm with semantic versioning
```

### 10. Observability Dashboard

**Technology**: Grafana + Cloud Monitoring
**Responsibility**: System performance monitoring and cost tracking

**Key Metrics**:
- Block-to-insight latency (P50, P95, P99)
- API uptime and error rates
- WebSocket connection stability
- AI inference costs per insight
- BigQuery query costs and performance
- User engagement metrics
- Insight accuracy ratings

**Alerting Rules**:
- P95 latency > 60 seconds
- API error rate > 1%
- Daily AI costs exceed budget threshold
- BigQuery costs exceed budget threshold
- WebSocket disconnection rate > 5%

### 11. CDN and Edge Caching

**Technology**: Cloud CDN + Cloud Storage
**Responsibility**: Global content delivery with low latency

**Caching Strategy**:
- Public insight feed: 60-second TTL
- Chart images: 1-hour TTL with immutable URLs
- Daily Brief pages: 24-hour TTL
- Static assets: 1-year TTL with versioning
- API responses: Conditional caching based on auth status

**Edge Locations**:
- Global distribution for P95 latency < 200ms
- Automatic cache invalidation on new insights
- Cache warming for popular content

## Data Models

### Core Data Structures

```typescript
interface Insight {
  id: string;
  signal_type: SignalType;
  headline: string;
  summary: string;
  confidence: number; // 0-1
  timestamp: Date;
  block_height: number;
  evidence: Citation[];
  chart_url?: string;
  tags: string[];
  explainability?: ExplainabilitySummary; // v2
  accuracy_rating?: number; // v2: aggregate user feedback
  is_predictive?: boolean; // v2: flag for predictive signals
}

interface Signal {
  type: SignalType;
  strength: number;
  data: Record<string, any>;
  block_height: number;
  transaction_ids: string[];
  entity_ids: string[];
  is_predictive?: boolean; // v2
  prediction_confidence_interval?: [number, number]; // v2
}

interface Citation {
  type: 'block' | 'transaction' | 'address';
  id: string;
  description: string;
  url: string;
}

interface Alert {
  id: string;
  user_id: string;
  signal_type: SignalType;
  threshold: number;
  operator: 'gt' | 'lt' | 'eq';
  is_active: boolean;
  created_at: Date;
}

// v2: New data models
interface ExplainabilitySummary {
  confidence_factors: {
    signal_strength: number;
    historical_accuracy: number;
    data_quality: number;
  };
  explanation: string;
  supporting_evidence: string[];
}

interface UserFeedback {
  insight_id: string;
  user_id: string;
  rating: 'useful' | 'not_useful';
  timestamp: Date;
  comment?: string;
}

interface PredictiveSignal {
  type: 'fee_forecast' | 'liquidity_pressure';
  prediction: number;
  confidence_interval: [number, number];
  forecast_horizon: string; // e.g., "next_block", "1h", "4h"
  model_version: string;
}

interface EmailPreferences {
  user_id: string;
  daily_brief_enabled: boolean;
  frequency: 'daily' | 'weekly' | 'never';
  signal_filters: SignalType[];
  quiet_hours?: { start: string; end: string };
}

interface WhiteLabelConfig {
  client_id: string;
  custom_domain: string;
  branding: {
    logo_url: string;
    primary_color: string;
    company_name: string;
  };
  api_endpoint_prefix: string;
  sla_tier: 'standard' | 'premium';
}
```

### Database Schema (BigQuery)

**btc.blocks**:
- block_hash, height, timestamp, size, tx_count, fees_total

**btc.transactions**:
- tx_hash, block_height, input_count, output_count, fee, size

**btc.entities**:
- address, entity_type, entity_name, first_seen, last_seen

**intel.insights** (v2: clustered by signal_type):
- insight_id, signal_type, confidence, headline, summary, created_at
- explainability_json, accuracy_rating, feedback_count, is_predictive

**intel.signals** (v2: partitioned by timestamp):
- signal_id, type, strength, block_height, data_json, processed_at
- is_predictive, prediction_confidence_interval, model_version

**intel.user_feedback** (v2):
- feedback_id, insight_id, user_id, rating, timestamp, comment

**intel.predictive_signals** (v2):
- prediction_id, signal_type, prediction_value, confidence_interval
- forecast_horizon, model_version, created_at, actual_value, accuracy_score

**intel.email_preferences** (v2):
- user_id, daily_brief_enabled, frequency, signal_filters_json, quiet_hours_json

**intel.white_label_clients** (v2):
- client_id, custom_domain, branding_json, api_prefix, sla_tier, created_at

**intel.cost_tracking** (v2):
- cost_id, service_type, insight_id, cost_usd, timestamp, resource_details_json

## Error Handling

### Data Quality Assurance

1. **Anomaly Detection**: Statistical outlier detection on key metrics
2. **Quiet Mode**: Automatic insight suppression during detected anomalies
3. **Confirmation Policy**: 6-block confirmation for high-impact signals
4. **Rollback Handling**: Reprocessing insights affected by blockchain reorgs

### API Error Responses

**OpenAPI v3 Error Schema**:
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class ErrorCode(str, Enum):
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SUBSCRIPTION_REQUIRED = "SUBSCRIPTION_REQUIRED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: str
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "API rate limit exceeded. Try again in 60 seconds.",
                    "details": {
                        "limit": 100,
                        "window": "1h",
                        "retry_after": 60
                    }
                },
                "request_id": "req_abc123",
                "timestamp": "2025-11-07T10:30:00Z"
            }
        }
```

**Error Categories with OpenAPI Documentation**:
- `DATA_UNAVAILABLE`: Blockchain data not yet available (HTTP 503)
- `CONFIDENCE_TOO_LOW`: Insight confidence below publication threshold (HTTP 422)
- `RATE_LIMIT_EXCEEDED`: User exceeded API rate limits (HTTP 429)
- `SUBSCRIPTION_REQUIRED`: Feature requires paid subscription (HTTP 402)
- `VALIDATION_ERROR`: Request validation failed (HTTP 400)
- `INTERNAL_ERROR`: Server-side processing error (HTTP 500)

### Monitoring and Alerting

- **SLA Monitoring**: Block-to-insight latency tracking (P95 < 60s)
- **Data Quality**: Duplicate signal rate monitoring (< 0.5%)
- **API Health**: Uptime monitoring (≥ 99.9%)
- **Cost Monitoring**: AI inference and compute cost tracking

## Testing Strategy

### Unit Testing
- Signal computation algorithms with historical data
- AI prompt engineering with known blockchain events
- Chart generation with various data scenarios
- API endpoint validation with mock data

### Integration Testing
- End-to-end data pipeline from Bitcoin node to insight publication
- X Bot posting workflow with test accounts
- Billing integration with Stripe test environment
- Authentication flow with Firebase test project

### Performance Testing
- Load testing API endpoints with concurrent users
- Stress testing Feature Engine with high block volume
- Latency testing for real-time insight generation
- Database query optimization validation

### Security Testing
- API authentication and authorization validation
- Input sanitization for chat queries
- Rate limiting effectiveness testing
- Data privacy compliance verification

## Deployment Architecture

### Production Environment (GCP)

**Compute**:
- Cloud Run services for stateless components
- Cloud Functions for event-driven processing
- GKE cluster for Bitcoin Core node (persistent storage)

**Storage**:
- BigQuery for analytical workloads
- Cloud SQL (PostgreSQL) for transactional data
- Cloud Storage for chart images and static assets
- Redis (Memorystore) for caching and rate limiting

**Networking**:
- Cloud Load Balancer with SSL termination
- Cloud CDN for static asset delivery
- VPC with private subnets for internal services
- Cloud NAT for outbound internet access

**Security**:
- Identity and Access Management (IAM) roles
- Secret Manager for API keys and credentials
- Cloud Security Command Center monitoring
- Web Application Firewall (Cloud Armor)

### CI/CD Pipeline

1. **Source Control**: GitHub with branch protection rules
2. **Build**: Cloud Build with Docker containerization
3. **Testing**: Automated test suite execution
4. **OpenAPI Validation** (v2): Schema diff validation for API contract testing
5. **Canary Deployment** (v2): 10% traffic routing with automated rollback
6. **Deployment**: Blue-green deployment to Cloud Run
7. **SDK Generation** (v2): Auto-generate and publish Python/JS SDKs
8. **Monitoring**: Cloud Monitoring and Logging integration with Grafana dashboards

**Canary Deployment Strategy** (v2):
- Route 10% of traffic to new version
- Monitor error rates and latency for 15 minutes
- Automatic rollback if error rate > 1% or P95 latency > 60s
- Gradual traffic increase: 10% → 25% → 50% → 100%
- OpenAPI schema compatibility validation before deployment