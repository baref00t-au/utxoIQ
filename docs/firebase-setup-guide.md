# Firebase Authentication Setup Guide

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or select existing "utxoiq-project"
3. Follow the setup wizard

## Step 2: Enable Authentication Methods

1. In Firebase Console, go to **Authentication** → **Sign-in method**
2. Enable the following providers:
   - ✅ **Email/Password** - Click Enable
   - ✅ **Google** - Click Enable and configure:
     - Project support email: vosika@gmail.com
     - Click Save

## Step 3: Get Firebase Configuration

1. Go to **Project Settings** (gear icon) → **General**
2. Scroll down to "Your apps"
3. Click the **Web** icon (`</>`) to add a web app
4. Register app with nickname: "utxoIQ Frontend"
5. Copy the Firebase configuration object

It will look like this:
```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "utxoiq-project.firebaseapp.com",
  projectId: "utxoiq-project",
  storageBucket: "utxoiq-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

## Step 4: Update Frontend Configuration

Update `frontend/.env.local` with your Firebase config:

```bash
# Firebase Configuration (Frontend)
NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq-project
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=utxoiq-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abc123

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_WS_URL=ws://localhost:8080

# Development Mode
NODE_ENV=development

# Use mock data when backend is unavailable
NEXT_PUBLIC_USE_MOCK_DATA=true
```

## Step 5: Create Your Admin Account

### Option A: Sign Up with Google (Recommended)

1. Start the Next.js dev server:
   ```bash
   cd frontend
   npm run dev
   ```

2. Open http://localhost:3000/sign-up

3. Click "Continue with Google"

4. Sign in with **vosika@gmail.com**

5. Your account is now created in Firebase!

### Option B: Sign Up with Email/Password

1. Go to http://localhost:3000/sign-up
2. Enter email: vosika@gmail.com
3. Enter a password
4. Click "Create Account"
5. Verify your email (check inbox)

## Step 6: Set Admin Privileges

### Method 1: Using Firebase Console (Quick)

1. Go to Firebase Console → **Authentication** → **Users**
2. Find your user (vosika@gmail.com)
3. Click the three dots → **Set custom user claims**
4. Add this JSON:
   ```json
   {
     "role": "admin",
     "subscriptionTier": "power",
     "isAdmin": true
   }
   ```
5. Click **Save**
6. Sign out and sign back in to the app

### Method 2: Using Admin Script (Automated)

1. Download Firebase Admin SDK service account key:
   - Firebase Console → **Project Settings** → **Service Accounts**
   - Click "Generate new private key"
   - Save as `firebase-admin-key.json` in project root

2. Install Firebase Admin SDK:
   ```bash
   npm install firebase-admin
   ```

3. Run the admin setup script:
   ```bash
   node scripts/setup-firebase-admin.js vosika@gmail.com
   ```

4. Sign out and sign back in to the app

## Step 7: Verify Admin Access

1. Sign in to the app with vosika@gmail.com
2. Check the header - you should see "power" badge
3. You now have full admin access to:
   - All insights and features
   - Dashboard customization
   - API access
   - Admin-only endpoints

## Security Notes

### Public Keys (Safe to Commit)
These Firebase config values are **public** and safe to commit:
- `apiKey`
- `authDomain`
- `projectId`
- `storageBucket`
- `messagingSenderId`
- `appId`

### Private Keys (NEVER Commit)
These should **NEVER** be committed to Git:
- `firebase-admin-key.json` (service account key)
- Backend service account credentials

Add to `.gitignore`:
```
firebase-admin-key.json
*-service-account.json
```

## Troubleshooting

### "Firebase not initialized" error
- Check that all `NEXT_PUBLIC_FIREBASE_*` env vars are set
- Restart the Next.js dev server after updating `.env.local`

### "User not found" when setting admin
- Make sure you've created the account first by signing up
- Check the email address is correct
- Verify the user exists in Firebase Console → Authentication

### Google Sign-In not working
- Verify Google provider is enabled in Firebase Console
- Check that `authDomain` is correct in `.env.local`
- Make sure you're using the correct Google account

### Custom claims not taking effect
- Sign out completely from the app
- Clear browser cookies/cache
- Sign back in
- Custom claims are loaded on sign-in, not automatically

## Next Steps

After setting up your admin account:

1. **Set up backend authentication**:
   - Configure Firebase Admin SDK in backend services
   - Add JWT token validation middleware
   - Implement role-based access control

2. **Configure Stripe**:
   - Set up Stripe account
   - Add Stripe keys to backend `.env`
   - Configure webhook endpoints

3. **Deploy to production**:
   - Update Firebase authorized domains
   - Set production environment variables
   - Configure OAuth redirect URIs

## Support

If you encounter issues:
- Check Firebase Console logs
- Review browser console for errors
- Verify all environment variables are set
- Ensure Firebase project billing is enabled (for production)
