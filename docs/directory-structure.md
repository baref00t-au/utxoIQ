# Directory Structure Reference

## Root Directory

```
utxoIQ/
├── .env, .env.example          # Environment configuration
├── .gitignore                  # Git ignore rules
├── AGENTS.md                   # AI agent guidelines (single source)
├── docker-compose.yml          # Docker composition
├── package.json                # Node.js dependencies
├── pytest.ini                  # Root pytest configuration
├── QUICKSTART.md               # Quick start guide
├── README.md                   # Main project documentation
├── requirements.txt            # Python dependencies
├── SETUP_CHECKLIST.md          # Setup checklist
└── utxoIQ.code-workspace       # VS Code workspace
```

## Documentation (`docs/`)

### Active Documentation
```
docs/
├── README.md                                    # Documentation index
├── ADMIN-SETUP.md                              # Admin configuration
├── api-authentication-quick-reference.md       # Auth quick reference
├── api-reference-auth.md                       # Auth API reference
├── authentication-guide.md                     # Authentication guide
├── bigquery-buffer-management.md               # BigQuery buffer management
├── bigquery-hybrid-strategy.md                 # BigQuery hybrid approach
├── bigquery-migration-guide.md                 # BigQuery migration
├── bitcoin-core-setup.md                       # Bitcoin Core setup
├── cleanup-summary.md                          # Cleanup documentation
├── database-api-documentation.md               # Database API docs
├── database-deployment-guide.md                # Database deployment
├── database-schema.md                          # Database schema
├── directory-structure.md                      # This file
├── docker-development.md                       # Docker development
├── firebase-custom-domains-setup.md            # Firebase domains
├── firebase-multi-environment-setup.md         # Firebase environments
├── firebase-oauth-configuration.md             # Firebase OAuth
├── firebase-quick-start.md                     # Firebase quick start
├── firebase-setup-guide.md                     # Firebase setup
├── find-umbrel-credentials.md                  # Umbrel credentials
├── frontend-api-integration.md                 # Frontend integration
├── historical-block-processing.md              # Historical data
├── integration-diagram.md                      # Architecture diagram
├── integration-roadmap.md                      # Development roadmap
├── local-development-setup.md                  # Local dev setup
├── local-monitor-setup.md                      # Monitor setup
├── monitoring-alert-configuration.md           # Monitoring alerts
├── monitoring-best-practices.md                # Monitoring practices
├── monitoring-custom-dashboards.md             # Custom dashboards
├── monitoring-distributed-tracing.md           # Distributed tracing
├── monitoring-log-search.md                    # Log search
├── monitoring-notification-channels.md         # Notifications
├── project-organization.md                     # Project structure
├── quick-reference.md                          # Quick reference
├── quick-start.md                              # Quick start
├── run-migrations-guide.md                     # Migrations
├── security-best-practices.md                  # Security practices
├── test-migration-guide.md                     # Test migration
├── test-organization-guide.md                  # Test organization
├── tor-setup-windows.md                        # Tor setup
├── ui-ux-features-guide.md                     # UI/UX features
├── unified-platform-integration.md             # Platform integration
├── web-api-deployment.md                       # Web API deployment
├── web-api-prerequisites.md                    # Web API prerequisites
└── WEBSOCKET_INFO.md                           # WebSocket info
```

### Subdirectories
```
docs/
├── archive/                    # Historical/completed documentation
├── implementation/             # Task implementation notes
└── specs/                      # Detailed specifications
```

## Scripts (`scripts/`)

```
scripts/
├── README.md                   # Scripts documentation
├── bigquery/                   # BigQuery operations
│   ├── cleanup-old-data.sh
│   ├── create-hybrid-dataset.sh
│   ├── create-unified-views.sh
│   └── test-hybrid-queries.sh
├── data/                       # Data management
│   ├── analyze-blocks.py
│   ├── backfill-*.py
│   ├── create-bigquery-*.py
│   ├── create-tables.*
│   ├── generate-insight*.py
│   ├── populate_treasury_entities.py
│   ├── quick-seed-insights.py
│   ├── recreate-tables.py
│   ├── run-migrations.*
│   ├── seed-insights-data.py
│   ├── setup-bigquery*.py
│   └── update-views-1hr-buffer.py
├── deployment/                 # Deployment automation
│   ├── block-monitor.py
│   ├── deploy-*.bat
│   ├── deploy-*.sh
│   ├── dev-docker*.bat
│   ├── monitor-blocks.py
│   ├── rebuild-backend.bat
│   ├── run-block-monitor.bat
│   ├── start-api.*
│   ├── start-block-monitor.bat
│   └── START-MONITOR.bat
├── setup/                      # Environment setup
│   ├── create-signal-tables.*
│   ├── install-monitor-service.ps1
│   ├── install-task-scheduler.ps1
│   ├── local-dev.sh
│   ├── setup-admin-firestore.js
│   ├── setup-block-monitor-service.ps1
│   ├── setup-cleanup-scheduler.bat
│   ├── setup-cloud-scheduler.*
│   ├── setup-cloud-sql.bat
│   ├── setup-custom-domain*.* 
│   ├── setup-firebase-admin.js
│   ├── setup-gcp.ps1
│   └── setup-retention-scheduler.*
└── testing/                    # Testing and verification
    ├── check-insights.py
    ├── compare-schemas.py
    ├── get-nested-schema.py
    ├── inspect-public-schema.py
    ├── test-*.py
    ├── verify-*.py
    └── verify-project-structure.py
```

## Tests (`tests/`)

```
tests/
├── README.md                   # Testing documentation
├── unit/                       # Cross-service utility tests
├── integration/                # Multi-service integration tests
├── e2e/                        # End-to-end user workflows
│   ├── block-to-insight-flow.e2e.test.py
│   ├── helpers.py
│   ├── pytest.ini
│   ├── README.md
│   └── requirements.txt
├── performance/                # System-wide performance tests
└── security/                   # Platform-wide security tests
```

## Services (`services/`)

```
services/
├── chart-renderer/
│   ├── src/
│   ├── tests/                  # 4 tests (unit + integration)
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── data-ingestion/
│   ├── src/
│   ├── tests/                  # 1 test (unit)
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── email-service/
│   ├── src/
│   ├── tests/                  # 6 tests (unit + integration)
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── insight-generator/
│   ├── src/
│   ├── tests/                  # 5 tests (unit + integration)
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── utxoiq-ingestion/
│   ├── src/
│   ├── tests/                  # 6 tests (unit + integration)
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── web-api/
│   ├── src/
│   ├── tests/                  # 39 tests (unit + integration)
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
└── x-bot/
    ├── src/
    ├── tests/                  # 5 tests (unit + integration)
    ├── Dockerfile
    ├── pytest.ini
    └── requirements.txt
```

## Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   ├── components/             # React components
│   ├── lib/                    # Utilities
│   ├── hooks/                  # Custom hooks
│   └── types/                  # TypeScript types
├── public/                     # Static assets
├── tests/                      # Frontend tests
├── next.config.js
├── package.json
└── tailwind.config.js
```

## Infrastructure (`infrastructure/`)

```
infrastructure/
├── terraform/                  # GCP resource definitions
├── bigquery/                   # BigQuery schemas
└── dataflow/                   # Data pipeline definitions
```

## Shared (`shared/`)

```
shared/
├── types/                      # Common TypeScript types
├── schemas/                    # Data validation schemas
└── utils/                      # Shared utilities
```

## Other Directories

```
.github/                        # GitHub Actions workflows
.kiro/                          # Kiro IDE configuration
  ├── specs/                    # Kiro-managed specifications
  └── steering/                 # Steering documents
.vscode/                        # VS Code settings
data/                           # Data files
logs/                           # Log files
temp/                           # Temporary files
venv/, venv312/                 # Python virtual environments
```

## Quick Navigation

### I want to...
- **Add a new script** → `scripts/{setup|deployment|data|testing}/`
- **Add documentation** → `docs/`
- **Add a service test** → `services/{service-name}/tests/`
- **Add a system test** → `tests/{unit|integration|e2e|performance|security}/`
- **Archive old docs** → `docs/archive/`
- **Find implementation notes** → `docs/implementation/`
- **Find specifications** → `docs/specs/` or `.kiro/specs/`

## Verification

Run structure verification:
```bash
python scripts/testing/verify-project-structure.py
```

This checks:
- Root directory cleanliness
- Test naming conventions
- Documentation organization
- Scripts organization
- Service test patterns
