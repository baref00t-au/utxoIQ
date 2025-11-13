# Project Structure

## Repository Organization

```
utxoiq/
├── services/
│   ├── feature-engine/          # Signal computation service
│   │   ├── src/
│   │   │   ├── processors/      # Signal processing logic
│   │   │   ├── models/          # Data models and schemas
│   │   │   └── main.py          # FastAPI application
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── insight-generator/       # AI insight generation service
│   │   ├── src/
│   │   │   ├── generators/      # Insight generation logic
│   │   │   ├── prompts/         # AI prompt templates
│   │   │   └── main.py          # FastAPI application
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── chart-renderer/          # Chart generation service
│   │   ├── src/
│   │   │   ├── renderers/       # Chart rendering logic
│   │   │   ├── templates/       # Chart templates
│   │   │   └── main.py          # FastAPI application
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── web-api/                 # Main API service
│   │   ├── src/
│   │   │   ├── routes/          # API endpoints
│   │   │   ├── middleware/      # Auth, rate limiting
│   │   │   ├── models/          # Database models
│   │   │   └── main.py          # FastAPI application
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── x-bot/                   # Social media automation
│       ├── src/
│       │   ├── posting/         # Tweet composition logic
│       │   ├── scheduling/      # Cron job handlers
│       │   └── main.py          # FastAPI application
│       ├── requirements.txt
│       └── Dockerfile
│
├── frontend/                    # Next.js web application
│   ├── src/
│   │   ├── app/                 # App router pages
│   │   ├── components/          # React components
│   │   │   ├── insights/        # Insight-related components
│   │   │   ├── alerts/          # Alert management
│   │   │   ├── chat/            # AI chat interface
│   │   │   └── billing/         # Subscription management
│   │   ├── lib/                 # Utilities and API clients
│   │   └── types/               # TypeScript type definitions
│   ├── package.json
│   ├── next.config.js
│   └── Dockerfile
│
├── shared/                      # Shared code and schemas
│   ├── types/                   # Common TypeScript interfaces
│   ├── schemas/                 # Data validation schemas
│   └── utils/                   # Shared utilities
│
├── infrastructure/              # Infrastructure as Code
│   ├── terraform/               # GCP resource definitions
│   ├── bigquery/                # BigQuery schemas and migrations
│   └── dataflow/                # Data pipeline definitions
│
├── scripts/                     # Development and deployment scripts
│   ├── setup/                   # Environment setup scripts
│   ├── deploy/                  # Deployment automation
│   └── data/                    # Data migration scripts
│
└── docs/                        # Documentation
    ├── api/                     # API documentation
    ├── deployment/              # Deployment guides
    └── development/             # Development setup
```

## Client/Server Architecture

### Separation Principles
- **Clear API boundaries**: Frontend communicates only through REST APIs
- **No direct database access**: Client never connects directly to databases  
- **Stateless backend**: Services maintain no client session state
- **Authentication delegation**: Client handles tokens, server validates them
- **Data transformation**: Server provides clean APIs, client manages UI state

### Backend Services (Server-side - Python/FastAPI)

Each service follows a consistent structure:

```
service-name/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models
│   ├── routes/              # API route handlers
│   ├── services/            # Business logic
│   ├── utils/               # Helper functions
│   └── tests/               # Unit tests
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
└── cloudbuild.yaml         # GCP build configuration
```

### Frontend Application (Client-side - Next.js)

```
frontend/
├── src/
│   ├── app/                 # App router (Next.js 16)
│   │   ├── layout.tsx       # Root layout with theme provider
│   │   ├── page.tsx         # Home page (server component)
│   │   ├── insights/        # Insight pages with ISR
│   │   ├── alerts/          # Alert management
│   │   ├── chat/            # AI chat interface
│   │   └── billing/         # Subscription pages
│   ├── components/          # Reusable components
│   │   ├── ui/              # shadcn/ui base components
│   │   ├── insights/        # Insight-specific components
│   │   ├── charts/          # Recharts/ECharts components
│   │   ├── forms/           # react-hook-form components
│   │   └── layout/          # Layout components
│   ├── lib/                 # Utilities
│   │   ├── api.ts           # TanStack Query client
│   │   ├── auth.ts          # Firebase Auth integration
│   │   ├── utils.ts         # Helper functions
│   │   ├── validations.ts   # Zod schemas
│   │   └── store.ts         # Zustand store
│   ├── hooks/               # Custom React hooks
│   ├── styles/              # Global styles and Tailwind config
│   └── types/               # TypeScript definitions
├── public/                  # Static assets
├── package.json
├── next.config.js           # Next.js configuration
├── tailwind.config.js       # Tailwind with CSS variables
├── components.json          # shadcn/ui configuration
└── playwright.config.ts     # E2E test configuration
```

## Database Schema Organization

### BigQuery Datasets

```
utxoiq-project/
├── btc/                     # Raw blockchain data
│   ├── blocks               # Block information
│   ├── transactions         # Transaction details
│   ├── entities             # Known addresses/entities
│   └── mempool              # Mempool snapshots
│
└── intel/                   # Processed intelligence
    ├── signals              # Computed signals
    ├── insights             # AI-generated insights
    ├── alerts               # User alert configurations
    └── metrics              # Performance metrics
```

### Cloud SQL (PostgreSQL)

```
utxoiq_db/
├── users                    # User accounts
├── subscriptions            # Billing information
├── user_alerts              # Alert configurations
├── alert_history            # Alert notifications
└── api_keys                 # API access tokens
```

## Development Workflow

### Local Development Setup

1. **Prerequisites**: Docker, Node.js 18+, Python 3.12+, GCP CLI
2. **Environment**: Use `.env.local` files for configuration
3. **Database**: Local PostgreSQL + BigQuery emulator for testing
4. **Services**: Docker Compose for local service orchestration

### Code Organization Principles

- **Separation of Concerns**: Each service has a single responsibility
- **Shared Types**: Common interfaces in `/shared/types/`
- **Configuration**: Environment-based config management
- **Testing**: Tests organized by type in `/tests/` with standardized naming
- **Documentation**: Organized in `/docs/` with clear structure

### Test Organization

Tests are organized by type in separate directories:

```
tests/
├── unit/              # Unit tests (*.unit.test.py/ts)
├── integration/       # Integration tests (*.integration.test.py/ts)
├── e2e/              # End-to-end tests (*.e2e.test.py/ts)
├── performance/      # Performance tests (*.performance.test.py/ts)
└── security/         # Security tests (*.security.test.py/ts)
```

Service-specific tests follow the same naming conventions within each service's `tests/` directory.

### Documentation Organization

```
docs/
├── README.md                    # Documentation index
├── implementation/              # Task implementation notes
├── archive/                     # Historical/completed docs
├── specs/                       # Detailed specifications
└── *.md                        # Active documentation
```

### Scripts Organization

```
scripts/
├── setup/           # Environment setup
├── deployment/      # Deployment automation
├── data/           # Data management
├── testing/        # Testing and verification
└── bigquery/       # BigQuery operations
```

### Naming Conventions

#### Files & Directories
- **Python files**: snake_case (e.g., `feature_engine.py`, `insight_generator.py`)
- **TypeScript files**: camelCase (e.g., `insightCard.tsx`, `apiClient.ts`)
- **Directories**: kebab-case (e.g., `feature-engine/`, `insight-generator/`)
- **Config files**: kebab-case (e.g., `docker-compose.yml`, `next.config.js`)

#### Code Identifiers
- **Python variables/functions**: snake_case (e.g., `block_height`, `process_transaction()`)
- **Python classes**: PascalCase (e.g., `BlockProcessor`, `InsightGenerator`)
- **Python constants**: UPPER_SNAKE_CASE (e.g., `MAX_BLOCK_SIZE`, `API_VERSION`)
- **TypeScript variables/functions**: camelCase (e.g., `blockHeight`, `processTransaction()`)
- **TypeScript interfaces/types**: PascalCase (e.g., `BlockData`, `InsightResponse`)
- **TypeScript constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `API_BASE_URL`)
- **React components**: PascalCase (e.g., `InsightCard`, `AlertManager`)

#### Database & API
- **Database tables**: snake_case (e.g., `user_alerts`, `block_insights`)
- **Database columns**: snake_case (e.g., `created_at`, `block_height`)
- **API endpoints**: kebab-case (e.g., `/api/v1/block-insights`, `/api/v1/user-alerts`)
- **JSON fields**: camelCase (e.g., `blockHeight`, `createdAt`)
- **Environment variables**: UPPER_SNAKE_CASE (e.g., `DATABASE_URL`, `VERTEX_AI_KEY`)

#### Cloud Resources
- **GCP services**: kebab-case (e.g., `utxoiq-api`, `insight-generator`)
- **BigQuery datasets**: snake_case (e.g., `btc_data`, `user_intel`)
- **BigQuery tables**: snake_case (e.g., `block_transactions`, `daily_insights`)
- **Pub/Sub topics**: kebab-case (e.g., `block-processed`, `insight-generated`)
- **Cloud Storage buckets**: kebab-case (e.g., `utxoiq-charts`, `utxoiq-assets`)

## Deployment Strategy

### Cloud Run Services

Each backend service deploys as a separate Cloud Run service:
- Independent scaling and versioning
- Blue-green deployment support
- Automatic HTTPS and load balancing

### Frontend Deployment

- Next.js app deployed to Cloud Run with static optimization
- CDN integration for static assets
- Environment-specific builds

### Infrastructure Management

- Terraform for GCP resource provisioning
- GitHub Actions for CI/CD pipeline
- Cloud Build for container image building
- Secret Manager for sensitive configuration