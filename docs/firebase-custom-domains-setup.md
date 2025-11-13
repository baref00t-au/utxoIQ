# Firebase Custom Domains Setup for Production

## Project Information
- **Firebase Project ID**: `utxoiq`
- **GCP Project ID**: `utxoiq`
- **Project Number**: `736762852981`

## Custom Domains to Configure

### Primary Domains
- **Frontend**: `utxoiq.com` (Next.js app)
- **API**: `api.utxoiq.com` (FastAPI backend)
- **Firebase Hosting**: `app.utxoiq.com` (optional, if using Firebase Hosting)

## Step 1: Add Authorized Domains in Firebase Console

Firebase Auth needs to know which domains are allowed to use authentication.

### Instructions:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: **utxoiq**
3. Navigate to: **Authentication** → **Settings** → **Authorized domains**
4. Click **Add domain** and add each of these:

```
utxoiq.com
api.utxoiq.com
app.utxoiq.com
www.utxoiq.com
```

**Note**: `localhost` and `*.firebaseapp.com` are already authorized by default.

## Step 2: Update OAuth Provider Redirect URLs

### Google OAuth Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project: **utxoiq** (Project ID: `utxoiq`)
3. Navigate to: **APIs & Services** → **Credentials**
4. Find your OAuth 2.0 Client ID (created by Firebase)
5. Click to edit
6. Under **Authorized redirect URIs**, add:

```
https://utxoiq.com/__/auth/handler
https://api.utxoiq.com/__/auth/handler
https://app.utxoiq.com/__/auth/handler
https://www.utxoiq.com/__/auth/handler
```

**Keep existing URIs:**
```
https://utxoiq.firebaseapp.com/__/auth/handler
http://localhost (for development)
```

### GitHub OAuth Configuration

1. Go to [GitHub](https://github.com/) → **Settings** → **Developer settings** → **OAuth Apps**
2. Select your Firebase OAuth app (or create new one)
3. Update **Authorization callback URL**:

**Primary callback:**
```
https://utxoiq.com/__/auth/handler
```

**Note**: GitHub OAuth apps only support ONE callback URL. For multiple domains, you'll need to create separate OAuth apps for each environment:

- **Production**: `https://utxoiq.com/__/auth/handler`
- **Staging**: `https://staging.utxoiq.com/__/auth/handler` (if needed)
- **Development**: `https://utxoiq.firebaseapp.com/__/auth/handler`

Then configure the appropriate Client ID/Secret in Firebase Console for each environment.

## Step 3: Configure DNS Records

### For Frontend (utxoiq.com)

If deploying to **Cloud Run**:

```bash
# Get Cloud Run service URL
gcloud run services describe utxoiq-frontend \
  --region=us-central1 \
  --format='value(status.url)'

# Add DNS records in your domain registrar:
# Type: CNAME
# Name: @ (or utxoiq.com)
# Value: ghs.googlehosted.com
```

If using **Firebase Hosting**:

```bash
# Connect custom domain via Firebase Console
# Authentication → Hosting → Add custom domain
# Follow the wizard to add DNS records
```

### For API (api.utxoiq.com)

If deploying to **Cloud Run**:

```bash
# Map custom domain to Cloud Run service
gcloud run domain-mappings create \
  --service=utxoiq-api \
  --domain=api.utxoiq.com \
  --region=us-central1

# Add DNS records shown in the output
```

### For www subdomain

```
Type: CNAME
Name: www
Value: utxoiq.com
```

## Step 4: Update Environment Variables

### Backend (.env)

Update `services/web-api/.env`:

```bash
# CORS - Add production domains
CORS_ORIGINS=https://utxoiq.com,https://www.utxoiq.com,https://app.utxoiq.com,http://localhost:3000

# Firebase
FIREBASE_PROJECT_ID=utxoiq
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

### Frontend (.env.production)

Create `frontend/.env.production`:

```bash
# Firebase Client Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key_here
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq

# API Configuration
NEXT_PUBLIC_API_URL=https://api.utxoiq.com

# Environment
NODE_ENV=production
```

## Step 5: SSL/TLS Certificates

### Cloud Run (Automatic)
Cloud Run automatically provisions and manages SSL certificates for custom domains. No action needed!

### Firebase Hosting (Automatic)
Firebase Hosting automatically provisions SSL certificates via Let's Encrypt. No action needed!

### Verification
```bash
# Check SSL certificate
curl -vI https://utxoiq.com 2>&1 | grep -i "SSL certificate"
curl -vI https://api.utxoiq.com 2>&1 | grep -i "SSL certificate"
```

## Step 6: Deploy with Custom Domain Configuration

### Deploy Backend API

```bash
cd services/web-api

# Deploy to Cloud Run
gcloud run deploy utxoiq-api \
  --source . \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="CORS_ORIGINS=https://utxoiq.com,https://www.utxoiq.com"

# Map custom domain
gcloud run domain-mappings create \
  --service=utxoiq-api \
  --domain=api.utxoiq.com \
  --region=us-central1
```

### Deploy Frontend

```bash
cd frontend

# Build for production
npm run build

# Deploy to Cloud Run
gcloud run deploy utxoiq-frontend \
  --source . \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated

# Map custom domain
gcloud run domain-mappings create \
  --service=utxoiq-frontend \
  --domain=utxoiq.com \
  --region=us-central1
```

## Step 7: Test Authentication Flow

### Test Email/Password Auth

```bash
# 1. Open browser to https://utxoiq.com
# 2. Click "Sign Up" or "Sign In"
# 3. Enter email and password
# 4. Verify redirect works correctly
```

### Test Google OAuth

```bash
# 1. Click "Sign in with Google"
# 2. Select Google account
# 3. Verify redirect to https://utxoiq.com/__/auth/handler
# 4. Verify successful authentication
```

### Test GitHub OAuth

```bash
# 1. Click "Sign in with GitHub"
# 2. Authorize the app
# 3. Verify redirect to https://utxoiq.com/__/auth/handler
# 4. Verify successful authentication
```

### Test API Authentication

```bash
# Get ID token from frontend, then test API
curl -X GET https://api.utxoiq.com/api/v1/auth/profile \
  -H "Authorization: Bearer YOUR_ID_TOKEN"
```

## Step 8: Update OAuth Consent Screen (Google)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: **APIs & Services** → **OAuth consent screen**
3. Update:
   - **Application home page**: `https://utxoiq.com`
   - **Application privacy policy**: `https://utxoiq.com/privacy`
   - **Application terms of service**: `https://utxoiq.com/terms`
   - **Authorized domains**: Add `utxoiq.com`

## Troubleshooting

### "Redirect URI mismatch" Error

**Cause**: OAuth redirect URL doesn't match configured URLs

**Solution**:
1. Check browser console for actual redirect URL
2. Verify it matches exactly in Google Cloud Console
3. Include protocol (https://) and path (/__/auth/handler)

### "Domain not authorized" Error

**Cause**: Domain not added to Firebase authorized domains

**Solution**:
1. Firebase Console → Authentication → Settings → Authorized domains
2. Add the domain
3. Wait 5-10 minutes for propagation

### SSL Certificate Issues

**Cause**: DNS not properly configured or certificate not provisioned

**Solution**:
```bash
# Check domain mapping status
gcloud run domain-mappings describe api.utxoiq.com \
  --region=us-central1

# Verify DNS records
nslookup api.utxoiq.com
```

### CORS Errors

**Cause**: Frontend domain not in CORS_ORIGINS

**Solution**:
1. Update `services/web-api/.env`
2. Add frontend domain to CORS_ORIGINS
3. Redeploy backend

## Security Checklist

- [ ] All domains use HTTPS (no HTTP)
- [ ] OAuth redirect URLs use HTTPS
- [ ] CORS configured with specific domains (not wildcard *)
- [ ] Firebase authorized domains list is minimal
- [ ] OAuth consent screen is configured
- [ ] Privacy policy and terms of service are published
- [ ] Rate limiting is enabled
- [ ] API keys are stored in Secret Manager

## Quick Reference Commands

```bash
# List domain mappings
gcloud run domain-mappings list --region=us-central1

# Describe specific mapping
gcloud run domain-mappings describe api.utxoiq.com --region=us-central1

# Delete domain mapping
gcloud run domain-mappings delete api.utxoiq.com --region=us-central1

# Update CORS in running service
gcloud run services update utxoiq-api \
  --update-env-vars="CORS_ORIGINS=https://utxoiq.com" \
  --region=us-central1
```

## Next Steps

1. ✅ Add authorized domains in Firebase Console
2. ✅ Update Google OAuth redirect URLs
3. ✅ Update GitHub OAuth callback URL
4. ✅ Configure DNS records
5. ✅ Deploy services with custom domains
6. ✅ Test authentication flow end-to-end
7. ✅ Update OAuth consent screen
8. ✅ Monitor logs for any issues

---

**Need Help?**
- [Firebase Custom Domain Docs](https://firebase.google.com/docs/hosting/custom-domain)
- [Cloud Run Custom Domains](https://cloud.google.com/run/docs/mapping-custom-domains)
- [OAuth 2.0 Redirect URIs](https://developers.google.com/identity/protocols/oauth2/web-server#uri-validation)
