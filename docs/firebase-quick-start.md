# Firebase Quick Start - Admin Setup

## Quick Steps to Set Up vosika@gmail.com as Admin

### 1. Create Firebase Project (5 minutes)
```
1. Go to https://console.firebase.google.com/
2. Create/select "utxoiq-project"
3. Enable Authentication → Google sign-in
4. Copy Firebase config values
```

### 2. Update Frontend Config
Edit `frontend/.env.local`:
```bash
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key_here
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq-project
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=utxoiq-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

### 3. Start Frontend & Sign Up
```bash
cd frontend
npm run dev
```
Then:
- Open http://localhost:3000/sign-up
- Click "Continue with Google"
- Sign in with **vosika@gmail.com**

### 4. Set Admin Role (Choose One Method)

#### Method A: Firebase Console (Easiest)
```
1. Firebase Console → Authentication → Users
2. Find vosika@gmail.com
3. Click ⋮ → Set custom user claims
4. Paste:
   {
     "role": "admin",
     "subscriptionTier": "power",
     "isAdmin": true
   }
5. Save
6. Sign out & sign back in
```

#### Method B: Admin Script
```bash
# Download service account key from Firebase Console
# Save as firebase-admin-key.json in project root

npm install firebase-admin
node scripts/setup-firebase-admin.js vosika@gmail.com
```

### 5. Verify Admin Access
- Sign in to app
- Check header shows "power" badge
- You now have full admin access!

## What You Get as Admin

✅ **Full Platform Access**
- All features unlocked
- No rate limits
- API access
- Data export

✅ **Admin Privileges**
- Access to admin-only endpoints
- Dashboard customization
- User management (when implemented)
- System monitoring

✅ **Power Tier Benefits**
- Real-time insights
- Unlimited alerts
- Full AI reasoning feed
- CSV/JSON export
- API access

## Troubleshooting

**Can't sign in with Google?**
- Check Google provider is enabled in Firebase Console
- Verify authDomain in .env.local
- Clear browser cache

**Admin role not working?**
- Sign out completely
- Clear cookies
- Sign back in (custom claims load on sign-in)

**Firebase not initialized?**
- Check all NEXT_PUBLIC_FIREBASE_* vars are set
- Restart dev server after updating .env.local

## Security Note

The Firebase config values in `.env.local` are **public** and safe to commit. They're meant to be exposed in the browser. Security is handled by Firebase Authentication rules and backend validation.

## Next Steps

After admin setup:
1. Configure backend Firebase Admin SDK
2. Set up Stripe for payments
3. Deploy to production
4. Add more admin features

See `docs/firebase-setup-guide.md` for detailed instructions.
