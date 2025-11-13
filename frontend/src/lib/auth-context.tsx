'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  User as FirebaseUser,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  GoogleAuthProvider,
  GithubAuthProvider,
  signInWithPopup,
  sendPasswordResetEmail,
  sendEmailVerification,
} from 'firebase/auth';
import { auth, db } from './firebase';
import { doc, getDoc } from 'firebase/firestore';

interface UserProfile {
  id: string;
  email: string;
  displayName?: string;
  role: string;
  subscriptionTier: 'free' | 'pro' | 'power';
}

interface AuthContextType {
  user: UserProfile | null;
  firebaseUser: FirebaseUser | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signInWithGithub: () => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  refreshProfile: () => Promise<void>;
  getIdToken: () => Promise<string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch user profile from backend or Firestore
  const fetchUserProfile = async (idToken: string, firebaseUser: FirebaseUser) => {
    try {
      const response = await fetch('/api/v1/auth/profile', {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      if (response.ok) {
        const profile = await response.json();
        setUser(profile);
        return;
      }
    } catch (error) {
      console.error('Failed to fetch user profile from backend:', error);
    }

    // Fallback 1: Try Firestore user profile
    if (db) {
      try {
        console.log('🔍 Fetching user profile from Firestore for UID:', firebaseUser.uid);
        const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));
        console.log('📄 Firestore document exists:', userDoc.exists());
        if (userDoc.exists()) {
          const userData = userDoc.data();
          console.log('✅ Firestore user data:', userData);
          setUser({
            id: firebaseUser.uid,
            email: firebaseUser.email || '',
            displayName: firebaseUser.displayName || undefined,
            role: userData.role || 'user',
            subscriptionTier: userData.subscriptionTier || 'free',
          });
          return;
        } else {
          console.warn('⚠️ No Firestore document found for user');
        }
      } catch (error) {
        console.error('❌ Failed to fetch user profile from Firestore:', error);
      }
    } else {
      console.warn('⚠️ Firestore (db) is not initialized');
    }

    // Fallback 2: Use Firebase custom claims
    try {
      const tokenResult = await firebaseUser.getIdTokenResult();
      const claims = tokenResult.claims;
      
      setUser({
        id: firebaseUser.uid,
        email: firebaseUser.email || '',
        displayName: firebaseUser.displayName || undefined,
        role: (claims.role as string) || 'user',
        subscriptionTier: (claims.subscriptionTier as 'free' | 'pro' | 'power') || 'free',
      });
    } catch (error) {
      console.error('Failed to get Firebase custom claims:', error);
      // Final fallback: basic user profile
      setUser({
        id: firebaseUser.uid,
        email: firebaseUser.email || '',
        displayName: firebaseUser.displayName || undefined,
        role: 'user',
        subscriptionTier: 'free',
      });
    }
  };

  // Listen to Firebase auth state
  useEffect(() => {
    if (typeof window === 'undefined' || !auth) {
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setFirebaseUser(firebaseUser);

      if (firebaseUser) {
        const idToken = await firebaseUser.getIdToken();
        await fetchUserProfile(idToken, firebaseUser);
      } else {
        setUser(null);
      }

      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  // Auto-refresh token before expiry
  useEffect(() => {
    if (!firebaseUser) return;

    const interval = setInterval(async () => {
      try {
        await firebaseUser.getIdToken(true); // Force refresh
      } catch (error) {
        console.error('Token refresh failed:', error);
      }
    }, 50 * 60 * 1000); // Refresh every 50 minutes

    return () => clearInterval(interval);
  }, [firebaseUser]);

  const signIn = async (email: string, password: string) => {
    if (!auth) {
      throw new Error(
        'Firebase Auth not configured. Please set up Firebase credentials in .env.local. See docs/firebase-quick-start.md'
      );
    }
    await signInWithEmailAndPassword(auth, email, password);
  };

  const signUp = async (email: string, password: string) => {
    if (!auth) {
      throw new Error(
        'Firebase Auth not configured. Please set up Firebase credentials in .env.local. See docs/firebase-quick-start.md'
      );
    }
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    // Send email verification
    if (userCredential.user) {
      await sendEmailVerification(userCredential.user);
    }
  };

  const signInWithGoogle = async () => {
    if (!auth) {
      throw new Error(
        'Firebase Auth not configured. Please set up Firebase credentials in .env.local. See docs/firebase-quick-start.md'
      );
    }
    const provider = new GoogleAuthProvider();
    await signInWithPopup(auth, provider);
  };

  const signInWithGithub = async () => {
    if (!auth) {
      throw new Error(
        'Firebase Auth not configured. Please set up Firebase credentials in .env.local. See docs/firebase-quick-start.md'
      );
    }
    const provider = new GithubAuthProvider();
    await signInWithPopup(auth, provider);
  };

  const signOut = async () => {
    if (!auth) {
      throw new Error(
        'Firebase Auth not configured. Please set up Firebase credentials in .env.local. See docs/firebase-quick-start.md'
      );
    }
    await firebaseSignOut(auth);
    setUser(null);
  };

  const resetPassword = async (email: string) => {
    if (!auth) {
      throw new Error(
        'Firebase Auth not configured. Please set up Firebase credentials in .env.local. See docs/firebase-quick-start.md'
      );
    }
    await sendPasswordResetEmail(auth, email);
  };

  const refreshProfile = async () => {
    if (firebaseUser) {
      const idToken = await firebaseUser.getIdToken();
      await fetchUserProfile(idToken, firebaseUser);
    }
  };

  const getIdToken = async (): Promise<string> => {
    if (!firebaseUser) {
      throw new Error('No user signed in');
    }
    return await firebaseUser.getIdToken();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        firebaseUser,
        loading,
        signIn,
        signUp,
        signInWithGoogle,
        signInWithGithub,
        signOut,
        resetPassword,
        refreshProfile,
        getIdToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
