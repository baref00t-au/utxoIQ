# AGENTS.md

## Project Overview

utxoIQ is an AI-powered Bitcoin blockchain intelligence platform that transforms raw on-chain data into human-readable insights for traders, analysts, and researchers. The platform processes Bitcoin blocks within 60 seconds to generate actionable insights using Vertex AI.

## Setup Commands

**IMPORTANT: Use Python 3.12.x (NOT 3.14+)**
Python 3.14 is too new and many dependencies are not yet compatible.

```bash
# Backend services (Python 3.12/FastAPI)
python --version  # Should show Python 3.12.x
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend (Next.js 16)
npm install
npm run dev

# Build containers
docker build -t utxoiq-api .
docker build -t utxoiq-frontend .

# GCP deployment
gcloud run deploy utxoiq-api --source .
gcloud run deploy utxoiq-frontend --source .
```

## Architecture

### Client/Server Separation
- **Clear API boundaries**: Frontend communicates only through REST APIs
- **No direct database access**: Client never connects directly to databases
- **Stateless services**: Backend services maintain no client session state
- **Authentication flow**: Client handles auth tokens, server validates them
- **Data transformation**: Server provides clean JSON APIs, client handles UI state

### Backend Services (Server-side)
- **Microservices**: FastAPI backends for feature-engine, insight-generator, chart-renderer, web-api, x-bot
- **Data layer**: BigQuery, Cloud SQL, Redis - never exposed to client
- **Business logic**: All Bitcoin processing, AI generation, and data validation
- **External integrations**: Bitcoin Core RPC, Vertex AI, X API
- **Authentication**: JWT token validation and user authorization

### Frontend (Client-side)
- **Next.js 16**: App Router, Server Components, ISR for fast public pages
- **TypeScript**: Strict configuration for type safety
- **Styling**: Tailwind CSS with CSS variables for theme tokens
- **UI Components**: shadcn/ui (Radix primitives) for accessible, themeable components
- **Animation**: Framer Motion for micro-interactions
- **Charts**: Recharts (start) → ECharts/D3 for custom visualizations
- **State management**: TanStack Query (server cache), Zustand (lightweight app state)
- **Forms**: react-hook-form + zod for validation
- **Tables**: TanStack Table with virtualization for Live Feed
- **Icons**: lucide-react
- **Testing**: Playwright (e2e) + Vitest/RTL (unit)

### Cloud Infrastructure
- **Google Cloud Platform**: Cloud Run, BigQuery, Cloud SQL, Pub/Sub
- **AI**: Vertex AI with Gemini Pro for insight generation
- **Auth**: Firebase Auth with Stripe for payments

## Code Style

### Python (Backend Services)
- FastAPI with async/await patterns
- PEP 8 with 88-character line limit (Black formatter)
- Pydantic models for validation
- Type hints required for all functions
- Import order: standard library, third-party, local

### TypeScript (Frontend)
- Strict TypeScript with no implicit any
- React functional components with hooks
- Next.js 16 App Router with Server Components
- shadcn/ui components with Radix primitives
- Tailwind CSS with CSS variables for theming
- TanStack Query for server state, Zustand for client state
- react-hook-form + zod for form validation
- Framer Motion for animations
- Prefer server components when possible

### Database
- snake_case for table/column names
- BigQuery for analytics, Cloud SQL for transactions
- Always include proper indexing
- Validate at API and database levels

## File Organization

### Project Structure Overview

```
utxoIQ/
├── docs/                        # All documentation
│   ├── archive/                 # Historical/completed docs
│   ├── implementation/          # Task implementation notes
│   ├── specs/                   # Supplementary specifications
│   └── *.md                     # Active documentation
├── scripts/                     # All scripts organized by purpose
│   ├── setup/                   # Environment setup scripts
│   ├── deployment/              # Deployment automation
│   ├── data/                    # Data management scripts
│   ├── testing/                 # Testing and verification
│   └── bigquery/                # BigQuery operations
├── tests/                       # System-level tests (cross-service)
│   ├── unit/                    # Cross-service utility tests
│   ├── integration/             # Multi-service integration tests
│   ├── e2e/                     # End-to-end user workflows
│   ├── performance/             # System-wide performance tests
│   └── security/                # Platform security tests
├── services/                    # Microservices
│   ├── {service-name}/
│   │   ├── src/                 # Service source code
│   │   ├── tests/               # Service-specific tests (unit + integration)
│   │   ├── Dockerfile
│   │   ├── pytest.ini
│   │   └── requirements.txt
│   └── ...
├── frontend/                    # Next.js application
│   ├── src/
│   ├── public/
│   └── tests/
├── shared/                      # Shared code and schemas
├── infrastructure/              # Infrastructure as Code
├── temp/                        # Temporary files
└── [config files]               # Root config files only
```

### Root Directory Rules
- **DO NOT** create documents, scripts, or temporary files in the root directory
- **Use organized directories**:
  - `docs/` - All documentation files (guides, specs, notes)
  - `docs/implementation/` - Task implementation notes
  - `docs/archive/` - Historical/completed documentation
  - `docs/specs/` - Specification documents with numbered format (e.g., `utxo-001/`, `utxo-002/`)
  - `scripts/setup/` - Environment setup scripts
  - `scripts/deployment/` - Deployment automation scripts
  - `scripts/data/` - Data management and migration scripts
  - `scripts/testing/` - Testing and verification scripts
  - `scripts/bigquery/` - BigQuery-specific operations
  - `temp/` - Temporary files and test outputs
- **Root directory should only contain**:
  - Core config files (`.env`, `docker-compose.yml`, `package.json`, `pytest.ini`, etc.)
  - README.md, QUICKSTART.md, SETUP_CHECKLIST.md
  - .gitignore
  - License files

### Where to Put New Files

**Documentation:**
- Active guides → `docs/`
- Implementation notes → `docs/implementation/`
- Completed/historical → `docs/archive/`
- Specifications → `docs/specs/` or `.kiro/specs/`

**Scripts:**
- Setup/configuration → `scripts/setup/`
- Deployment → `scripts/deployment/`
- Data operations → `scripts/data/`
- Testing/verification → `scripts/testing/`
- BigQuery operations → `scripts/bigquery/`

**Tests:**
- Service-specific → `services/{service-name}/tests/`
- Cross-service workflows → `tests/e2e/`
- Multi-service integration → `tests/integration/`
- System performance → `tests/performance/`
- Platform security → `tests/security/`

**Temporary files:**
- All temp files → `temp/`

### Specification Documentation
- **Kiro-managed specs**: Keep in `.kiro/specs/` directory (managed by Kiro IDE)
  - These contain `requirements.md`, `design.md`, and `tasks.md`
  - Do NOT move or duplicate these files
- **Additional spec documentation**: Use `docs/specs/` for supplementary documentation
  - Implementation notes, research, diagrams, etc.
  - Use numbered format: `utxo-001/`, `utxo-002/`
- **Spec references**: Reference Kiro specs by their directory name (e.g., "See .kiro/specs/utxoiq-mvp/")

### Examples
✅ **Correct**:
- `.kiro/specs/utxoiq-mvp/requirements.md` (Kiro-managed spec)
- `docs/api-guide.md` (active documentation)
- `docs/implementation/task-1-implementation.md` (implementation notes)
- `docs/archive/deployment-complete.md` (historical docs)
- `docs/specs/utxo-001/implementation-notes.md` (supplementary specs)
- `scripts/setup/local-dev.sh` (setup script)
- `scripts/deployment/deploy-web-api.sh` (deployment script)
- `scripts/data/backfill-blocks.py` (data script)
- `scripts/testing/verify-deployment.py` (testing script)
- `services/web-api/tests/api.unit.test.py` (service test)
- `tests/e2e/user-signup.e2e.test.py` (system test)
- `temp/test-output.json` (temporary file)

❌ **Incorrect**:
- `test-bitcoin-connection.bat` (should be `scripts/testing/test-bitcoin-connection.bat`)
- `IMPLEMENTATION_SUMMARY.md` (should be `docs/implementation/task-1-implementation.md`)
- `deploy-api.sh` (should be `scripts/deployment/deploy-api.sh`)
- `test-output.json` (should be `temp/test-output.json`)
- `setup.sh` (should be `scripts/setup/setup.sh`)
- `BUILD_SUCCESS.md` (should be `docs/archive/build-success.md`)

### Structure Verification

Run the automated structure verification tool:
```bash
python scripts/testing/verify-project-structure.py
```

This checks:
- Root directory cleanliness (no stray files)
- Test naming conventions (*.unit.test.py, *.integration.test.py, etc.)
- Documentation organization (active vs archived)
- Scripts organization (by purpose)
- Service test patterns (colocated with services)

## Naming Conventions

### Files & Directories
- **Python files**: snake_case (e.g., `feature_engine.py`, `insight_generator.py`)
- **TypeScript files**: camelCase (e.g., `insightCard.tsx`, `apiClient.ts`)
- **Directories**: kebab-case (e.g., `feature-engine/`, `insight-generator/`)
- **Config files**: kebab-case (e.g., `docker-compose.yml`, `next.config.js`)

### Code Identifiers
- **Python variables/functions**: snake_case (e.g., `block_height`, `process_transaction()`)
- **Python classes**: PascalCase (e.g., `BlockProcessor`, `InsightGenerator`)
- **Python constants**: UPPER_SNAKE_CASE (e.g., `MAX_BLOCK_SIZE`, `API_VERSION`)
- **TypeScript variables/functions**: camelCase (e.g., `blockHeight`, `processTransaction()`)
- **TypeScript interfaces/types**: PascalCase (e.g., `BlockData`, `InsightResponse`)
- **TypeScript constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `API_BASE_URL`)
- **React components**: PascalCase (e.g., `InsightCard`, `AlertManager`)

### Database & API
- **Database tables**: snake_case (e.g., `user_alerts`, `block_insights`)
- **Database columns**: snake_case (e.g., `created_at`, `block_height`)
- **API endpoints**: kebab-case (e.g., `/api/v1/block-insights`, `/api/v1/user-alerts`)
- **JSON fields**: camelCase (e.g., `blockHeight`, `createdAt`)
- **Environment variables**: UPPER_SNAKE_CASE (e.g., `DATABASE_URL`, `VERTEX_AI_KEY`)

### Cloud Resources
- **GCP services**: kebab-case (e.g., `utxoiq-api`, `insight-generator`)
- **BigQuery datasets**: snake_case (e.g., `btc_data`, `user_intel`)
- **BigQuery tables**: snake_case (e.g., `block_transactions`, `daily_insights`)
- **Pub/Sub topics**: kebab-case (e.g., `block-processed`, `insight-generated`)
- **Cloud Storage buckets**: kebab-case (e.g., `utxoiq-charts`, `utxoiq-assets`)

## Testing Instructions

### Test File Structure

**Two-tier test organization:**

1. **Service Tests** (`services/{service-name}/tests/`)
   - Unit tests for service-specific logic
   - Integration tests for service dependencies (DB, external APIs)
   - Tests are colocated with the service code
   - Each service has its own pytest.ini

2. **System Tests** (`tests/`)
   - Cross-service integration tests
   - End-to-end user workflow tests
   - System-wide performance tests
   - Platform security tests

```
# Service-level tests (most tests go here)
services/
├── web-api/tests/           # web-api unit + integration tests
├── utxoiq-ingestion/tests/  # ingestion unit + integration tests
└── ...

# System-level tests (cross-service only)
tests/
├── unit/              # Cross-service utility tests
├── integration/       # Multi-service integration tests
├── e2e/              # End-to-end user workflows
├── performance/      # System-wide load tests
└── security/         # Platform security tests
```

### Test File Naming Conventions

- **Unit tests**: `*.unit.test.py` or `*.unit.test.ts`
- **Integration tests**: `*.integration.test.py` or `*.integration.test.ts`
- **E2E tests**: `*.e2e.test.py` or `*.e2e.test.ts`
- **Performance tests**: `*.performance.test.py` or `*.performance.test.ts`
- **Security tests**: `*.security.test.py` or `*.security.test.ts`

### Running Tests

```bash
# Python tests
pytest                              # Run all tests
pytest tests/unit/                  # Run unit tests only
pytest tests/integration/           # Run integration tests only
pytest tests/e2e/                   # Run e2e tests only
pytest --cov=src tests/             # Run with coverage

# TypeScript tests
npm test                            # Run all tests
npm test -- tests/unit              # Run unit tests only
npm test -- tests/integration       # Run integration tests only
npm test -- tests/e2e               # Run e2e tests only
npm run test:coverage               # Run with coverage

# Linting
black src/
flake8 src/
npm run lint
```

### Test Guidelines

- **Unit tests**: Test individual functions/classes in isolation, mock dependencies, fast execution (< 1s)
- **Integration tests**: Test component interactions, use test databases, moderate speed (< 10s)
- **E2E tests**: Test complete workflows, use staging environments, slower (< 60s)
- **Performance tests**: Test system performance under load, measure response times
- **Security tests**: Test auth/authorization, check vulnerabilities, validate input sanitization

## Bitcoin-Specific Guidelines

- Always validate block heights and transaction hashes
- Use proper Bitcoin address validation (P2PKH, P2SH, Bech32)
- Handle mempool volatility with caching
- Implement reorg detection for blockchain data
- Use satoshi units internally, convert to BTC for display
- Process new blocks within 60 seconds
- Include blockchain citations in all insights

## AI & Content Generation

- Use Vertex AI Gemini Pro for insights
- Include confidence scores for AI content
- Always provide blockchain evidence (block height, tx hash)
- Generate actionable insights, not just summaries
- Implement fallback strategies for AI failures
- Use consistent professional tone

## Security Requirements

- Firebase Auth for user management
- API keys with proper scoping and rate limiting
- Environment variables for secrets
- Cloud Secret Manager for production
- Never log sensitive user data
- GDPR compliance for data handling

## Development Workflow

- Write unit tests for business logic (80%+ coverage)
- Use pre-commit hooks for formatting
- Implement proper error handling with structured logging
- Use Cloud Monitoring for metrics and alerting
- Blue-green deployments for zero downtime
- Feature flags for gradual rollouts

## Performance Guidelines

- Connection pooling for databases
- Multi-level caching (Redis, CDN)
- Async processing for non-critical operations
- Optimize BigQuery with partitioning/clustering
- Lazy loading for frontend components
- Design for horizontal scaling

## Client/Server Boundaries

### Server Responsibilities
- Data persistence and retrieval
- Business logic and validation
- External API integrations (Bitcoin Core, Vertex AI)
- Authentication and authorization
- Rate limiting and security
- Background processing and cron jobs

### Client Responsibilities
- User interface rendering
- Form validation (client-side only, server always validates)
- Navigation and routing
- Local state management
- API request orchestration
- Real-time UI updates

### Communication Patterns
- **API-first design**: All client-server communication via REST APIs
- **JSON data exchange**: Structured request/response formats
- **Stateless requests**: Each request contains all necessary context
- **Error handling**: Consistent error response formats across all APIs
- **Authentication**: Bearer tokens in Authorization headers
- **CORS configuration**: Proper cross-origin resource sharing setup

## Common Patterns

- Use Cloud Pub/Sub for inter-service communication (server-side only)
- Implement circuit breakers for external APIs (server-side only)
- RESTful endpoints with proper HTTP status codes
- API versioning in URL paths (v1, v2)
- Consistent error response formats
- Correlation IDs for request tracing

## Frontend Implementation Notes

### Theming & Design
- Define Tailwind tokens for `--brand`, `--accent`, `--background`, `--foreground`
- Enable dark mode by default with light mode toggle
- Use charcoal/white/orange color palette
- Grid-based card layouts for insights
- Responsive typography with `clamp()` for headings
- shadcn/ui components themed to brand

### Performance Optimization
- Next.js Server Components for static content
- ISR (Incremental Static Regeneration) for insight pages
- Next `<Image>` component with GCS signed URLs for charts
- CDN caching for static assets
- Streaming with server actions + Suspense for Live Feed
- TanStack Table virtualization for large datasets

### SEO & Metadata
- Dynamic `<Metadata>` per insight page
- OpenGraph images using chart PNGs
- Structured data for blockchain insights
- Sitemap generation for public pages

### Data Fetching Patterns
- TanStack Query for server state with optimistic updates
- Zustand for lightweight client state (UI preferences, filters)
- Server actions for mutations
- Polling or WebSocket for real-time Live Feed updates

### Forms & Validation
- react-hook-form for performance
- Zod schemas shared between client and server
- Client-side validation for UX, server-side for security
- Accessible error messages

## Deployment Notes

- Each service deploys as separate Cloud Run service
- Next.js standalone output → Cloud Run
- Use Docker for containerization
- GitHub Actions for CI/CD
- Terraform for infrastructure provisioning
- Environment-specific configuration
- Health checks for all services
- CDN caching enabled for static assets