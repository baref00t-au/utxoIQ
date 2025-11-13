# Project Organization

## Directory Structure

### Documentation (`docs/`)
```
docs/
├── README.md                    # Documentation index
├── implementation/              # Task implementation notes
├── archive/                     # Historical/completed documentation
├── specs/                       # Detailed specifications
└── *.md                        # Active documentation files
```

**Guidelines:**
- Keep active documentation in `docs/` root
- Move implementation notes to `docs/implementation/`
- Archive completed/historical docs in `docs/archive/`
- Use descriptive kebab-case filenames

### Scripts (`scripts/`)
```
scripts/
├── README.md                    # Scripts documentation
├── setup/                       # Environment setup scripts
├── deployment/                  # Deployment automation
├── data/                        # Data management scripts
├── testing/                     # Testing and verification
└── bigquery/                    # BigQuery operations
```

**Guidelines:**
- Organize by purpose (setup, deployment, data, testing)
- Use kebab-case for filenames
- Provide both `.sh` and `.bat` versions when possible
- Include clear usage documentation

### Tests (`tests/`)
```
tests/
├── README.md                    # Testing documentation
├── unit/                        # Cross-service utility tests
├── integration/                 # Multi-service integration tests
├── e2e/                         # End-to-end user workflow tests
├── performance/                 # System-wide performance tests
└── security/                    # Platform-wide security tests
```

**Root Tests Focus:**
- Cross-service workflows and integration
- Complete user journeys (e.g., signup → insight → alert)
- System-level performance and load testing
- Platform-wide security testing

**Test Naming Conventions:**
- Unit: `*.unit.test.py` or `*.unit.test.ts`
- Integration: `*.integration.test.py` or `*.integration.test.ts`
- E2E: `*.e2e.test.py` or `*.e2e.test.ts`
- Performance: `*.performance.test.py` or `*.performance.test.ts`
- Security: `*.security.test.py` or `*.security.test.ts`

**Note:** Service-specific tests live in `services/{service-name}/tests/`

### Services (`services/`)
```
services/
├── utxoiq-ingestion/
│   ├── src/                     # Source code
│   ├── tests/                   # Service-specific tests (unit + integration)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
├── feature-engine/
├── insight-generator/
├── chart-renderer/
├── web-api/
└── x-bot/
```

**Service Test Organization:**
- Tests stay within each service directory (colocation principle)
- Follow same naming conventions as root tests
- Use pytest.ini for service-specific configuration
- Focus on service-specific unit and integration tests
- Test service in isolation with mocked external dependencies

**Service Tests:**
- Follow same naming conventions as root tests
- Keep tests within service directory
- Use pytest.ini for service-specific configuration

### Frontend (`frontend/`)
```
frontend/
├── src/
│   ├── app/                     # Next.js App Router
│   ├── components/              # React components
│   ├── lib/                     # Utilities
│   ├── hooks/                   # Custom hooks
│   └── types/                   # TypeScript types
├── public/                      # Static assets
└── tests/                       # Frontend tests
```

### Shared (`shared/`)
```
shared/
├── types/                       # Common TypeScript types
├── schemas/                     # Data validation schemas
└── utils/                       # Shared utilities
```

### Infrastructure (`infrastructure/`)
```
infrastructure/
├── terraform/                   # GCP resource definitions
├── bigquery/                    # BigQuery schemas
└── dataflow/                    # Data pipeline definitions
```

## Root Directory

**Keep root directory clean!** Only these files should be in root:

### Configuration Files
- `.env`, `.env.example`
- `docker-compose.yml`, `docker-compose.*.yml`
- `package.json`, `package-lock.json`
- `requirements.txt`
- `pytest.ini`
- `.gitignore`
- `*.code-workspace`

### Documentation
- `README.md` - Main project documentation
- `QUICKSTART.md` - Quick start guide
- `AGENTS.md` - AI agent guidelines
- `SETUP_CHECKLIST.md` - Setup checklist

### Build/Deploy
- `Dockerfile` (if applicable)
- `cloudbuild.yaml` (if applicable)

### Temporary Files
- Use `temp/` directory for temporary files
- Add to `.gitignore`

## File Naming Conventions

### Python Files
- **Modules**: `snake_case.py`
- **Tests**: `*.unit.test.py`, `*.integration.test.py`, etc.
- **Scripts**: `kebab-case.py`

### TypeScript/JavaScript Files
- **Components**: `PascalCase.tsx`
- **Utilities**: `camelCase.ts`
- **Tests**: `*.unit.test.ts`, `*.integration.test.ts`, etc.
- **Config**: `kebab-case.config.ts`

### Shell Scripts
- **Bash**: `kebab-case.sh`
- **Batch**: `kebab-case.bat`
- **PowerShell**: `kebab-case.ps1`

### Documentation
- **Markdown**: `kebab-case.md`
- **Specs**: Use numbered format in `docs/specs/` (e.g., `utxo-001/`)

### Directories
- **All directories**: `kebab-case/`

## Best Practices

### Documentation
1. Keep documentation up-to-date
2. Use clear, descriptive filenames
3. Include README.md in each major directory
4. Archive old documentation instead of deleting
5. Link related documents

### Scripts
1. Make scripts idempotent (safe to run multiple times)
2. Include error handling
3. Add usage documentation
4. Use environment variables for configuration
5. Provide cross-platform versions when possible

### Tests
1. **Service tests** stay in `services/{name}/tests/` (colocation)
2. **System tests** go in root `tests/` directory (cross-service)
3. Use descriptive test names that explain what's being tested
4. Keep tests isolated and independent
5. Mock external dependencies in unit tests
6. Maintain 80%+ code coverage for critical paths

### Code Organization
1. Follow single responsibility principle
2. Keep related code together
3. Use clear, consistent naming
4. Document complex logic
5. Separate concerns (client/server, business/presentation)

## Migration Notes

Recent organizational changes:
- Moved task implementation docs to `docs/implementation/`
- Archived completed documentation in `docs/archive/`
- Organized scripts by purpose (setup, deployment, data, testing)
- Standardized test naming conventions
- Created README files for major directories
- Updated pytest configurations for new test patterns
