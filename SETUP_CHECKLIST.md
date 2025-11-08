# Setup Checklist

## ✅ Integration Complete

All platform components have been integrated into a unified dashboard!

## 🔧 Setup Steps

### 1. Install Frontend Dependencies
```bash
cd frontend
npm install
```

This will install:
- All existing dependencies
- New: `sonner` for toast notifications
- All UI component dependencies (@radix-ui/*)

### 2. Verify Build
```bash
cd frontend
npm run build
```

Should complete without errors.

### 3. Start Services

**Option A: Docker Compose (Recommended)**
```bash
# From project root
docker-compose up -d
```

**Option B: Manual Start**
```bash
# Terminal 1: Web API
cd services/web-api
python -m uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 4. Access Dashboard
```bash
open http://localhost:3000/dashboard
```

### 5. Test Integration (Optional)
```bash
python scripts/test-integration.py
```

### 6. Run Backfill (Optional)
```bash
python scripts/backfill-with-progress.py \
  --start 800000 \
  --end 850000 \
  --api-url http://localhost:8000
```

## 📋 Pre-flight Checklist

Before starting, ensure you have:

- [ ] Node.js 18+ installed
- [ ] Python 3.9+ installed
- [ ] Docker and Docker Compose installed (for full stack)
- [ ] Bitcoin Core RPC access (for backfill)
- [ ] Environment variables configured

## 🔍 Verification Steps

### 1. Check API Health
```bash
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", ...}`

### 2. Check Monitoring Endpoint
```bash
curl http://localhost:8000/api/v1/monitoring/status | jq
```

Expected: JSON with system status

### 3. Check Frontend
```bash
curl http://localhost:3000
```

Expected: HTML response

### 4. Check WebSocket
```javascript
// In browser console at http://localhost:3000/dashboard
const ws = new WebSocket('ws://localhost:8000/ws/monitoring');
ws.onopen = () => console.log('Connected!');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

Expected: Connection established, messages received

## 🐛 Troubleshooting

### Build Errors

**Error: Module not found '@/components/ui/card'**
- Solution: Run `npm install` in frontend directory
- Files created: card.tsx, dialog.tsx

**Error: Cannot find module 'sonner'**
- Solution: Run `npm install` in frontend directory
- Added to package.json

### Runtime Errors

**Error: API not responding**
- Check API is running: `curl http://localhost:8000/health`
- Check logs: `docker-compose logs web-api`
- Verify port 8000 is not in use

**Error: WebSocket connection failed**
- Check API WebSocket endpoint: `curl -i http://localhost:8000/ws/monitoring`
- Verify CORS settings in web-api config
- Check browser console for errors

**Error: Database connection failed**
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify credentials

## 📦 What Was Built

### Backend (7 files)
- ✅ Monitoring API endpoints
- ✅ Feedback API endpoints
- ✅ WebSocket handler
- ✅ Connection manager

### Frontend (8 files)
- ✅ Dashboard page
- ✅ System status component
- ✅ Feedback component
- ✅ WebSocket hook
- ✅ Card UI component
- ✅ Dialog UI component
- ✅ Textarea UI component
- ✅ Toast utility

### Scripts (2 files)
- ✅ Enhanced backfill script
- ✅ Integration test suite

### Documentation (10 files)
- ✅ Comprehensive integration guide
- ✅ Quick summary
- ✅ Architecture diagrams
- ✅ Quick reference
- ✅ Roadmap
- ✅ Integration README
- ✅ Project status
- ✅ Build fix guide
- ✅ This checklist
- ✅ Integration complete summary

## 🎯 Success Criteria

- [ ] Frontend builds without errors
- [ ] All services start successfully
- [ ] Dashboard loads at /dashboard
- [ ] System status shows service health
- [ ] WebSocket connection indicator shows "connected"
- [ ] Backfill progress updates in real-time
- [ ] Feedback dialogs open and close
- [ ] No console errors in browser

## 🚀 Next Steps

After setup is complete:

1. **Explore Dashboard**
   - View system status
   - Check service health
   - Monitor metrics

2. **Test Feedback**
   - Rate an insight
   - Add a comment
   - Flag content

3. **Run Backfill**
   - Start backfill script
   - Watch progress in dashboard
   - Monitor completion

4. **Review Documentation**
   - Read integration guide
   - Check API reference
   - Review roadmap

## 📞 Need Help?

- **Documentation**: See `docs/` directory
- **Build Issues**: See `docs/BUILD_FIX.md`
- **Integration Guide**: See `docs/unified-platform-integration.md`
- **Quick Reference**: See `docs/quick-reference.md`
- **GitHub Issues**: https://github.com/utxoiq/utxoiq/issues
- **Email**: support@utxoiq.com

## ✨ You're Ready!

Once all checklist items are complete, you have a fully integrated utxoIQ platform with:
- Real-time monitoring
- User feedback system
- Backfill progress tracking
- Live WebSocket updates
- Comprehensive metrics

**Start exploring at http://localhost:3000/dashboard** 🎉
