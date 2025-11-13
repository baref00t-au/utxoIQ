/**
 * Simple Admin Setup using Firestore
 * 
 * This script creates an admin user profile in Firestore.
 * No Firebase Admin SDK needed - just uses the Firebase client SDK.
 * 
 * Usage:
 *   1. Sign up with your account first (vosika@gmail.com)
 *   2. Get your User ID from Firebase Console → Authentication → Users
 *   3. Run: node scripts/setup-admin-firestore.js YOUR_USER_ID
 */

const { initializeApp } = require('firebase/app');
const { getFirestore, doc, setDoc } = require('firebase/firestore');

const firebaseConfig = {
  apiKey: "AIzaSyC-uPcyqfnL-n8tUKrndsoiGq1GPa6X7GA",
  authDomain: "utxoiq.firebaseapp.com",
  projectId: "utxoiq",
  storageBucket: "utxoiq.firebasestorage.app",
  messagingSenderId: "736762852981",
  appId: "1:736762852981:web:5ef6b4268948a89ea3aa3c"
};

async function setupAdmin(userId) {
  try {
    // Initialize Firebase
    const app = initializeApp(firebaseConfig);
    const db = getFirestore(app);

    // Create admin user profile
    const userProfile = {
      role: 'admin',
      subscriptionTier: 'power',
      isAdmin: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    await setDoc(doc(db, 'users', userId), userProfile);

    console.log('✅ Admin profile created successfully!');
    console.log('   User ID:', userId);
    console.log('   Role: admin');
    console.log('   Subscription: power');
    console.log('\n⚠️  Note: Sign out and sign back in for changes to take effect');

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

// Get user ID from command line
const userId = process.argv[2];

if (!userId) {
  console.error('❌ Error: User ID required');
  console.error('\nUsage: node scripts/setup-admin-firestore.js <user-id>');
  console.error('\nTo get your User ID:');
  console.error('1. Sign up at http://localhost:3000/sign-up');
  console.error('2. Go to Firebase Console → Authentication → Users');
  console.error('3. Copy your User UID');
  console.error('4. Run: node scripts/setup-admin-firestore.js YOUR_UID');
  process.exit(1);
}

console.log('🔧 Setting up admin profile...\n');
setupAdmin(userId);
