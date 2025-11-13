# utxoIQ Quick Start Guide

## ✅ Prerequisites Installed

- ✅ Python 3.12.10
- ✅ Node.js 18+
- ✅ Docker Desktop
- ✅ All dependencies installed

## 🚀 Start the Platform

### Terminal 1: Frontend (Already Running)
```powershell
# Frontend is already running at http://localhost:3000
# Dashboard: http://localhost:3000/dashboard
```

### Terminal 2: Start Web API
```powershell
# From project root
cd services\web-api
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

Or use the script:
```powershell
.\scripts\start-api.ps1
```

### Terminal 3: Run Backfill (Optional)
```powershell
# Wait for API to start, then run backfill
python scripts\backfill-with-progress.py --start 870000 --end 870100 --batch-size 10
```

## 📊 Access Points

- **Frontend**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard
- **API Docs**: http://localhost:8080/docs
- **API Health**: http://localhost:8080/health

## 🔍 What to Expect

### Dashboard Features
- **System Status Tab**: Service health, backfill progress
- **Insights Tab**: Real-time insight feed with user feedback
- **Metrics Tab**: Signal and insight generation statistics

### WebSocket Connection
- 🟢 **Green WiFi icon** = Connected (live updates)
- ⚪ **Gray WiFi icon** = Disconnected (API not running)

## 🐛 Troubleshooting

### API Won't Start
```powershell
# Check if port 8080 is in use
netstat -ano | findstr :8080

# Check Docker services are running
docker ps

# Check you're in the right directory
cd services\web-api
```

### Frontend Shows Errors
```powershell
# Restart frontend
cd frontend
npm run dev
```

### Database Connection Issues
```powershell
# Restart Docker services
docker-compose restart

# Check PostgreSQL is healthy
docker ps | findstr postgres
```

## 📝 Configuration Files

- **Frontend**: `frontend/.env.local`
- **Web API**: `services/web-api/.env`
- **Root**: `.env` (for shared config)

## 🎯 Next Steps

1. **Start API** (Terminal 2)
2. **Open Dashboard** (http://localhost:3000/dashboard)
3. **Verify WebSocket** (green icon in dashboard)
4. **Run Backfill** (Terminal 3) to see progress tracking

## 📚 Documentation

- **Quick Reference**: `docs/quick-reference.md`
- **Integration Guide**: `docs/unified-platform-integration.md`
- **WebSocket Info**: `docs/WEBSOCKET_INFO.md`
- **Setup Checklist**: `SETUP_CHECKLIST.md`

---

**Ready!** Start with Terminal 2 to launch the API, then watch the dashboard come alive! 🎉
