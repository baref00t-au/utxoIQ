# Design Document

## Overview

This design implements a comprehensive authentication and authorization system using Firebase Auth for identity management, JWT tokens for stateless authentication, and role-based access control (RBAC) for fine-grained permissions. The system integrates with Stripe for subscription management and enforces tiered access to platform features.

## Architecture

### High-Level Architecture

```
┌──────────────┐
│   Frontend   │
│  (Next.js)   │
└──────┬───────┘
       │
       │ JWT Token
       │
┌──────▼───────┐      ┌─────────────┐
│   FastAPI    │◄────►│  Firebase   │
│   web-api    │      │    Auth     │
└──────┬───────┘      └─────────────┘
       │
       │
┌──────▼───────┐      ┌─────────────┐
│  Cloud SQL   │      │    Redis    │
│ (User Data)  │      │(Rate Limit) │
└──────────────┘      └─────────────┘
       │
       │
┌──────▼───────┐
│    Stripe    │
│  (Payments)  │
└──────────────┘
```

### Authentication Flow

```
User → Frontend → Firebase Auth → JWT Token → Backend API
                                      ↓
                                 Validate Token
                                      ↓
                                 Check Permissions
                                      ↓
                                 Process Request
```

### Authorization Flow

```
Request → Extract JWT → Validate Signature → Extract Claims
            ↓
       Check Role → Check Subscription Tier → Check Rate Limit
            ↓
       Allow/Deny
```

## Components and Interfaces

### 1. Firebase Auth Integration

#### Firebase Configuration
```python
import firebase_admin
from firebase_admin import credentials, auth

class FirebaseAuthService:
    def __init__(self, credentials_path: str):
        """Initialize Firebase Admin SDK"""
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
    
    async def verify_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return decoded claims"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except auth.InvalidIdTokenError:
            raise AuthenticationError("Invalid token")
        except auth.ExpiredIdTokenError:
            raise AuthenticationError("Token expired")
    
    async def get_user(self, uid: str) -> auth.UserRecord:
        """Get user record from Firebase"""
        return auth.get_user(uid)
    
    async def revoke_refresh_tokens(self, uid: str) -> None:
        """Revoke all refresh tokens for a user"""
        auth.revoke_refresh_tokens(uid)
```

### 2. User Profile Models

#### Database Model
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    firebase_uid = Column(String(128), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user", nullable=False)  # user, admin, service
    subscription_tier = Column(String(20), default="free", nullable=False)  # free, pro, power
    stripe_customer_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_user_firebase_uid', 'firebase_uid'),
        Index('idx_user_email', 'email'),
    )

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False)  # SHA256 hash
    key_prefix = Column(String(20), nullable=False)  # First 8 chars for display
    name = Column(String(100), nullable=False)
    scopes = Column(ARRAY(String), default=[])  # ['insights:read', 'alerts:write']
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    user = relationship("User", backref="api_keys")
    
    __table_args__ = (
        Index('idx_apikey_hash', 'key_hash'),
        Index('idx_apikey_user', 'user_id'),
    )
```

#### Pydantic Schemas
```python
class UserProfile(BaseModel):
    id: UUID
    email: str
    display_name: Optional[str]
    role: str
    subscription_tier: str
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    display_name: Optional[str] = None

class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = []

class APIKeyResponse(BaseModel):
    id: UUID
    key_prefix: str
    name: str
    scopes: List[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class APIKeyWithSecret(APIKeyResponse):
    key: str  # Only returned on creation
```

### 3. Authentication Middleware

#### JWT Token Validation
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    firebase_service: FirebaseAuthService = Depends(),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extract and validate JWT token, return user"""
    token = credentials.credentials
    
    try:
        # Verify Firebase token
        decoded_token = await firebase_service.verify_token(token)
        firebase_uid = decoded_token['uid']
        
        # Get or create user in database
        user = await get_user_by_firebase_uid(db, firebase_uid)
        if not user:
            # Create user on first login
            user = await create_user_from_firebase(db, decoded_token)
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return user
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
```

#### API Key Validation
```python
async def get_current_user_from_api_key(
    api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate API key and return associated user"""
    
    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Look up API key
    api_key_record = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.revoked_at.is_(None)
        )
    )
    api_key_record = api_key_record.scalar_one_or_none()
    
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Update last used timestamp
    api_key_record.last_used_at = datetime.utcnow()
    await db.commit()
    
    # Return associated user
    return api_key_record.user
```

### 4. Authorization System

#### Role-Based Access Control
```python
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SERVICE = "service"

class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    POWER = "power"

def require_role(required_role: Role):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(
            current_user: User = Depends(get_current_user),
            *args, **kwargs
        ):
            if current_user.role != required_role.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {required_role.value} role"
                )
            return await func(current_user=current_user, *args, **kwargs)
        return wrapper
    return decorator

def require_subscription(min_tier: SubscriptionTier):
    """Decorator to require minimum subscription tier"""
    tier_hierarchy = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 1,
        SubscriptionTier.POWER: 2,
    }
    
    def decorator(func):
        async def wrapper(
            current_user: User = Depends(get_current_user),
            *args, **kwargs
        ):
            user_tier_level = tier_hierarchy.get(current_user.subscription_tier, 0)
            required_tier_level = tier_hierarchy.get(min_tier, 0)
            
            if user_tier_level < required_tier_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {min_tier.value} subscription or higher"
                )
            return await func(current_user=current_user, *args, **kwargs)
        return wrapper
    return decorator
```

#### Scope-Based Access Control (for API Keys)
```python
def require_scope(required_scope: str):
    """Decorator to require specific API key scope"""
    def decorator(func):
        async def wrapper(
            api_key: str = Header(..., alias="X-API-Key"),
            db: AsyncSession = Depends(get_db),
            *args, **kwargs
        ):
            # Get API key record
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            api_key_record = await get_api_key_by_hash(db, key_hash)
            
            if not api_key_record:
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # Check scope
            if required_scope not in api_key_record.scopes:
                raise HTTPException(
                    status_code=403,
                    detail=f"API key missing required scope: {required_scope}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 5. Rate Limiting

#### Redis-Based Rate Limiter
```python
class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        user_id: str,
        tier: SubscriptionTier,
        window_seconds: int = 3600
    ) -> Tuple[bool, int]:
        """Check if user is within rate limit"""
        
        # Define limits per tier
        limits = {
            SubscriptionTier.FREE: 100,
            SubscriptionTier.PRO: 1000,
            SubscriptionTier.POWER: 10000,
        }
        
        limit = limits.get(tier, 100)
        key = f"rate_limit:{user_id}:{int(time.time() // window_seconds)}"
        
        # Increment counter
        current = await self.redis.incr(key)
        
        # Set expiry on first request
        if current == 1:
            await self.redis.expire(key, window_seconds)
        
        # Check limit
        remaining = max(0, limit - current)
        allowed = current <= limit
        
        return allowed, remaining

async def rate_limit_dependency(
    current_user: User = Depends(get_current_user),
    rate_limiter: RateLimiter = Depends()
):
    """Dependency to enforce rate limiting"""
    allowed, remaining = await rate_limiter.check_rate_limit(
        str(current_user.id),
        current_user.subscription_tier
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"X-RateLimit-Remaining": "0"}
        )
    
    return remaining
```

### 6. Frontend Auth Integration

#### Auth Context (React)
```typescript
// lib/auth.ts
import { createContext, useContext, useEffect, useState } from 'react';
import { 
  getAuth, 
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  GithubAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User as FirebaseUser
} from 'firebase/auth';

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
  signInWithGoogle: () => Promise<void>;
  signInWithGithub: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  
  const auth = getAuth();
  
  // Fetch user profile from backend
  const fetchUserProfile = async (idToken: string) => {
    const response = await fetch('/api/v1/auth/profile', {
      headers: { Authorization: `Bearer ${idToken}` }
    });
    if (response.ok) {
      const profile = await response.json();
      setUser(profile);
    }
  };
  
  // Listen to Firebase auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setFirebaseUser(firebaseUser);
      
      if (firebaseUser) {
        const idToken = await firebaseUser.getIdToken();
        await fetchUserProfile(idToken);
      } else {
        setUser(null);
      }
      
      setLoading(false);
    });
    
    return unsubscribe;
  }, []);
  
  // Auto-refresh token before expiry
  useEffect(() => {
    if (!firebaseUser) return;
    
    const interval = setInterval(async () => {
      await firebaseUser.getIdToken(true); // Force refresh
    }, 50 * 60 * 1000); // Refresh every 50 minutes
    
    return () => clearInterval(interval);
  }, [firebaseUser]);
  
  const signIn = async (email: string, password: string) => {
    await signInWithEmailAndPassword(auth, email, password);
  };
  
  const signInWithGoogle = async () => {
    const provider = new GoogleAuthProvider();
    await signInWithPopup(auth, provider);
  };
  
  const signInWithGithub = async () => {
    const provider = new GithubAuthProvider();
    await signInWithPopup(auth, provider);
  };
  
  const signOut = async () => {
    await firebaseSignOut(auth);
  };
  
  const refreshProfile = async () => {
    if (firebaseUser) {
      const idToken = await firebaseUser.getIdToken();
      await fetchUserProfile(idToken);
    }
  };
  
  return (
    <AuthContext.Provider value={{
      user,
      firebaseUser,
      loading,
      signIn,
      signInWithGoogle,
      signInWithGithub,
      signOut,
      refreshProfile
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
```

#### Protected Route Component
```typescript
// components/ProtectedRoute.tsx
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function ProtectedRoute({ 
  children,
  requireTier
}: { 
  children: React.ReactNode;
  requireTier?: 'pro' | 'power';
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  
  useEffect(() => {
    if (!loading && !user) {
      router.push('/sign-in');
    }
    
    if (!loading && user && requireTier) {
      const tierHierarchy = { free: 0, pro: 1, power: 2 };
      const userLevel = tierHierarchy[user.subscriptionTier];
      const requiredLevel = tierHierarchy[requireTier];
      
      if (userLevel < requiredLevel) {
        router.push('/pricing');
      }
    }
  }, [user, loading, requireTier]);
  
  if (loading) return <div>Loading...</div>;
  if (!user) return null;
  
  return <>{children}</>;
}
```

## Data Models

### API Endpoints

#### Authentication Endpoints
```python
@router.post("/auth/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserProfile.from_orm(current_user)

@router.patch("/auth/profile")
async def update_profile(
    update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    current_user.display_name = update.display_name
    await db.commit()
    return UserProfile.from_orm(current_user)

@router.post("/auth/api-keys")
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new API key"""
    # Check limit
    existing_keys = await count_user_api_keys(db, current_user.id)
    if existing_keys >= 5:
        raise HTTPException(400, "Maximum 5 API keys allowed")
    
    # Generate key
    key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:8]
    
    # Store in database
    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        scopes=key_data.scopes
    )
    db.add(api_key)
    await db.commit()
    
    # Return key only once
    return APIKeyWithSecret(
        **APIKeyResponse.from_orm(api_key).dict(),
        key=key
    )

@router.delete("/auth/api-keys/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke API key"""
    api_key = await get_api_key(db, key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(404, "API key not found")
    
    api_key.revoked_at = datetime.utcnow()
    await db.commit()
    return {"message": "API key revoked"}
```

## Error Handling

### Authentication Errors
```python
class AuthenticationError(Exception):
    """Base authentication error"""
    pass

class TokenExpiredError(AuthenticationError):
    """Token has expired"""
    pass

class InvalidTokenError(AuthenticationError):
    """Token is invalid"""
    pass

class InsufficientPermissionsError(Exception):
    """User lacks required permissions"""
    pass

# Error handlers
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"}
    )

@app.exception_handler(InsufficientPermissionsError)
async def permission_error_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)}
    )
```

## Testing Strategy

### Unit Tests
- Token validation logic
- Role and subscription tier checks
- API key generation and hashing
- Rate limit calculation

### Integration Tests
- End-to-end authentication flow
- Protected endpoint access
- API key authentication
- Rate limiting enforcement
- Subscription tier restrictions

### Security Tests
- Token tampering detection
- Expired token rejection
- Invalid signature rejection
- SQL injection in user queries
- Rate limit bypass attempts

## Configuration

### Environment Variables
```bash
# Firebase
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
FIREBASE_PROJECT_ID=utxoiq-prod

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=RS256
JWT_EXPIRY_MINUTES=60

# Rate Limiting
RATE_LIMIT_WINDOW_SECONDS=3600
RATE_LIMIT_FREE_TIER=100
RATE_LIMIT_PRO_TIER=1000
RATE_LIMIT_POWER_TIER=10000

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Deployment Considerations

### Security Best Practices
- Store Firebase credentials in Secret Manager
- Use HTTPS only for all endpoints
- Implement CORS properly
- Enable Cloud Armor for DDoS protection
- Rotate API keys regularly
- Monitor for suspicious authentication patterns

### Performance Optimization
- Cache Firebase public keys for token validation
- Use Redis for rate limiting counters
- Index database queries on firebase_uid and email
- Implement connection pooling for database
