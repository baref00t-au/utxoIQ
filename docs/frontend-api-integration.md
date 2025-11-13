# Frontend API Integration Guide

## Overview

Once web-api is deployed to Cloud Run, you'll need to update the frontend environment variables to point to the production API endpoints.

## Current Setup

**Frontend**: Running locally on `http://localhost:3000`
**Backend Services**:
- ✅ utxoiq-ingestion: `https://utxoiq-ingestion-544291059247.us-central1.run.app`
- ⏳ web-api: To be deployed

## Step 1: Get web-api URL

After deploying web-api, get the service URL:

```cmd
gcloud run services describe web-api --region us-central1 --format="value(status.url)"
```

Expected output:
```
https://web-api-544291059247.us-central1.run.app
```

## Step 2: Update Frontend Environment Variables

Edit `frontend/.env.local`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=https://web-api-544291059247.us-central1.run.app
NEXT_PUBLIC_API_VERSION=v1

# Firebase Configuration (already configured)
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyDGBx...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq-dev.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq-dev
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=utxoiq-dev.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=544291059247
NEXT_PUBLIC_FIREBASE_APP_ID=1:544291059247:web:...

# Stripe Configuration (if needed)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# Feature Flags (optional)
NEXT_PUBLIC_ENABLE_CHAT=false
NEXT_PUBLIC_ENABLE_ALERTS=true
NEXT_PUBLIC_ENABLE_INSIGHTS=true
```

## Step 3: Restart Development Server

```cmd
REM Stop current dev server (Ctrl+C)

REM Start fresh
cd frontend
npm run dev
```

## Step 4: Test API Connection

### Test 1: Health Check

Open browser console and run:
```javascript
fetch('https://web-api-544291059247.us-central1.run.app/health')
  .then(r => r.json())
  .then(console.log)
```

Expected response:
```json
{
  "status": "healthy",
  "service": "web-api",
  "timestamp": "2025-11-12T09:30:00.000000"
}
```

### Test 2: Get Insights (if endpoint exists)

```javascript
fetch('https://web-api-544291059247.us-central1.run.app/api/v1/insights')
  .then(r => r.json())
  .then(console.log)
```

### Test 3: Authentication Flow

1. Try to sign in via frontend
2. Check browser console for API calls
3. Verify Firebase Auth tokens are being sent
4. Check web-api logs for authentication requests

## Step 5: Verify CORS Configuration

If you get CORS errors, web-api needs to allow your frontend origin:

```python
# In web-api/src/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://utxoiq.com",     # Production (when deployed)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Common API Endpoints

Based on your architecture, web-api should expose:

### Public Endpoints (No Auth Required)
- `GET /health` - Health check
- `GET /api/v1/insights` - List public insights
- `GET /api/v1/insights/{id}` - Get specific insight
- `GET /api/v1/brief` - Get daily brief

### Protected Endpoints (Auth Required)
- `GET /api/v1/user/profile` - Get user profile
- `POST /api/v1/alerts` - Create alert
- `GET /api/v1/alerts` - List user alerts
- `PUT /api/v1/alerts/{id}` - Update alert
- `DELETE /api/v1/alerts/{id}` - Delete alert
- `GET /api/v1/subscription` - Get subscription status

## Testing Checklist

After updating environment variables and restarting:

- [ ] Frontend loads without errors
- [ ] API health check succeeds
- [ ] Can view public insights (if available)
- [ ] Sign in flow works
- [ ] Authenticated API calls work
- [ ] No CORS errors in console
- [ ] Firebase Auth integration works
- [ ] Error messages display correctly

## Troubleshooting

### Issue: API calls fail with 404

**Cause**: web-api not deployed or wrong URL
**Solution**: 
```cmd
gcloud run services list --region us-central1 | findstr web-api
```

### Issue: CORS errors

**Cause**: web-api doesn't allow frontend origin
**Solution**: Update CORS middleware in web-api and redeploy

### Issue: Authentication fails

**Cause**: Firebase config mismatch or token not sent
**Solution**: 
1. Check Firebase config in frontend
2. Verify token is in Authorization header
3. Check web-api logs for auth errors

### Issue: 500 Internal Server Error

**Cause**: web-api error
**Solution**: Check web-api logs:
```cmd
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=web-api"
```

## Environment Variables Reference

### Required for Frontend
```env
NEXT_PUBLIC_API_URL=<web-api-url>
NEXT_PUBLIC_FIREBASE_API_KEY=<firebase-key>
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<firebase-domain>
NEXT_PUBLIC_FIREBASE_PROJECT_ID=<firebase-project>
```

### Optional for Frontend
```env
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=<stripe-key>
NEXT_PUBLIC_ENABLE_CHAT=true
NEXT_PUBLIC_ENABLE_ALERTS=true
NEXT_PUBLIC_ANALYTICS_ID=<ga-id>
```

## Quick Test Script

Create `frontend/test-api.js`:

```javascript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function testAPI() {
  console.log('Testing API:', API_URL);
  
  // Test 1: Health check
  try {
    const health = await fetch(`${API_URL}/health`);
    console.log('✅ Health:', await health.json());
  } catch (e) {
    console.error('❌ Health check failed:', e);
  }
  
  // Test 2: Public endpoint
  try {
    const insights = await fetch(`${API_URL}/api/v1/insights`);
    console.log('✅ Insights:', await insights.json());
  } catch (e) {
    console.error('❌ Insights failed:', e);
  }
}

testAPI();
```

Run with:
```cmd
node frontend/test-api.js
```

## Next Steps

1. ✅ Deploy web-api to Cloud Run
2. ⏳ Get web-api URL
3. ⏳ Update `frontend/.env.local`
4. ⏳ Restart frontend dev server
5. ⏳ Test API integration
6. ⏳ Fix any CORS or auth issues
7. ⏳ Deploy frontend to production

## Production Deployment

When ready to deploy frontend:

```cmd
REM Build frontend
cd frontend
npm run build

REM Deploy to Cloud Run (or Vercel/Netlify)
gcloud run deploy utxoiq-frontend --source . --region us-central1
```

Update production environment variables in Cloud Run console.
