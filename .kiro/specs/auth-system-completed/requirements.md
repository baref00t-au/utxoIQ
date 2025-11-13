# Requirements Document

## Introduction

This specification defines the authentication and authorization system for the utxoIQ platform. The system will integrate Firebase Auth for user identity management and implement role-based access control (RBAC) to secure API endpoints, protect user data, and enable tiered subscription features. The system must support multiple authentication methods while maintaining sub-200ms token validation performance.

## Glossary

- **Firebase Auth**: Google's authentication service providing user identity management
- **JWT Token**: JSON Web Token used for stateless authentication
- **RBAC**: Role-Based Access Control system for managing user permissions
- **API Key**: Long-lived token for programmatic API access
- **Session**: User authentication state maintained across requests
- **Rate Limiting**: Mechanism to restrict request frequency per user or API key
- **Subscription Tier**: User access level (Free, Pro, Power) determining feature availability
- **Protected Endpoint**: API route requiring authentication and authorization
- **Token Validation**: Process of verifying JWT signature and claims
- **Refresh Token**: Long-lived token used to obtain new access tokens

## Requirements

### Requirement 1

**User Story:** As a new user, I want to sign up using email/password or social providers, so that I can access the platform quickly without creating yet another password.

#### Acceptance Criteria

1. THE Authentication System SHALL support email/password registration with email verification
2. THE Authentication System SHALL support Google OAuth authentication
3. THE Authentication System SHALL support GitHub OAuth authentication
4. WHEN a user completes registration, THE Authentication System SHALL create a user profile record within 2 seconds
5. THE Authentication System SHALL assign the "Free" subscription tier to new users by default

### Requirement 2

**User Story:** As a registered user, I want to sign in securely and stay authenticated across sessions, so that I don't have to log in repeatedly.

#### Acceptance Criteria

1. WHEN a user provides valid credentials, THE Authentication System SHALL issue a JWT access token within 200 milliseconds
2. THE Authentication System SHALL issue a refresh token valid for 30 days
3. THE Authentication System SHALL validate JWT tokens on protected endpoints within 50 milliseconds
4. WHEN an access token expires, THE Authentication System SHALL accept a valid refresh token to issue a new access token
5. THE Authentication System SHALL invalidate all user tokens when the user logs out

### Requirement 3

**User Story:** As a backend developer, I want API endpoints protected by authentication, so that only authorized users can access their data and perform actions.

#### Acceptance Criteria

1. THE Authorization System SHALL reject requests to protected endpoints without a valid JWT token with HTTP 401 status
2. THE Authorization System SHALL extract user identity from JWT claims for request context
3. THE Authorization System SHALL validate token signature using Firebase public keys
4. THE Authorization System SHALL reject expired tokens with HTTP 401 status
5. THE Authorization System SHALL log all authentication failures for security monitoring

### Requirement 4

**User Story:** As a power user, I want to generate API keys for programmatic access, so that I can integrate utxoIQ data into my trading systems.

#### Acceptance Criteria

1. WHEN a user requests an API key, THE API Key System SHALL generate a unique key with a prefix identifying the user
2. THE API Key System SHALL allow users to create up to 5 active API keys
3. THE API Key System SHALL support API key scopes limiting access to specific endpoints
4. THE API Key System SHALL validate API keys within 50 milliseconds
5. THE API Key System SHALL allow users to revoke API keys immediately

### Requirement 5

**User Story:** As a product manager, I want role-based access control implemented, so that admin users can access monitoring dashboards while regular users cannot.

#### Acceptance Criteria

1. THE RBAC System SHALL support three roles: "user", "admin", and "service"
2. WHEN a user attempts to access an admin endpoint, THE RBAC System SHALL verify the user has the "admin" role
3. THE RBAC System SHALL reject unauthorized role access with HTTP 403 status
4. THE RBAC System SHALL allow role assignment only by existing admin users
5. THE RBAC System SHALL log all authorization failures with user identity and attempted resource

### Requirement 6

**User Story:** As a security engineer, I want rate limiting enforced per user and API key, so that the system is protected from abuse and excessive usage.

#### Acceptance Criteria

1. THE Rate Limiting System SHALL limit Free tier users to 100 requests per hour
2. THE Rate Limiting System SHALL limit Pro tier users to 1000 requests per hour
3. THE Rate Limiting System SHALL limit Power tier users to 10000 requests per hour
4. WHEN a user exceeds their rate limit, THE Rate Limiting System SHALL reject requests with HTTP 429 status
5. THE Rate Limiting System SHALL reset rate limit counters every hour

### Requirement 7

**User Story:** As a subscription manager, I want user subscription tiers enforced at the API level, so that users can only access features included in their plan.

#### Acceptance Criteria

1. THE Subscription System SHALL store user subscription tier in the user profile
2. WHEN a Free tier user attempts to access Pro features, THE Subscription System SHALL reject the request with HTTP 403 status
3. THE Subscription System SHALL allow access to AI chat endpoints only for Pro and Power tier users
4. THE Subscription System SHALL allow custom alert creation only for Pro and Power tier users
5. THE Subscription System SHALL update user tier immediately upon successful Stripe payment

### Requirement 8

**User Story:** As a user, I want my profile information managed securely, so that I can update my preferences and view my subscription status.

#### Acceptance Criteria

1. THE User Profile System SHALL store user email, display name, and subscription tier
2. THE User Profile System SHALL allow users to update their display name and preferences
3. THE User Profile System SHALL prevent users from modifying other users' profiles
4. THE User Profile System SHALL return user profile data within 100 milliseconds
5. THE User Profile System SHALL not expose sensitive data like password hashes in API responses

### Requirement 9

**User Story:** As a compliance officer, I want user authentication events logged, so that we can audit access patterns and investigate security incidents.

#### Acceptance Criteria

1. THE Audit System SHALL log all successful login attempts with timestamp and IP address
2. THE Audit System SHALL log all failed login attempts with reason
3. THE Audit System SHALL log API key creation and revocation events
4. THE Audit System SHALL log role assignment changes
5. THE Audit System SHALL retain audit logs for 1 year in Cloud Logging

### Requirement 10

**User Story:** As a frontend developer, I want authentication state managed in the React app, so that I can show/hide features based on user authentication and subscription tier.

#### Acceptance Criteria

1. THE Frontend Auth System SHALL provide an AuthContext with user state
2. THE Frontend Auth System SHALL automatically refresh access tokens before expiration
3. THE Frontend Auth System SHALL redirect unauthenticated users to the login page when accessing protected routes
4. THE Frontend Auth System SHALL display user subscription tier in the header
5. THE Frontend Auth System SHALL clear auth state and redirect to login on token expiration
