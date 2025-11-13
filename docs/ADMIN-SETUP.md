# Admin Setup - Simple Method

## Quick Setup (5 minutes)

### Step 1: Enable Firestore

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your **utxoiq** project
3. Click **Firestore Database** in the left menu
4. Click **Create database**
5. Choose **Start in test mode** (for development)
6. Select a location (e.g., us-central)
7. Click **Enable**

### Step 2: Sign Up

1. Make sure your dev server is running:
   ```bash
   cd frontend
   npm run dev
   ```

2. Open http://localhost:3000/sign-up

3. Click **"Continue with Google"**

4. Sign in with **vosika@gmail.com**

5. You're now signed up!

### Step 3: Get Your User ID

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select **utxoiq** project
3. Go to **Authentication** → **Users**
4. Find **vosika@gmail.com**
5. Copy the **User UID** (looks like: `abc123def456...`)

### Step 4: Set Admin Role

Run this command with your User UID:

```bash
npm install firebase
node scripts/setup-admin-firestore.js YOUR_USER_UID_HERE
```

Example:
```bash
node scripts/setup-admin-firestore.js abc123def456ghi789
```

You should see:
```
✅ Admin profile created successfully!
   User ID: abc123def456ghi789
   Role: admin
   Subscription: power
```

### Step 5: Sign Out and Back In

1. In the app, click your email in the header
2. Click **Sign Out**
3. Sign back in with Google
4. You should now see **"power"** badge next to your email!

## Verify Admin Access

After signing back in, you should have:
- ✅ "power" badge in header
- ✅ Full access to all features
- ✅ No rate limits
- ✅ Admin privileges

## Troubleshooting

**"Cannot find module 'firebase'"**
```bash
npm install firebase
```

**"User ID required"**
- Make sure you copied the full User UID from Firebase Console
- It should be a long string like: `abc123def456ghi789`

**Admin role not showing**
- Make sure you signed out completely
- Clear browser cookies
- Sign back in
- User profile loads from Firestore on sign-in

**Firestore permission denied**
- Make sure you created Firestore database in test mode
- Test mode allows read/write for 30 days
- For production, you'll need proper security rules

## What's Next?

Now that you're an admin:

1. **Explore the platform** - All features unlocked
2. **Set up backend** - Configure backend services
3. **Add security rules** - Secure Firestore for production
4. **Deploy** - Deploy to production when ready

## Alternative: Manual Firestore Setup

If you prefer to do it manually:

1. Go to Firebase Console → **Firestore Database**
2. Click **Start collection**
3. Collection ID: `users`
4. Document ID: `YOUR_USER_UID`
5. Add fields:
   - `role` (string): `admin`
   - `subscriptionTier` (string): `power`
   - `isAdmin` (boolean): `true`
   - `createdAt` (timestamp): (current time)
6. Click **Save**
7. Sign out and back in

Done! You're now an admin.
