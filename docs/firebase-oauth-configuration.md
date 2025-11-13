# Firebase OAuth Provider Configuration

**Task**: 1.2 Configure authentication providers  
**Status**: Configuration guide for Firebase Console setup  
**Requirements**: Requirement 1 - Support email/password, Google OAuth, and GitHub OAuth authentication

## Firebase Project Information

- **Project ID**: `utxoiq`
- **Project Number**: `736762852981`
- **Web App ID**: `1:736762852981:web:5ef6b4268948a89ea3aa3c`
- **Auth Domain**: `utxoiq.firebaseapp.com`
- **API Key**: `AIzaSyC-uPcyqfnL-n8tUKrndsoiGq1GPa6X7GA`

## Overview

This guide walks through configuring all authentication providers required for the utxoIQ platform:
1. **Email/Password** - Basic authentication with email verification
2. **Google OAuth** - Social sign-in with Google accounts
3. **GitHub OAuth** - Social sign-in with GitHub accounts
4. **OAuth Redirect URLs** - Proper configuration for all environments

## Step 1: Add Authorized Domains in Firebase Console

You need to authorize ALL domains that will use Firebase Auth (dev, staging, prod).

### Instructions:

1. Go to [Firebase Console](https://console.firebase.google.com/project/utxoiq/authentication/settings)
2. Click on **Authorized domains** tab
3. Click **Add domain** for each of these:

```
✅ localhost (already authorized)
✅ utxoiq.firebaseapp.com (already authorized)

Add these:
□ dev.utxoiq.com
□ dev-api.utxoiq.com
□ staging.utxoiq.com
□ staging-api.utxoiq.com
□ utxoiq.com
□ api.utxoiq.com
□ www.utxoiq.com
```

**Why all these domains?**
- Frontend domains (dev.utxoiq.com, staging.utxoiq.com, utxoiq.com) - where users sign in
- API domains (dev-api.utxoiq.com, staging-api.utxoiq.com, api.utxoiq.com) - for CORS
- www.utxoiq.com - for production www subdomain

## Step 2: Configure Google OAuth Provider

### 2.1 Enable Google Sign-In in Firebase

1. Go to [Firebase Console - Authentication](https://console.firebase.google.com/project/utxoiq/authentication/providers)
2. Click on **Google** provider
3. Click **Enable**
4. Set **Project support email**: `vosika@gmail.com` (or your email)
5. Click **Save**

### 2.2 Configure OAuth Consent Screen

1. Go to [Google Cloud Console - OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent?project=utxoiq)
2. Select **External** user type (or Internal if workspace)
3. Fill in:
   - **App name**: `utxoIQ`
   - **User support email**: `vosika@gmail.com`
   - **App logo**: (optional, upload logo)
   - **Application home page**: `https://utxoiq.com`
   - **Application privacy policy**: `https://utxoiq.com/privacy`
   - **Application terms of service**: `https://utxoiq.com/terms`
   - **Authorized domains**: `utxoiq.com`
   - **Developer contact**: `vosika@gmail.com`
4. Click **Save and Continue**
5. **Scopes**: Add these scopes:
   - `email`
   - `profile`
   - `openid`
6. Click **Save and Continue**
7. **Test users** (if in testing mode): Add your email
8. Click **Save and Continue**

### 2.3 Configure OAuth Redirect URIs

1. Go to [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials?project=utxoiq)
2. Find the OAuth 2.0 Client ID created by Firebase (starts with "Web client (auto created by Google Service)")
3. Click to edit
4. Under **Authorized JavaScript origins**, add:
   ```
   http://localhost:3000
   https://dev.utxoiq.com
   https://staging.utxoiq.com
   https://utxoiq.com
   https://www.utxoiq.com
   ```

5. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:3000/__/auth/handler
   https://utxoiq.firebaseapp.com/__/auth/handler
   https://dev.utxoiq.com/__/auth/handler
   https://staging.utxoiq.com/__/auth/handler
   https://utxoiq.com/__/auth/handler
   https://www.utxoiq.com/__/auth/handler
   ```

6. Click **Save**

## Step 3: Configure GitHub OAuth Provider

### Option A: Single GitHub OAuth App (Recommended for Simplicity)

Use Firebase's default callback URL which works for all environments.

#### 3.1 Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in:
   - **Application name**: `utxoIQ`
   - **Homepage URL**: `https://utxoiq.com`
   - **Application description**: `Bitcoin blockchain intelligence platform`
   - **Authorization callback URL**: `https://utxoiq.firebaseapp.com/__/auth/handler`
4. Click **Register application**
5. Copy the **Client ID**
6. Click **Generate a new client secret**
7. Copy the **Client Secret** (you won't see it again!)

#### 3.2 Configure in Firebase

1. Go to [Firebase Console - Authentication](https://console.firebase.google.com/project/utxoiq/authentication/providers)
2. Click on **GitHub** provider
3. Click **Enable**
4. Paste **Client ID** from GitHub
5. Paste **Client Secret** from GitHub
6. Copy the **Authorization callback URL** shown (should be `https://utxoiq.firebaseapp.com/__/auth/handler`)
7. Click **Save**

### Option B: Multiple GitHub OAuth Apps (Better for Production)

Create separate OAuth apps for each environment.

#### Development OAuth App

1. Create new OAuth App:
   - **Name**: `utxoIQ Development`
   - **Homepage**: `https://dev.utxoiq.com`
   - **Callback**: `https://dev.utxoiq.com/__/auth/handler`
2. Get Client ID and Secret
3. Configure in Firebase (you can only have one GitHub provider, so switch as needed)

#### Staging OAuth App

1. Create new OAuth App:
   - **Name**: `utxoIQ Staging`
   - **Homepage**: `https://staging.utxoiq.com`
   - **Callback**: `https://staging.utxoiq.com/__/auth/handler`
2. Get Client ID and Secret

#### Production OAuth App

1. Create new OAuth App:
   - **Name**: `utxoIQ`
   - **Homepage**: `https://utxoiq.com`
   - **Callback**: `https://utxoiq.com/__/auth/handler`
2. Get Client ID and Secret
3. Configure in Firebase for production

**Note**: With this approach, you'll need to manually switch the GitHub provider credentials in Firebase Console when deploying to different environments. Option A is simpler.

## Step 4: Configure Email/Password Provider

1. Go to [Firebase Console - Authentication](https://console.firebase.google.com/project/utxoiq/authentication/providers)
2. Click on **Email/Password** provider
3. Click **Enable**
4. **Email/Password**: Toggle ON
5. **Email link (passwordless sign-in)**: Toggle OFF (or ON if you want passwordless)
6. Click **Save**

### Email Verification (Optional but Recommended)

1. Go to **Templates** tab in Authentication
2. Click on **Email address verification**
3. Customize the email template
4. Update **Action URL** to your domain: `https://utxoiq.com`

## Step 5: Update Environment Variables

### Backend Configuration

Update `services/web-api/.env`:

```bash
# Firebase Auth (same for all environments)
FIREBASE_PROJECT_ID=utxoiq
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

### Frontend Configuration

#### Development (`frontend/.env.development`):

```bash
# Firebase Client SDK
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyC-uPcyqfnL-n8tUKrndsoiGq1GPa6X7GA
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq
NEXT_PUBLIC_FIREBASE_APP_ID=1:736762852981:web:5ef6b4268948a89ea3aa3c
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=736762852981
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=utxoiq.firebasestorage.app

# API
NEXT_PUBLIC_API_URL=https://dev-api.utxoiq.com
```

#### Staging (`frontend/.env.staging`):

```bash
# Firebase Client SDK (same as dev)
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyC-uPcyqfnL-n8tUKrndsoiGq1GPa6X7GA
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq
NEXT_PUBLIC_FIREBASE_APP_ID=1:736762852981:web:5ef6b4268948a89ea3aa3c
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=736762852981
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=utxoiq.firebasestorage.app

# API
NEXT_PUBLIC_API_URL=https://staging-api.utxoiq.com
```

#### Production (`frontend/.env.production`):

```bash
# Firebase Client SDK (same as dev/staging)
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyC-uPcyqfnL-n8tUKrndsoiGq1GPa6X7GA
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq
NEXT_PUBLIC_FIREBASE_APP_ID=1:736762852981:web:5ef6b4268948a89ea3aa3c
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=736762852981
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=utxoiq.firebasestorage.app

# API
NEXT_PUBLIC_API_URL=https://api.utxoiq.com
```

## Step 6: Test Authentication

### Test Email/Password

```bash
# Sign up
curl -X POST \
  'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyC-uPcyqfnL-n8tUKrndsoiGq1GPa6X7GA' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "returnSecureToken": true
  }'

# Sign in
curl -X POST \
  'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyC-uPcyqfnL-n8tUKrndsoiGq1GPa6X7GA' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "returnSecureToken": true
  }'
```

### Test Google OAuth

1. Open `http://localhost:3000` (or your frontend URL)
2. Click "Sign in with Google"
3. Select Google account
4. Verify redirect works
5. Check Firebase Console → Authentication → Users to see new user

### Test GitHub OAuth

1. Open `http://localhost:3000`
2. Click "Sign in with GitHub"
3. Authorize the app
4. Verify redirect works
5. Check Firebase Console → Authentication → Users

### Test Backend Token Verification

```bash
# Get ID token from frontend (check browser console or network tab)
TOKEN="eyJhbGc..."

# Test backend API
curl -X GET http://localhost:8080/api/v1/auth/profile \
  -H "Authorization: Bearer $TOKEN"
```

## Verification Checklist

- [ ] All domains added to Firebase Authorized domains
- [ ] Google OAuth consent screen configured
- [ ] Google OAuth redirect URIs added for all environments
- [ ] GitHub OAuth app created and configured
- [ ] Email/Password provider enabled
- [ ] Frontend environment variables updated
- [ ] Backend environment variables updated
- [ ] Tested email/password sign up
- [ ] Tested Google OAuth sign in
- [ ] Tested GitHub OAuth sign in
- [ ] Tested backend token verification

## Troubleshooting

### "Redirect URI mismatch" (Google)

**Error**: The redirect URI in the request does not match

**Solution**:
1. Check the exact URL in browser console
2. Verify it's in Google Cloud Console → Credentials → Authorized redirect URIs
3. Make sure protocol (https://) and path (/__/auth/handler) match exactly

### "Domain not authorized" (Firebase)

**Error**: This domain is not authorized for OAuth operations

**Solution**:
1. Firebase Console → Authentication → Settings → Authorized domains
2. Add the domain
3. Wait 5-10 minutes for propagation

### "Invalid OAuth callback URL" (GitHub)

**Error**: The redirect_uri MUST match the registered callback URL

**Solution**:
1. GitHub → Settings → Developer settings → OAuth Apps
2. Verify callback URL matches exactly
3. Use `https://utxoiq.firebaseapp.com/__/auth/handler` for all environments (Option A)

### CORS Errors

**Error**: Access to fetch blocked by CORS policy

**Solution**:
1. Update backend `CORS_ORIGINS` in `.env`
2. Include all frontend domains
3. Redeploy backend service

## Next Steps

1. ✅ Configure all OAuth providers
2. ⏳ Set up custom domains (see `docs/firebase-custom-domains-setup.md`)
3. ⏳ Implement frontend authentication UI
4. ⏳ Test authentication flow end-to-end
5. ⏳ Set up user profile management
6. ⏳ Implement role-based access control

---

**Quick Links:**
- [Firebase Console](https://console.firebase.google.com/project/utxoiq)
- [Google Cloud Console](https://console.cloud.google.com/?project=utxoiq)
- [GitHub OAuth Apps](https://github.com/settings/developers)
