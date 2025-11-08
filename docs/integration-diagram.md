# Platform Integration Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                             │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Dashboard (/dashboard)                       │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │   Insights   │  │System Status │  │   Metrics    │         │ │
│  │  │              │  │              │  │              │         │ │
│  │  │ • Feed       │  │ • Services   │  │ • Signals    │         │ │
│  │  │ • Feedback   │  │ • Backfill   │  │ • Insights   │         │ │
│  │  │ • Ratings    │  │ • Progress   │  │ • Charts     │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  │                                                                  │ │
│  │  ┌────────────────────────────────────────────────────────┐    │ │
│  │  │         Real-time Updates (WebSocket)                   │    │ │
│  │  │  • New insights    • Backfill progress                  │    │ │
│  │  │  • System status   • Signal computed                    │    │ │
│  │  └────────────────────────────────────────────────────────┘    │ │
│  └──────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   HTTP + WebSocket    │
                    └───────────┬───────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                          WEB API LAYER                               │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Monitoring     │  │    Feedback      │  │    WebSocket     │  │
│  │   Endpoints      │  │    Endpoints     │  │    Manager       │  │
│  │                  │  │                  │  │                  │  │
│  │ • /status        │  │ • /rate          │  │ • /ws/monitoring │  │
│  │ • /backfill      │  │ • /comment       │  │ • /ws/insights   │  │
│  │ • /metrics       │  │ • /flag          │  │ • Broadcast      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Connection Manager & Event Bus                   │  │
│  │  • Manages WebSocket connections                              │  │
│  │  • Broadcasts events to connected clients                     │  │
│  │  • Handles reconnection and heartbeat                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   Internal Services   │
                    └───────────┬───────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                      BACKEND SERVICES                                │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Feature Engine   │  │ Insight Generator│  │ Data Ingestion   │  │
│  │                  │  │                  │  │                  │  │
│  │ • Compute signals│  │ • Generate AI    │  │ • Fetch blocks   │  │
│  │ • Detect patterns│  │   insights       │  │ • Process txs    │  │
│  │ • Publish events │  │ • Publish events │  │ • Stream to BQ   │  │
│  └──────────────────┘  └──────────────────┘  └────────┬─────────┘  │
│                                                         │            │
│  ┌──────────────────────────────────────────────────────┘            │
│  │                                                                    │
│  │  ┌──────────────────┐  ┌──────────────────┐                      │
│  │  │   Chart Renderer │  │     X Bot        │                      │
│  │  │                  │  │                  │                      │
│  │  │ • Generate charts│  │ • Post insights  │                      │
│  │  │ • Store in GCS   │  │ • Schedule posts │                      │
│  │  └──────────────────┘  └──────────────────┘                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │    Data Storage       │
                    └───────────┬───────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                         DATA LAYER                                   │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   PostgreSQL     │  │    BigQuery      │  │      Redis       │  │
│  │                  │  │                  │  │                  │  │
│  │ • Users          │  │ • Blocks         │  │ • Cache          │  │
│  │ • Feedback       │  │ • Transactions   │  │ • Rate limits    │  │
│  │ • Backfill jobs  │  │ • Signals        │  │ • Sessions       │  │
│  │ • Alerts         │  │ • Insights       │  │ • Pub/Sub        │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐                         │
│  │  Cloud Storage   │  │   Pub/Sub        │                         │
│  │                  │  │                  │                         │
│  │ • Chart images   │  │ • Event stream   │                         │
│  │ • Static assets  │  │ • Job queue      │                         │
│  └──────────────────┘  └──────────────────┘                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   External Services   │
                    └───────────┬───────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                      EXTERNAL INTEGRATIONS                           │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Bitcoin Core    │  │   Vertex AI      │  │     X API        │  │
│  │      RPC         │  │   (Gemini Pro)   │  │                  │  │
│  │                  │  │                  │  │                  │  │
│  │ • Block data     │  │ • Generate text  │  │ • Post tweets    │  │
│  │ • Mempool info   │  │ • Confidence     │  │ • Schedule posts │  │
│  │ • Transaction    │  │ • Embeddings     │  │                  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### 1. Backfill Progress Flow

```
┌──────────────┐
│ Backfill     │
│ Script       │
└──────┬───────┘
       │ 1. Create job
       ▼
┌──────────────┐
│ Web API      │
│ /backfill    │
└──────┬───────┘
       │ 2. Store job
       ▼
┌──────────────┐
│ PostgreSQL   │
│ backfill_jobs│
└──────┬───────┘
       │ 3. Broadcast update
       ▼
┌──────────────┐
│ WebSocket    │
│ Manager      │
└──────┬───────┘
       │ 4. Send to clients
       ▼
┌──────────────┐
│ Dashboard    │
│ (Frontend)   │
└──────────────┘
```

### 2. Insight Generation Flow

```
┌──────────────┐
│ New Block    │
│ Detected     │
└──────┬───────┘
       │ 1. Process block
       ▼
┌──────────────┐
│ Feature      │
│ Engine       │
└──────┬───────┘
       │ 2. Compute signals
       ▼
┌──────────────┐
│ Insight      │
│ Generator    │
└──────┬───────┘
       │ 3. Generate insight
       ▼
┌──────────────┐
│ BigQuery     │
│ insights     │
└──────┬───────┘
       │ 4. Broadcast event
       ▼
┌──────────────┐
│ WebSocket    │
│ Manager      │
└──────┬───────┘
       │ 5. Notify clients
       ▼
┌──────────────┐
│ Dashboard    │
│ Toast        │
└──────────────┘
```

### 3. User Feedback Flow

```
┌──────────────┐
│ User clicks  │
│ "Rate"       │
└──────┬───────┘
       │ 1. Submit rating
       ▼
┌──────────────┐
│ Web API      │
│ /feedback    │
└──────┬───────┘
       │ 2. Store feedback
       ▼
┌──────────────┐
│ PostgreSQL   │
│ feedback     │
└──────┬───────┘
       │ 3. Update stats
       ▼
┌──────────────┐
│ Cache        │
│ (Redis)      │
└──────┬───────┘
       │ 4. Return response
       ▼
┌──────────────┐
│ Dashboard    │
│ Success toast│
└──────────────┘
```

## Component Interactions

### Frontend Components

```
Dashboard Page
├── Tabs
│   ├── Insights Tab
│   │   ├── InsightFeed
│   │   │   ├── InsightCard
│   │   │   │   └── InsightFeedback
│   │   │   │       ├── Rating Dialog
│   │   │   │       ├── Comment Dialog
│   │   │   │       └── Flag Dialog
│   │   │   └── Pagination
│   │   └── Filters
│   │
│   ├── System Status Tab
│   │   ├── SystemStatusDashboard
│   │   │   ├── Overall Status Card
│   │   │   ├── Services Health Card
│   │   │   ├── Backfill Progress Card
│   │   │   ├── Processing Metrics Cards
│   │   │   └── Performance Metrics Card
│   │   └── WebSocket Indicator
│   │
│   └── Metrics Tab
│       ├── SignalMetrics
│       └── InsightMetrics
│
└── useMonitoringWebSocket Hook
    ├── Connection Management
    ├── Event Handlers
    ├── Query Invalidation
    └── Toast Notifications
```

### Backend Services

```
Web API
├── Routes
│   ├── /api/v1/monitoring
│   │   ├── GET /status
│   │   ├── GET /backfill
│   │   ├── GET /backfill/{job_id}
│   │   ├── GET /metrics/signals
│   │   └── GET /metrics/insights
│   │
│   ├── /api/v1/feedback
│   │   ├── POST /insights/{id}/rate
│   │   ├── POST /insights/{id}/comment
│   │   ├── POST /insights/{id}/flag
│   │   └── GET /insights/{id}/stats
│   │
│   └── /ws
│       ├── /ws/monitoring
│       └── /ws/insights
│
├── WebSocket Manager
│   ├── Connection Pool
│   ├── Broadcast Loop
│   ├── Event Handlers
│   └── Heartbeat
│
└── Middleware
    ├── CORS
    ├── Auth
    └── Rate Limiting
```

## Technology Stack

### Frontend
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix)
- **State Management**: TanStack Query + Zustand
- **Real-time**: WebSocket API
- **Notifications**: Sonner (toast)

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.9+
- **API**: REST + WebSocket
- **Validation**: Pydantic
- **Async**: asyncio

### Data Storage
- **Relational**: PostgreSQL (Cloud SQL)
- **Analytics**: BigQuery
- **Cache**: Redis (Memorystore)
- **Files**: Cloud Storage
- **Events**: Cloud Pub/Sub

### Infrastructure
- **Platform**: Google Cloud Platform
- **Compute**: Cloud Run (serverless)
- **Orchestration**: Docker Compose (local)
- **CI/CD**: GitHub Actions
- **IaC**: Terraform

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Cloud Load Balancer                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────┐              ┌───────────────┐
│  Cloud Run    │              │  Cloud Run    │
│  (Frontend)   │              │  (Web API)    │
│               │              │               │
│ • Next.js     │              │ • FastAPI     │
│ • SSR/ISR     │              │ • WebSocket   │
│ • Static      │              │ • REST API    │
└───────────────┘              └───────┬───────┘
                                       │
                        ┌──────────────┴──────────────┐
                        │                             │
                        ▼                             ▼
                ┌───────────────┐           ┌───────────────┐
                │  Cloud Run    │           │  Cloud Run    │
                │  (Services)   │           │  (Services)   │
                │               │           │               │
                │ • Feature     │           │ • Insight     │
                │   Engine      │           │   Generator   │
                │ • Data        │           │ • Chart       │
                │   Ingestion   │           │   Renderer    │
                └───────┬───────┘           └───────┬───────┘
                        │                           │
                        └───────────┬───────────────┘
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                        ▼                       ▼
                ┌───────────────┐       ┌───────────────┐
                │  Cloud SQL    │       │   BigQuery    │
                │  (PostgreSQL) │       │               │
                │               │       │ • Blocks      │
                │ • Users       │       │ • Signals     │
                │ • Feedback    │       │ • Insights    │
                │ • Jobs        │       │               │
                └───────────────┘       └───────────────┘
```

## Security & Authentication

```
User Request
    │
    ▼
┌─────────────┐
│ Firebase    │
│ Auth        │
└──────┬──────┘
       │ JWT Token
       ▼
┌─────────────┐
│ Web API     │
│ Middleware  │
└──────┬──────┘
       │ Verify Token
       ▼
┌─────────────┐
│ Protected   │
│ Endpoint    │
└─────────────┘
```

## Monitoring & Observability

```
Application Logs
    │
    ▼
┌─────────────┐
│ Cloud       │
│ Logging     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Cloud       │
│ Monitoring  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Alerts &    │
│ Dashboards  │
└─────────────┘
```
