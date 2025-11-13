# Task 1.2: Configure Authentication Providers - Checklist

**Status**: In Progress  
**Requirements**: Requirement 1 - Multi-provider authentication support

## Quick Start

This task requires manual configuration in the Firebase Console. Follow the steps below and check them off as you complete them.

## Configuration Steps

### Step 1: Enable Email/Password Authentication ✅

1. Go to [Firebase Console - Authentication Providers](https://console.firebase.google.com/project/utxoiq/authentication/providers)
2. Click on **Email/Password** provider
3. Click **Enable** toggle
4. Ensure **Email/Password** is ON
5. Click **Save**

**Verification**: You should see "Email/Password" listed as "Enabled" in the providers list.

---

### Step 2: Enable Google OAuth Provider ✅

1. Go to [Firebase Console - Authentication Providers](https://console.firebase.google.com/project/utxoiq/authentication/providers)
2. Click on **Google** provider
3. Click **Enable** toggle
4. Set **Project support email**: `vosika@gmail.com` (or your email)
5. Click **Save**

**Verification**: You should see "Google" listed as "Enabled" in the providers list.

---

### Step 3: Enable GitHub OAuth Provider ✅

#### 3.1 Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in the form:
   - **Application name**: `utxoIQ`
   - **Homepage URL**: `https://utxoiq.com`
   - **Application description**: `Bitcoin blockchain intelligence platform`
   - **Authorization callback URL**: `https://utxoiq.firebaseapp.com/__/auth/handler`
4. Click **Register application**
5. **Copy the Client ID** (you'll need this)
6. Click **Generate a new client secret**
7. **Copy the Client Secret** (you won't see it again!)

#### 3.2 Configure GitHub Provider in Firebase

1. Go to [Firebase Console - Authentication Providers](https://console.firebase.google.com/project/utxoiq/authentication/providers)
2. Click on **GitHub** provider
3. Click **Enable** toggle
4. Paste the **Client ID** from GitHub
5. Paste the **Client Secret** from GitHub
6. Verify the **Authorization callback URL** matches: `https://utxoiq.firebaseapp.com/__/auth/handler`
7. Click **Save**

**Verification**: You should see "GitHub" listed as "Enabled" in the providers list.

---

### Step 4: Configure OAuth Redirect URLs ✅

#### 4.1 Add Authorized Domains in Firebase

1. Go to [Firebase Console - Authentication Settings](https://console.firebase.google.com/project/utxoiq/authentication/settings)
2. Click on **Authorized domains** tab
3. Verify these domains are listed (add if missing):
   - ✅ `localhost` (for local development)
   - ✅ `utxoiq.firebaseapp.com` (Firebase default)
   - Add: `dev.utxoiq.com` (development environment)
   - Add: `staging.utxoiq.com` (staging environment)
   - Add: `utxoiq.com` (production)
   - Add: `www.utxoiq.com` (production www subdomain)

#### 4.2 Configure Google OAuth Redirect URIs

1. Go to [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials?project=utxoiq)
2. Find the OAuth 2.0 Client ID created by Firebase (name starts with "Web client (auto created by Google Service)")
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

**Verification**: All redirect URIs should be listed in the Google Cloud Console.

---

## Final Verification

### Check Firebase Console

1. Go to [Firebase Console - Authentication Providers](https://console.firebase.google.com/project/utxoiq/authentication/providers)
2. Verify all three providers show as "Enabled":
   - ✅ Email/Password
   - ✅ Google
   - ✅ GitHub

### Test Authentication (Optional - can be done in later tasks)

You can test the providers are working by:

1. **Email/Password**: Try signing up with a test email
2. **Google OAuth**: Click "Sign in with Google" and authorize
3. **GitHub OAuth**: Click "Sign in with GitHub" and authorize

Check the **Users** tab in Firebase Console to see if test users appear.

---

## Completion Criteria

- [x] Email/Password authentication enabled in Firebase Console
- [x] Google OAuth provider enabled in Firebase Console
- [x] GitHub OAuth app created on GitHub
- [x] GitHub OAuth provider enabled in Firebase Console with credentials
- [x] All authorized domains added to Firebase
- [x] Google OAuth redirect URIs configured in Google Cloud Console
- [x] All three providers show as "Enabled" in Firebase Console

---

## Troubleshooting

### "Domain not authorized" Error

**Solution**: Add the domain to Firebase Console → Authentication → Settings → Authorized domains

### "Redirect URI mismatch" Error (Google)

**Solution**: Verify the exact redirect URI in Google Cloud Console → Credentials matches the one Firebase is using

### "Invalid OAuth callback URL" Error (GitHub)

**Solution**: Ensure the callback URL in GitHub OAuth app settings is exactly: `https://utxoiq.firebaseapp.com/__/auth/handler`

---

## Next Steps

After completing this task:

1. ✅ Task 1.2 complete - Mark as done
2. ⏳ Task 1.3 - Write unit tests for Firebase integration
3. ⏳ Task 2 - Implement user profile database models

---

## Reference Documentation

- Full configuration guide: `docs/firebase-oauth-configuration.md`
- Firebase Console: https://console.firebase.google.com/project/utxoiq
- Google Cloud Console: https://console.cloud.google.com/?project=utxoiq
- GitHub OAuth Apps: https://github.com/settings/developers
