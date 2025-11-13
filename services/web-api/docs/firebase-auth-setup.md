# Firebase Authentication Setup Guide

## Project Information
- **Firebase Project ID**: `utxoiq`
- **Service Account**: `firebase-adminsdk-fbsvc@utxoiq.iam.gserviceaccount.com`

## Authentication Providers Configured

### 1. Email/Password Authentication
✅ **Status**: Enabled

**Configuration:**
- Email verification: Recommended for production
- Password requirements: Minimum 6 characters (Firebase default)

**User Flow:**
1. User signs up with email and password
2. Firebase creates user account
3. User receives verification email (if enabled)
4. User can sign in with verified credentials

### 2. Google OAuth Provider
✅ **Status**: Enabled

**Configuration:**
- Provider: Google
- OAuth 2.0 Client ID: Auto-configured by Firebase

**Authorized Redirect URIs:**
```
https://utxoiq.firebaseapp.com/__/auth/handler
https://utxoiq.firebaseapp.com/__/auth/iframe
```

**For Custom Domain (Production):**
Add these redirect URIs in Google Cloud Console:
```
https://utxoiq.com/__/auth/handler
https://utxoiq.com/__/auth/iframe
https://api.utxoiq.com/__/auth/handler
```

### 3. GitHub OAuth Provider
✅ **Status**: Enabled

**Configuration:**
- Provider: GitHub
- OAuth App must be created in GitHub

**GitHub OAuth App Settings:**
- **Homepage URL**: `https://utxoiq.com`
- **Authorization callback URL**: 
  ```
  https://utxoiq.firebaseapp.com/__/auth/handler
  ```

**For Custom Domain (Production):**
Update GitHub OAuth App callback URL:
```
https://utxoiq.com/__/auth/handler
```

## Backend Configuration

### Environment Variables
Located in `services/web-api/.env`:

```bash
# Firebase Authentication
FIREBASE_PROJECT_ID=utxoiq
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

### Service Account Credentials
The Firebase Admin SDK requires a service account key file:

**Location**: `services/web-api/firebase-credentials.json`

**How to Download:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select `utxoiq` project
3. Settings → Service accounts
4. Click "Generate new private key"
5. Save as `firebase-credentials.json` in `services/web-api/`

**Security Note**: This file contains sensitive credentials and should:
- ✅ Be added to `.gitignore` (already configured)
- ✅ Be stored in Secret Manager for production
- ❌ Never be committed to version control

## Frontend Configuration

### Firebase Client SDK
Located in `frontend/.env.local`:

```bash
# Firebase Client Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key_here
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq
```

**How to Get API Key:**
1. Firebase Console → Project Settings → General
2. Under "Your apps" → Web app
3. Copy the `apiKey` value

## OAuth Redirect URL Configuration

### Development Environment
Firebase automatically handles redirects for:
- `http://localhost:3000` (frontend dev server)
- `https://utxoiq.firebaseapp.com` (Firebase hosting)

### Production Environment
When deploying to custom domain, update redirect URLs:

**Google OAuth:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. APIs & Services → Credentials
3. Select OAuth 2.0 Client ID
4. Add authorized redirect URIs:
   - `https://utxoiq.com/__/auth/handler`
   - `https://api.utxoiq.com/__/auth/handler`

**GitHub OAuth:**
1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. Select your app
3. Update "Authorization callback URL":
   - `https://utxoiq.com/__/auth/handler`

## Testing Authentication

### Test Email/Password
```bash
# Using Firebase Auth REST API
curl -X POST \
  'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "returnSecureToken": true
  }'
```

### Test Token Verification (Backend)
```bash
# Get ID token from frontend, then verify with backend
curl -X GET \
  'http://localhost:8080/api/v1/auth/profile' \
  -H 'Authorization: Bearer YOUR_ID_TOKEN'
```

## Security Best Practices

### Token Management
- ✅ ID tokens expire after 1 hour
- ✅ Refresh tokens valid for 30 days
- ✅ Backend verifies token signature with Firebase public keys
- ✅ Revoked tokens are checked on verification

### Rate Limiting
- Free tier: 100 requests/hour
- Pro tier: 1000 requests/hour
- Power tier: 10000 requests/hour

### CORS Configuration
Update `services/web-api/.env`:
```bash
CORS_ORIGINS=http://localhost:3000,https://utxoiq.com
```

## Troubleshooting

### "Invalid authentication token"
- Check token hasn't expired (1 hour lifetime)
- Verify Firebase project ID matches in frontend and backend
- Ensure service account credentials are valid

### "Authentication service temporarily unavailable"
- Check Firebase Admin SDK can fetch public keys
- Verify network connectivity to Firebase
- Check service account has proper permissions

### OAuth redirect errors
- Verify redirect URLs match exactly (including protocol)
- Check OAuth app is enabled in Firebase Console
- Ensure OAuth consent screen is configured

## Next Steps

1. ✅ Enable authentication providers (Email, Google, GitHub)
2. ⏳ Download service account credentials
3. ⏳ Configure frontend Firebase SDK
4. ⏳ Set up OAuth redirect URLs for production
5. ⏳ Test authentication flow end-to-end
