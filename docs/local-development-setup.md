# Local Development Setup Guide

## Prerequisites

✅ **Already Installed:**
- Python 3.14
- Bitcoin Core node (Umbrel at umbrel.local:8332)
- Node.js (for frontend, when needed)

🔄 **Installing:**
- Docker Desktop for Windows

## Step 1: Install Docker Desktop

1. Download from: https://www.docker.com/products/docker-desktop/
2. Install and restart your computer if prompted
3. Start Docker Desktop
4. Verify installation: `docker --version`

## Step 2: Start Local Services

Once Docker is installed, start the local infrastructure:

```bash
# From the project root
docker-compose up -d
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **BigQuery Emulator** on port 9050
- **Pub/Sub Emulator** on port 8085

### Verify Services Are Running

```bash
# Check running containers
docker-compose ps

# Check logs
docker-compose logs -f
```

## Step 3: Verify Your .env Configuration

Your `.env` file should already be configured with:

```bash
# Bitcoin Core (Umbrel)
BITCOIN_RPC_HOST=umbrel.local
BITCOIN_RPC_PORT=8332
BITCOIN_RPC_USER=umbrel
BITCOIN_RPC_PASSWORD=your_password

# PostgreSQL (Docker)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=utxoiq_db
POSTGRES_USER=utxoiq
POSTGRES_PASSWORD=utxoiq_dev_password

# Redis (Docker)
REDIS_HOST=localhost
REDIS_PORT=6379

# GCP (for local emulators)
GCP_PROJECT_ID=utxoiq-local
```

## Step 4: Test Bitcoin Connection

```bash
cd services/data-ingestion
python test_connection.py
```

Expected output:
```
✓ Connected successfully!
✓ Current block height: 922,XXX
✓ Mempool size: XXX transactions
```

## Step 5: Run the Data Ingestion Service

```bash
cd services/data-ingestion
python src/main.py
```

This will:
- Connect to your Umbrel Bitcoin node
- Monitor for new blocks
- Detect mempool anomalies
- Stream data to Pub/Sub (local emulator)

Expected logs:
```
INFO - Starting blockchain ingestion service...
INFO - Starting from block height: 922582
INFO - Processed block 922583 (2945 transactions)
INFO - Published mempool snapshot to Pub/Sub
```

## Common Commands

### Docker Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart a specific service
docker-compose restart postgres

# Remove all data (fresh start)
docker-compose down -v
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it utxoiq-postgres psql -U utxoiq -d utxoiq_db

# List tables
\dt

# Query users
SELECT * FROM users;

# Exit
\q
```

### Redis Access

```bash
# Connect to Redis
docker exec -it utxoiq-redis redis-cli

# Check keys
KEYS *

# Get a value
GET some_key

# Exit
exit
```

## Troubleshooting

### Docker Not Starting

**Issue**: Docker containers won't start
**Solution**: 
1. Ensure Docker Desktop is running
2. Check if ports are already in use: `netstat -ano | findstr :5432`
3. Restart Docker Desktop

### PostgreSQL Connection Failed

**Issue**: Can't connect to PostgreSQL
**Solution**:
```bash
# Check if container is running
docker ps | findstr postgres

# Check logs
docker logs utxoiq-postgres

# Restart container
docker-compose restart postgres
```

### Bitcoin Connection Failed

**Issue**: Can't connect to Umbrel node
**Solution**:
1. Verify Umbrel is running: `ping umbrel.local`
2. Check RPC credentials in `.env`
3. Test with: `python services/data-ingestion/test_connection.py`

### Port Already in Use

**Issue**: Port 5432 (or other) already in use
**Solution**:
```bash
# Find what's using the port
netstat -ano | findstr :5432

# Kill the process (replace PID)
taskkill /PID <process_id> /F

# Or change the port in docker-compose.yml
```

## Development Workflow

### Typical Development Session

1. **Start Docker services**
   ```bash
   docker-compose up -d
   ```

2. **Verify services are healthy**
   ```bash
   docker-compose ps
   ```

3. **Run data ingestion service**
   ```bash
   cd services/data-ingestion
   python src/main.py
   ```

4. **In another terminal, monitor logs**
   ```bash
   docker-compose logs -f
   ```

5. **When done, stop services**
   ```bash
   docker-compose down
   ```

### Running Tests

```bash
# Python tests
cd services/data-ingestion
pytest

# TypeScript tests (shared module)
cd shared
npm test
```

## What's Next?

After local development is set up:

1. ✅ **Task 1 Complete** - Infrastructure and data models
2. 🔄 **Task 2** - Implement Feature Engine for signal processing
3. 🔄 **Task 3** - Build Insight Generator with Vertex AI
4. 🔄 **Task 4** - Create Chart Renderer service
5. 🔄 **Task 5** - Build Web API service
6. 🔄 **Task 6** - Develop Next.js frontend

## Quick Reference

| Service | Port | Access |
|---------|------|--------|
| PostgreSQL | 5432 | `psql -h localhost -U utxoiq -d utxoiq_db` |
| Redis | 6379 | `redis-cli -h localhost` |
| BigQuery Emulator | 9050 | HTTP API |
| Pub/Sub Emulator | 8085 | HTTP API |
| Bitcoin Core (Umbrel) | 8332 | RPC via Python client |

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)
- [Bitcoin Core RPC](https://developer.bitcoin.org/reference/rpc/)
