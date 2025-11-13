/**
 * Firebase Admin Setup Script
 * 
 * This script helps set up admin privileges for a Firebase user.
 * Run this after creating your Firebase project and enabling authentication.
 * 
 * Prerequisites:
 * 1. Firebase project created
 * 2. Firebase Admin SDK service account key downloaded
 * 3. User account created in Firebase Authentication
 * 
 * Usage:
 *   node scripts/setup-firebase-admin.js vosika@gmail.com
 */

const admin = require('firebase-admin');
const path = require('path');

// Initialize Firebase Admin SDK
// You'll need to download the service account key from Firebase Console:
// Project Settings → Service Accounts → Generate New Private Key
const serviceAccountPath = path.join(__dirname, '../firebase-admin-key.json');

try {
  const serviceAccount = require(serviceAccountPath);
  
  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
  });

  console.log('✅ Firebase Admin SDK initialized');
} catch (error) {
  console.error('❌ Error: Could not find firebase-admin-key.json');
  console.error('Please download your service account key from Firebase Console:');
  console.error('Project Settings → Service Accounts → Generate New Private Key');
  console.error('Save it as firebase-admin-key.json in the project root');
  process.exit(1);
}

async function setAdminRole(email) {
  try {
    // Get user by email
    const user = await admin.auth().getUserByEmail(email);
    
    // Set custom claims for admin role
    await admin.auth().setCustomUserClaims(user.uid, {
      role: 'admin',
      subscriptionTier: 'power',
      isAdmin: true,
    });

    console.log(`✅ Admin privileges granted to ${email}`);
    console.log(`   User ID: ${user.uid}`);
    console.log(`   Role: admin`);
    console.log(`   Subscription: power`);
    
    // Verify the claims were set
    const updatedUser = await admin.auth().getUser(user.uid);
    console.log('\n📋 Custom Claims:', updatedUser.customClaims);
    
    console.log('\n⚠️  Note: User needs to sign out and sign back in for changes to take effect');
    
  } catch (error) {
    if (error.code === 'auth/user-not-found') {
      console.error(`❌ User ${email} not found in Firebase Authentication`);
      console.error('Please create the account first by signing up through the app');
    } else {
      console.error('❌ Error setting admin role:', error.message);
    }
    process.exit(1);
  }
}

// Get email from command line argument
const email = process.argv[2];

if (!email) {
  console.error('❌ Error: Email address required');
  console.error('Usage: node scripts/setup-firebase-admin.js <email>');
  console.error('Example: node scripts/setup-firebase-admin.js vosika@gmail.com');
  process.exit(1);
}

// Validate email format
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!emailRegex.test(email)) {
  console.error('❌ Error: Invalid email format');
  process.exit(1);
}

console.log(`🔧 Setting up admin privileges for ${email}...\n`);

setAdminRole(email)
  .then(() => {
    console.log('\n✅ Setup complete!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Setup failed:', error);
    process.exit(1);
  });
