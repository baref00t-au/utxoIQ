# WebSocket Connection Info

## Expected Behavior

### When API is NOT Running

You'll see this console error:
```
WebSocket error: {}
WebSocket disconnected
Attempting to reconnect...
```

**This is normal!** The WebSocket is trying to connect to the backend API at `ws://localhost:8000/ws/monitoring`.

### What Happens

1. Frontend tries to connect to WebSocket
2. Connection fails (API not running)
3. WebSocket shows "disconnected" indicator (gray WiFi icon)
4. Automatic reconnection attempts every 5 seconds
5. Dashboard still works, just without live updates

### When API IS Running

Once you start the backend API:
```bash
# Start the API
docker-compose up -d
# OR
cd services/web-api && python -m uvicorn src.main:app --reload
```

The WebSocket will:
1. ✅ Automatically connect
2. ✅ Show "connected" indicator (green WiFi icon)
3. ✅ Start receiving real-time updates
4. ✅ Display live system status
5. ✅ Show backfill progress
6. ✅ Send toast notifications for new insights

## Visual Indicators

### Dashboard Header
Look for the WiFi icon next to "System Status":
- 🟢 **Green WiFi icon** = Connected (live updates)
- ⚪ **Gray WiFi icon** = Disconnected (no API)

### Console Messages

**Disconnected:**
```
WebSocket error: {}
WebSocket disconnected
Attempting to reconnect...
```

**Connected:**
```
Monitoring WebSocket connected
Subscribed to monitoring updates
```

## How to Start the API

### Option 1: Docker Compose (Recommended)
```bash
# From project root
docker-compose up -d

# Check if running
curl http://localhost:8000/health
```

### Option 2: Manual Start
```bash
# Terminal 1: Web API
cd services/web-api
python -m uvicorn src.main:app --reload

# Terminal 2: Frontend (if not already running)
cd frontend
npm run dev
```

### Option 3: Just Frontend (No Live Updates)
```bash
# Frontend only - dashboard works but no live data
cd frontend
npm run dev
```

## Testing WebSocket Connection

### 1. Check API is Running
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

### 2. Test WebSocket Endpoint
```bash
# Windows PowerShell
Test-NetConnection localhost -Port 8000

# Or use curl
curl -i http://localhost:8000/ws/monitoring
```

### 3. Check Browser Console
Open DevTools (F12) → Console tab:
- Look for "Monitoring WebSocket connected" message
- Check Network tab → WS filter for WebSocket connection

### 4. Check Dashboard Indicator
- Open http://localhost:3000/dashboard
- Look at "System Status" card header
- Green WiFi icon = Connected ✅
- Gray WiFi icon = Disconnected (API not running)

## Troubleshooting

### WebSocket Won't Connect

**1. Check API is running**
```bash
curl http://localhost:8000/health
```

**2. Check correct URL**
Frontend expects API at:
- HTTP: `http://localhost:8000`
- WebSocket: `ws://localhost:8000`

**3. Check environment variables**
In `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

**4. Check CORS settings**
In `services/web-api/src/main.py`, CORS should allow:
```python
allow_origins=["*"]  # or ["http://localhost:3000"]
```

**5. Check firewall**
Ensure ports 3000 and 8000 are not blocked

### Connection Keeps Dropping

**1. Check API logs**
```bash
docker-compose logs -f web-api
```

**2. Increase timeout**
WebSocket has 30-second ping interval. If connection drops:
- Check network stability
- Check API isn't restarting
- Check for rate limiting

**3. Check browser console**
Look for specific error messages in DevTools

## Features Without API

The dashboard works without the API, but with limited functionality:

### ✅ Works Without API
- Dashboard layout and navigation
- UI components and interactions
- Tabs switching
- Feedback dialogs (UI only)
- Static content

### ❌ Requires API
- Live system status
- Service health checks
- Backfill progress
- Processing metrics
- Real-time updates
- WebSocket connection
- Actual feedback submission
- Insight data

## Development Workflow

### Frontend-Only Development
```bash
cd frontend
npm run dev
```
- Dashboard loads
- UI components work
- No live data
- Good for UI/UX work

### Full Stack Development
```bash
# Terminal 1: Backend
docker-compose up -d

# Terminal 2: Frontend
cd frontend
npm run dev
```
- Dashboard loads
- Live data available
- WebSocket connected
- Full functionality

## Production Deployment

In production, ensure:
1. API URL is set correctly in environment variables
2. WebSocket URL uses `wss://` (secure WebSocket)
3. CORS is configured for production domain
4. Health checks are enabled
5. Auto-reconnection is working

Example production config:
```bash
NEXT_PUBLIC_API_URL=https://api.utxoiq.com
NEXT_PUBLIC_WS_URL=wss://api.utxoiq.com
```

## Summary

**The WebSocket error is expected when the API isn't running.**

To get live updates:
1. Start the backend API
2. Refresh the dashboard
3. Look for green WiFi icon
4. Enjoy real-time updates!

The dashboard is fully functional without the API - it just won't show live data until you start the backend services.

---

**Quick Start:**
```bash
# Start everything
docker-compose up -d

# Open dashboard
open http://localhost:3000/dashboard

# Check connection indicator (should be green)
```
