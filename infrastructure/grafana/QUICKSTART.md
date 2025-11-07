# Grafana Observability Quick Start

Get the utxoIQ observability stack running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- 4GB RAM available
- Ports 3000 and 9090 available

## Quick Start

### 1. Setup Environment

```bash
cd infrastructure/grafana

# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional for local dev)
nano .env
```

### 2. Start Services

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

### 3. Access Dashboards

Open your browser:
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

Default credentials:
- Username: `admin`
- Password: `admin` (change on first login)

### 4. View Dashboards

In Grafana, navigate to:
1. **Dashboards** → **Browse**
2. Select **utxoIQ** folder
3. Choose a dashboard:
   - Performance Monitoring
   - Cost Tracking & Analytics
   - Accuracy & Feedback

## Instrument Your Service

Add metrics to your FastAPI service:

```python
from fastapi import FastAPI
from infrastructure.grafana.metrics_instrumentation import (
    setup_metrics_endpoint,
    track_http_request,
    BlockProcessingTimer
)

app = FastAPI()
setup_metrics_endpoint(app)

@app.post("/process-block")
async def process_block(block_data: dict):
    with BlockProcessingTimer():
        # Your processing logic
        result = await process_block_data(block_data)
    
    track_http_request("POST", "/process-block", 200, "feature-engine")
    return result
```

## Validate Setup

```bash
# Run validation script
python validate.py

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f
```

## Common Issues

### Port Already in Use

```bash
# Check what's using the port
lsof -i :3000
lsof -i :9090

# Stop conflicting services or change ports in docker-compose.yml
```

### Grafana Won't Start

```bash
# Check logs
docker-compose logs grafana

# Reset and restart
docker-compose down -v
docker-compose up -d
```

### No Metrics Showing

1. Verify services are exposing `/metrics` endpoint
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify service URLs in `prometheus.yml`

## Next Steps

- [Full Documentation](README.md)
- [Production Deployment](DEPLOYMENT.md)
- [Metrics Instrumentation Guide](metrics_instrumentation.py)

## Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```
