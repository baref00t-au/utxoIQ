# utxoIQ Project Structure

## Directory Organization

```
utxoiq/
├── .git/                           # Git repository
├── .kiro/                          # Kiro IDE configuration
│   ├── specs/                      # Kiro-managed specifications
│   │   └── utxoiq-mvp/            # MVP spec (DO NOT MOVE)
│   │       ├── requirements.md
│   │       ├── design.md
│   │       └── tasks.md
│   └── steering/                   # Kiro steering rules
│
├── docs/                           # Documentation
│   ├── specs/                      # Supplementary spec documentation
│   │   └── utxo-001/              # Additional implementation notes
│   ├── task-1-implementation.md   # Task completion summaries
│   └── project-structure.md       # This file
│
├── scripts/                        # All scripts
│   ├── setup/                      # Setup scripts
│   │   └── local-dev.sh
│   └── test-bitcoin-connection.bat # Test utilities
│
├── temp/                           # Temporary files and test outputs
│
├── infrastructure/                 # Infrastructure as Code
│   ├── bigquery/                   # BigQuery schemas and setup
│   ├── postgres/                   # PostgreSQL schemas
│   ├── dataflow/                   # Data pipeline definitions
│   └── README.md
│
├── services/                       # Backend microservices
│   └── data-ingestion/            # Bitcoin data ingestion service
│       ├── src/
│       ├── tests/
│       ├── requirements.txt
│       └── Dockerfile
│
├── shared/                         # Shared code and types
│   ├── types/                      # TypeScript interfaces
│   ├── schemas/                    # Zod validation schemas
│   ├── utils/                      # Shared utilities
│   └── tests/                      # Unit tests
│
├── frontend/                       # Next.js frontend (to be created)
│
├── .env                           # Environment variables (gitignored)
├── .env.example                   # Environment template
├── docker-compose.yml             # Local development services
├── AGENTS.md                      # AI agent guidelines
├── README.md                      # Project overview
└── utxoIQ.code-workspace         # VS Code workspace
```

## File Organization Rules

### Root Directory
**Only these files should be in root:**
- Core config files (`.env`, `docker-compose.yml`, `package.json`)
- `README.md`
- `AGENTS.md`
- `.gitignore`
- License files
- Workspace files

### Where to Put Files

| File Type | Location | Example |
|-----------|----------|---------|
| Documentation | `docs/` | `docs/api-guide.md` |
| Spec supplements | `docs/specs/utxo-XXX/` | `docs/specs/utxo-001/notes.md` |
| Scripts | `scripts/` | `scripts/deploy.sh` |
| Temporary files | `temp/` | `temp/test-output.json` |
| Kiro specs | `.kiro/specs/` | `.kiro/specs/utxoiq-mvp/` |

### Kiro Specs
- **Location**: `.kiro/specs/`
- **Managed by**: Kiro IDE
- **Do NOT**: Move, rename, or duplicate these files
- **Contains**: `requirements.md`, `design.md`, `tasks.md`

### Supplementary Documentation
- **Location**: `docs/specs/utxo-XXX/`
- **Purpose**: Implementation notes, research, diagrams
- **Naming**: Use numbered format (utxo-001, utxo-002, etc.)

## Service Structure

Each service follows this pattern:

```
services/service-name/
├── src/                    # Source code
│   ├── main.py            # Entry point
│   ├── config.py          # Configuration
│   ├── models/            # Data models
│   ├── routes/            # API routes
│   └── utils/             # Utilities
├── tests/                 # Unit tests
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
└── README.md             # Service documentation
```

## Naming Conventions

### Files
- **Python**: `snake_case.py`
- **TypeScript**: `camelCase.ts` or `camelCase.tsx`
- **Directories**: `kebab-case/`
- **Config**: `kebab-case.yml`

### Code
- **Python variables/functions**: `snake_case`
- **Python classes**: `PascalCase`
- **Python constants**: `UPPER_SNAKE_CASE`
- **TypeScript variables/functions**: `camelCase`
- **TypeScript types/interfaces**: `PascalCase`
- **TypeScript constants**: `UPPER_SNAKE_CASE`
- **React components**: `PascalCase`

### Database
- **Tables**: `snake_case`
- **Columns**: `snake_case`
- **API endpoints**: `/kebab-case`
- **JSON fields**: `camelCase`

### Cloud Resources
- **GCP services**: `kebab-case`
- **BigQuery datasets**: `snake_case`
- **BigQuery tables**: `snake_case`
- **Pub/Sub topics**: `kebab-case`
- **Storage buckets**: `kebab-case`

## Quick Reference

### Running Tests
```bash
# TypeScript tests
cd shared && npm test

# Python tests
cd services/data-ingestion && pytest

# Test Bitcoin connection
cd scripts && ./test-bitcoin-connection.bat
```

### Local Development
```bash
# Start infrastructure
docker-compose up -d

# Start data ingestion
cd services/data-ingestion && python src/main.py
```

### Deployment
```bash
# Deploy to GCP
cd scripts && ./deploy.sh

# Setup BigQuery
cd infrastructure/bigquery && ./setup.sh
```
