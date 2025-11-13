# Implementation Plan

- [x] 1. Set up Firebase Auth integration





  - Initialize Firebase Admin SDK in backend
  - Configure Firebase project with authentication providers
  - Set up Firebase credentials in Secret Manager
  - _Requirements: 1, 2_

- [x] 1.1 Create Firebase Auth service



  - Implement FirebaseAuthService class with token verification
  - Add method to verify ID tokens and extract claims
  - Add method to get user records from Firebase
  - Add method to revoke refresh tokens
  - _Requirements: 2, 3_



- [x] 1.2 Configure authentication providers
  - Enable email/password authentication in Firebase Console
  - Enable Google OAuth provider
  - Enable GitHub OAuth provider
  - Configure OAuth redirect URLs
  - _Requirements: 1_

- [x] 1.3 Write unit tests for Firebase integration




  - Test token verification with valid tokens
  - Test token verification with expired tokens
  - Test token verification with invalid signatures
  - _Requirements: 2, 3_

- [x] 2. Implement user profile database models





  - Create User model with Firebase UID, email, role, and subscription tier
  - Create APIKey model with user relationship and scopes
  - Create database migrations for user tables
  - Add indexes for firebase_uid and email lookups
  - _Requirements: 1, 8_

- [x] 2.1 Create user management service


  - Implement create_user_from_firebase method for first-time login
  - Implement get_user_by_firebase_uid query method
  - Implement update_user_profile method
  - Implement get_user_by_email query method
  - _Requirements: 1, 8_

- [x] 2.2 Write unit tests for user models



  - Test user creation with valid data
  - Test unique constraints on firebase_uid and email
  - Test default values for role and subscription_tier
  - _Requirements: 1, 8_

- [x] 3. Implement authentication middleware





  - Create get_current_user dependency with JWT validation
  - Extract and verify Firebase token from Authorization header
  - Create or update user record on successful authentication
  - Update last_login_at timestamp
  - _Requirements: 2, 3_

- [x] 3.1 Implement API key authentication

  - Create get_current_user_from_api_key dependency
  - Hash and validate API key from X-API-Key header
  - Update last_used_at timestamp on successful validation
  - Return associated user for request context
  - _Requirements: 4_

- [x] 3.2 Add authentication error handling


  - Create custom AuthenticationError exception classes
  - Add exception handlers for 401 responses
  - Log all authentication failures with details
  - _Requirements: 3, 9_

- [x] 3.3 Write integration tests for authentication



  - Test successful JWT authentication
  - Test expired token rejection
  - Test invalid token rejection
  - Test API key authentication
  - Test missing authentication rejection
  - _Requirements: 2, 3, 4_

- [x] 4. Implement role-based access control





  - Create Role and SubscriptionTier enums
  - Implement require_role decorator for admin endpoints
  - Implement require_subscription decorator for tiered features
  - Add authorization error handling with 403 responses
  - _Requirements: 5, 7_

- [x] 4.1 Implement scope-based access control for API keys


  - Create require_scope decorator
  - Validate API key scopes against required scope
  - Reject requests with insufficient scopes
  - _Requirements: 4_

- [x] 4.2 Add authorization logging


  - Log all authorization failures with user identity
  - Log role assignment changes
  - Log subscription tier changes
  - _Requirements: 5, 9_

- [x] 4.3 Write tests for authorization



  - Test role-based access control
  - Test subscription tier restrictions
  - Test API key scope validation
  - Test authorization failure logging
  - _Requirements: 5, 7, 4_

- [x] 5. Implement rate limiting system





  - Create RateLimiter class with Redis backend
  - Implement check_rate_limit method with tier-based limits
  - Create rate_limit_dependency for FastAPI endpoints
  - Return rate limit headers in responses
  - _Requirements: 6_



- [x] 5.1 Configure rate limits per subscription tier

  - Set Free tier limit to 100 requests per hour
  - Set Pro tier limit to 1000 requests per hour
  - Set Power tier limit to 10000 requests per hour
  - Implement hourly window reset logic


  - _Requirements: 6_

- [x] 5.2 Add rate limit error handling

  - Return HTTP 429 when rate limit exceeded


  - Include X-RateLimit-Remaining header
  - Include X-RateLimit-Reset header with reset time
  - _Requirements: 6_

- [x] 5.3 Write tests for rate limiting


  - Test rate limit enforcement for each tier
  - Test rate limit counter reset after window
  - Test rate limit headers in responses
  - Test concurrent requests within limit
  - _Requirements: 6_

- [x] 6. Implement API key management endpoints





  - Create POST /api/v1/auth/api-keys endpoint for key creation
  - Generate secure random API keys with secrets module
  - Store hashed keys in database with SHA256
  - Enforce 5 API key limit per user
  - _Requirements: 4_

- [x] 6.1 Implement API key listing and revocation


  - Create GET /api/v1/auth/api-keys endpoint to list user's keys
  - Create DELETE /api/v1/auth/api-keys/{key_id} endpoint for revocation
  - Set revoked_at timestamp instead of deleting records
  - Return key prefix for identification in UI
  - _Requirements: 4_

- [x] 6.2 Write tests for API key management



  - Test API key creation and hashing
  - Test 5 key limit enforcement
  - Test API key listing
  - Test API key revocation
  - Test revoked key rejection
  - _Requirements: 4_

- [x] 7. Implement user profile endpoints





  - Create GET /api/v1/auth/profile endpoint
  - Create PATCH /api/v1/auth/profile endpoint for updates
  - Validate user can only update their own profile
  - Exclude sensitive fields from responses
  - _Requirements: 8_

- [x] 7.1 Add subscription tier management


  - Create endpoint to update subscription tier (admin only)
  - Integrate with Stripe webhook for automatic tier updates
  - Validate tier changes and log for audit
  - _Requirements: 7_

- [x] 7.2 Write tests for profile endpoints



  - Test profile retrieval
  - Test profile updates
  - Test unauthorized profile access prevention
  - Test subscription tier updates
  - _Requirements: 8, 7_

- [x] 8. Implement audit logging





  - Log successful login attempts with timestamp and IP
  - Log failed login attempts with reason
  - Log API key creation and revocation events
  - Log role and subscription tier changes
  - _Requirements: 9_

- [x] 8.1 Configure Cloud Logging retention


  - Set audit log retention to 1 year
  - Create log sink for long-term storage
  - Add structured logging with correlation IDs
  - _Requirements: 9_

- [x] 8.2 Write tests for audit logging



  - Verify login events are logged
  - Verify API key events are logged
  - Verify authorization events are logged
  - _Requirements: 9_

- [x] 9. Implement frontend authentication





  - Install Firebase SDK in Next.js app
  - Create AuthContext with user state management
  - Implement signIn, signInWithGoogle, signInWithGithub methods
  - Implement signOut method
  - _Requirements: 1, 2, 10_

- [x] 9.1 Create authentication pages


  - Create sign-in page with email/password form
  - Add Google and GitHub OAuth buttons
  - Create sign-up page with email verification
  - Add password reset functionality
  - _Requirements: 1, 2_

- [x] 9.2 Implement token refresh logic


  - Auto-refresh Firebase tokens before expiration
  - Fetch user profile from backend after authentication
  - Store user profile in AuthContext state
  - _Requirements: 2, 10_

- [x] 9.3 Create ProtectedRoute component


  - Redirect unauthenticated users to sign-in page
  - Check subscription tier for protected features
  - Redirect to pricing page if tier insufficient
  - Show loading state during auth check
  - _Requirements: 7, 10_

- [x] 9.4 Add user profile UI


  - Display user email and subscription tier in header
  - Create profile page with display name editor
  - Add API key management UI
  - Show rate limit usage
  - _Requirements: 8, 4, 6_

- [x] 9.5 Write frontend tests for authentication



  - Test sign-in flow
  - Test OAuth flows
  - Test protected route redirects
  - Test token refresh
  - _Requirements: 1, 2, 10_

- [x] 10. Protect existing API endpoints





  - Add authentication to insight endpoints
  - Add authentication to feedback endpoints
  - Add authentication to alert endpoints
  - Add role-based protection to monitoring endpoints
  - _Requirements: 3, 5_

- [x] 10.1 Add subscription tier restrictions


  - Restrict AI chat endpoints to Pro and Power tiers
  - Restrict custom alerts to Pro and Power tiers
  - Restrict advanced filtering to Power tier
  - _Requirements: 7_

- [x] 10.2 Add rate limiting to all endpoints


  - Apply rate limiting middleware to all API routes
  - Exclude health check endpoints from rate limiting
  - Add rate limit headers to all responses
  - _Requirements: 6_

- [x] 10.3 Write integration tests for protected endpoints



  - Test endpoint access with valid authentication
  - Test endpoint rejection without authentication
  - Test subscription tier enforcement
  - Test rate limiting on protected endpoints
  - _Requirements: 3, 5, 7, 6_

- [x] 11. Integrate Stripe for subscription management





  - Set up Stripe webhook endpoint
  - Handle subscription.created event
  - Handle subscription.updated event
  - Handle subscription.deleted event
  - _Requirements: 7_

- [x] 11.1 Update user subscription tier on payment


  - Update user.subscription_tier on successful payment
  - Downgrade tier on subscription cancellation
  - Handle trial periods
  - _Requirements: 7_

- [x] 11.2 Write tests for Stripe integration



  - Test webhook signature verification
  - Test subscription tier updates
  - Test subscription cancellation handling
  - _Requirements: 7_

- [x] 12. Update documentation





  - Document authentication flow and token format
  - Document API key creation and usage
  - Document role and subscription tier system
  - Document rate limiting policies
  - Create authentication guide for API users
  - Update docs\integration-roadmap.md
  - _Requirements: 1, 2, 3, 4, 5, 6, 7_
