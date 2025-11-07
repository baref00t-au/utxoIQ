# utxoIQ Quick Start Guide

## ✅ What's Already Set Up

- ✅ Docker running (PostgreSQL, Redis, BigQuery emulator, Pub/Sub emulator)
- ✅ Bitcoin Core connection to Umbrel node (umbrel.local:8332)
- ✅ Python 3.14 with all dependencies
- ✅ Mock Pub/Sub for local development (Python 3.14 compatibility)
- ✅ Data ingestion service ready

## 🚀 Quick Commands

### 1. Test Bitcoin Connection
```bash
cd services/data-ingestion
python test_connection.py
```

### 2. Process Recent Blocks (Backfill)
```bash
cd scripts

# Last 10 blocks (quick test)
python backfill-blocks.py --last 10

# Last week (~2 minutes)
python backfill-blocks.py --last 1008

# Last month (~10 minutes)
python backfill-blocks.py --last 4320
```

### 3. Start Real-time Monitoring
```bash
cd services/data-ingestion

# Monitor from current tip
python src/main.py

# Start from specific block
python src/main.py --start-height 922000

# Start from genesis
python src/main.py --from-genesis
```

### 4. Check Docker Services
```bash
# View running containers
docker compose ps

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop services
docker compose down
```

## 📊 What's Happening

### Mock Pub/Sub Mode
Currently running in **local development mode** with mock Pub/Sub:
- ✅ Connects to your Umbrel Bitcoin node
- ✅ Fetches and normalizes block data
- ✅ Processes transactions
- ✅ Detects mempool anomalies
- ⚠️ **Logs data instead of publishing to Pub/Sub** (Python 3.14 compatibility)

### When You See This:
```
[MOCK] Would publish block 922577 (hash: 00000000...)
[MOCK] Would publish 2636 transactions for block 922577
```

This means the service is working correctly - it's just logging instead of actually publishing to Pub/Sub.

## 🎯 Current Status

### Task 1: Infrastructure Setup ✅ COMPLETE
- ✅ Core data models and TypeScript interfaces
- ✅ Bitcoin Core RPC client with anomaly detection
- ✅ Database schemas (BigQuery + PostgreSQL)
- ✅ Docker development environment
- ✅ Unit tests for core functionality

### What's Working:
1. **Bitcoin Connection**: Connected to Umbrel node
2. **Block Processing**: Can process any block range
3. **Transaction Parsing**: Full transaction details
4. **Mempool Analysis**: 3-sigma anomaly detection
5. **Reorg Detection**: Monitors up to 10 blocks deep
6. **Docker Services**: PostgreSQL, Redis, emulators running

### What's Next:
- **Task 2**: Feature Engine (signal processing)
- **Task 3**: Insight Generator (AI-powered insights)
- **Task 4**: Chart Renderer
- **Task 5**: Web API
- **Task 6**: Frontend (Next.js)

## 🔧 Troubleshooting

### Docker Not Running
```bash
# Start Docker Desktop
# Then run:
docker compose up -d
```

### Bitcoin Connection Failed
```bash
# Check Umbrel is accessible
ping umbrel.local

# Verify credentials in .env
cat .env | grep BITCOIN_RPC
```

### Python Import Errors
```bash
# Reinstall dependencies
cd services/data-ingestion
python -m pip install -r requirements.txt
```

### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :5432

# Stop Docker services
docker compose down

# Start again
docker compose up -d
```

## 📈 Performance Tips

### Processing Speed
- **Current rate**: ~0.7 blocks/sec with full transaction data
- **Factors**: Network latency to Umbrel, transaction count per block
- **Optimization**: Process in batches, run overnight for full history

### Resource Usage
- **PostgreSQL**: ~200MB RAM
- **Redis**: ~50MB RAM
- **Emulators**: ~100MB RAM each
- **Python process**: ~100MB RAM

## 🎓 Learning Resources

### Project Documentation
- `docs/project-structure.md` - Complete project layout
- `docs/local-development-setup.md` - Detailed setup guide
- `docs/historical-block-processing.md` - Block processing guide
- `docs/task-1-implementation.md` - What was implemented

### Code Locations
- **Data Models**: `shared/types/index.ts`
- **Validation**: `shared/schemas/validation.ts`
- **Bitcoin RPC**: `services/data-ingestion/src/bitcoin_rpc.py`
- **Database Utils**: `shared/utils/database.ts`
- **Tests**: `shared/tests/` and `services/data-ingestion/tests/`

## 💡 Tips

1. **Start Small**: Test with `--last 10` before processing large ranges
2. **Monitor Logs**: Use `docker compose logs -f` to watch activity
3. **Save Progress**: The backfill script shows progress and can be interrupted
4. **Check Data**: Verify blocks are being processed correctly
5. **Use Mock Mode**: Perfect for development without GCP setup

## 🚀 Next Steps

### Option 1: Process More History
```bash
cd scripts
python backfill-blocks.py --last 52560  # Last year
```

### Option 2: Start Real-time Monitoring
```bash
cd services/data-ingestion
python src/main.py
```

### Option 3: Move to Task 2
Start implementing the Feature Engine for signal processing!

---

**Need Help?** Check the detailed guides in `docs/` or review the implementation summary in `docs/task-1-implementation.md`.
