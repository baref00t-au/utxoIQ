# utxoIQ

AI-powered Bitcoin blockchain intelligence platform with real-time monitoring and insights.

## 🎉 Platform Integration Complete!

A unified dashboard bringing together all platform components with:
- ✅ Real-time system monitoring
- ✅ User feedback system
- ✅ Backfill progress tracking
- ✅ Live WebSocket updates
- ✅ Comprehensive metrics

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Frontend
```bash
npm run dev
```

### 3. Open Dashboard
```
http://localhost:3000/dashboard
```

### 4. Start Backend (Optional - for live data)
```bash
docker-compose up -d
```

## 📊 Dashboard Features

### System Status Tab
- Live service health monitoring
- Backfill progress with ETA
- Processing metrics (24h blocks, insights, signals)
- Performance metrics
- WebSocket connection indicator

### Insights Tab
- Real-time insight feed
- User feedback (ratings, comments, flags)
- Aggregated statistics

### Metrics Tab
- Signal generation by category
- Insight generation statistics
- Historical trends

## 🔌 WebSocket Connection

The dashboard uses WebSocket for real-time updates. You'll see:
- 🟢 **Green WiFi icon** = Connected (live updates)
- ⚪ **Gray WiFi icon** = Disconnected (API not running)

**Note:** WebSocket errors in console are normal when the API isn't running. The dashboard works fine without the API, just without live data.

See [docs/WEBSOCKET_INFO.md](docs/WEBSOCKET_INFO.md) for details.

## 📚 Documentation

### Getting Started
- **[Integration Complete](INTEGRATION_COMPLETE.md)** - What was built
- **[Setup Checklist](SETUP_CHECKLIST.md)** - Complete setup guide
- **[Build Success](BUILD_SUCCESS.md)** - Build details
- **[Quick Reference](docs/quick-reference.md)** - Commands and API reference

### Authentication & Security
- **[Authentication Guide](docs/authentication-guide.md)** - Complete authentication documentation
- **[API Authentication Quick Reference](docs/api-authentication-quick-reference.md)** - Quick start guide
- **[API Reference - Auth](docs/api-reference-auth.md)** - Authentication endpoints
- **[Security Best Practices](docs/security-best-practices.md)** - Security guidelines

### Integration
- **[WebSocket Info](docs/WEBSOCKET_INFO.md)** - WebSocket connection guide
- **[Integration Guide](docs/unified-platform-integration.md)** - Comprehensive guide
- **[Integration Roadmap](docs/integration-roadmap.md)** - Development roadmap

## 🏗️ Architecture

```
Frontend (Next.js 16)
    ↓ WebSocket + REST
Web API (FastAPI)
    ↓
Backend Services
    ├── Feature Engine
    ├── Insight Generator
    ├── Data Ingestion
    └── Chart Renderer
    ↓
Data Storage
    ├── PostgreSQL
    ├── BigQuery
    └── Redis
```

## 🔧 Development

### Frontend Only
```bash
cd frontend
npm run dev
```
Dashboard works, no live data.

### Full Stack
```bash
# Terminal 1: Backend
docker-compose up -d

# Terminal 2: Frontend
cd frontend
npm run dev
```
Dashboard with live data and WebSocket updates.

## 🧪 Testing

```bash
# Frontend tests
cd frontend
npm test

# Integration tests
python scripts/test-integration.py

# Build test
cd frontend
npm run build
```

## 📦 What's Included

- **Backend**: 7 new files (monitoring, feedback, WebSocket)
- **Frontend**: 8 new files (dashboard, components, hooks)
- **Scripts**: 2 new files (backfill, tests)
- **Documentation**: 10+ comprehensive guides

## 🎯 Status

- ✅ Phase 1: Core Integration Complete
- ✅ Phase 2: Database & Persistence Complete
- ✅ Phase 3: Authentication & Authorization Complete
- 📅 Phase 4: Advanced Monitoring (Next)

See [docs/integration-roadmap.md](docs/integration-roadmap.md) for full roadmap.

## 📞 Support

- **Documentation**: See `docs/` directory
- **GitHub Issues**: https://github.com/utxoiq/utxoiq/issues
- **Email**: support@utxoiq.com

---

**Ready to use!** Start with `cd frontend && npm run dev` and visit http://localhost:3000/dashboard