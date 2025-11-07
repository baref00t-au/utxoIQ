# Technology Stack

## Cloud Platform
- **Google Cloud Platform (GCP)** - Primary cloud infrastructure
- **Cloud Run** - Serverless containers for stateless services
- **Cloud Functions** - Event-driven processing
- **GKE** - Kubernetes cluster for Bitcoin Core node

## Data Infrastructure
- **BigQuery** - Data warehouse for blockchain analytics
- **Cloud SQL (PostgreSQL)** - Transactional data storage
- **Cloud Storage** - Chart images and static assets
- **Redis (Memorystore)** - Caching and rate limiting
- **Cloud Pub/Sub** - Real-time data streaming

## AI & Machine Learning
- **Vertex AI** - AI platform with Gemini Pro model
- **Custom ML Models** - Signal processing and anomaly detection

## Backend Services
- **FastAPI** - Python web framework for APIs
- **Python** - Primary backend language
- **TypeScript** - Type-safe JavaScript for shared models

## Frontend
- **Next.js 16** - App Router, Server Components, ISR for performance
- **TypeScript** - Strict configuration for type safety
- **Tailwind CSS** - Utility-first CSS with CSS variables for theming
- **shadcn/ui** - Accessible UI components built on Radix primitives
- **Framer Motion** - Animation library for micro-interactions
- **Recharts** - Chart library (migrate to ECharts/D3 for custom viz)
- **TanStack Query** - Server state management and caching
- **Zustand** - Lightweight client state management
- **react-hook-form + zod** - Form handling and validation
- **TanStack Table** - Virtualized tables for large datasets
- **lucide-react** - Icon library
- **Playwright + Vitest** - End-to-end and unit testing

## Authentication & Payments
- **Firebase Auth** - User authentication
- **Stripe** - Payment processing and subscription management

## External Integrations
- **Bitcoin Core** - Blockchain data source via RPC
- **X API v2** - Social media automation

## Development Tools
- **Docker** - Containerization
- **GitHub Actions** - CI/CD pipeline
- **Cloud Build** - GCP build service

## Common Commands

### Development Setup
```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Start local development
npm run dev
python -m uvicorn main:app --reload

# Run tests
npm test              # Vitest unit tests
npm run test:e2e      # Playwright e2e tests
pytest                # Python backend tests

# Build containers
docker build -t utxoiq-api .
docker build -t utxoiq-frontend .
```

### Deployment
```bash
# Deploy to Cloud Run
gcloud run deploy utxoiq-api --source .
gcloud run deploy utxoiq-frontend --source .

# Deploy Cloud Functions
gcloud functions deploy process-block --runtime python39

# Update BigQuery schemas
bq mk --dataset utxoiq:btc
bq mk --dataset utxoiq:intel
```

### Data Operations
```bash
# Query BigQuery
bq query --use_legacy_sql=false "SELECT * FROM btc.blocks LIMIT 10"

# Stream to Pub/Sub
gcloud pubsub topics publish btc.blocks --message="block_data"

# Check Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision"
```