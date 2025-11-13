# Authentication Guide

## Overview

utxoIQ uses Firebase Auth for user identity management with JWT tokens for API authentication. The system supports multiple authentication methods and implements role-based access control (RBAC) with subscription tier enforcement.

## Table of Contents

1. [Authentication Flow](#authentication-flow)
2. [Token Format](#token-format)
3. [API Key Authentication](#api-key-authentication)
4. [Role-Based Access Control](#role-based-access-control)
5. [Subscription Tiers](#subscription-tiers)
6. [Rate Limiting](#rate-limiting)
7. [API Usage Examples](#api-usage-examples)
8. [Error Handling](#error-handling)
9. [Security Best Practices](#security-best-practices)

---

## Authentication Flow

### User Registration & Login

utxoIQ supports three authentication methods:

1. **Email/Password**: Traditional email-based authentication with email verification
2. **Google OAuth**: Sign in with Google account
3. **GitHub OAuth**: Sign in with GitHub account

#### Registration Flow

```
User → Frontend → Firebase Auth → JWT Token → Backend API
                                      ↓
                                 Create User Profile
                                      ↓
                                 Return User Data
```

**Steps:**

1. User submits credentials via frontend
2. Firebase Auth validates and creates user account
3. Firebase returns ID token (JWT)
4. Frontend sends token to backend `/api/v1/auth/profile` endpoint
5. Backend verifies token and creates user profile in database
6. User profile includes:
   - Firebase UID (unique identifier)
   - Email address
   - Display name (optional)
   - Role (default: "user")
   - Subscription tier (default: "free")

#### Login Flow

```
User → Frontend → Firebase Auth → JWT Token → Backend API
                                      ↓
                                 Verify Token
                                      ↓
                                 Update Last Login
                                      ↓
                                 Return User Data
```

**Steps:**

1. User provides credentials
2. Firebase Auth validates credentials
3. Firebase returns ID token (JWT)
4. Frontend includes token in `Authorization` header for all API requests
5. Backend validates token on each request
6. Backend updates `last_login_at` timestamp

### Token Refresh

Firebase ID tokens expire after 1 hour. The frontend automatically refreshes tokens before expiration:

- Tokens refresh every 50 minutes
- Refresh happens in the background
- No user interaction required
- Failed refresh redirects to login page

---

## Token Format

### JWT Structure

Firebase ID tokens are JSON Web Tokens (JWT) with the following structure:

```
Header.Payload.Signature
```

#### Header

```json
{
  "alg": "RS256",
  "kid": "key-id",
  "typ": "JWT"
}
```

#### Payload (Claims)

```json
{
  "iss": "https://securetoken.google.com/utxoiq-prod",
  "aud": "utxoiq-prod",
  "auth_time": 1704067200,
  "user_id": "abc123xyz",
  "sub": "abc123xyz",
  "iat": 1704067200,
  "exp": 1704070800,
  "email": "user@example.com",
  "email_verified": true,
  "firebase": {
    "identities": {
      "email": ["user@example.com"]
    },
    "sign_in_provider": "password"
  }
}
```

**Key Claims:**

- `user_id` / `sub`: Firebase UID (used to identify user in database)
- `email`: User's email address
- `email_verified`: Whether email has been verified
- `exp`: Token expiration timestamp (Unix time)
- `iat`: Token issued at timestamp (Unix time)

#### Signature

The signature is created using RS256 algorithm with Firebase's private key. Backend validates using Firebase's public keys.

### Using Tokens in API Requests

Include the token in the `Authorization` header with `Bearer` scheme:

```http
GET /api/v1/insights HTTP/1.1
Host: api.utxoiq.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...
```

### Token Validation

Backend validates tokens using Firebase Admin SDK:

1. **Signature verification**: Validates token signature using Firebase public keys
2. **Expiration check**: Ensures token hasn't expired
3. **Issuer validation**: Confirms token issued by Firebase
4. **Audience validation**: Verifies token intended for utxoIQ project

**Validation Performance:**

- Token validation: < 50ms
- Cached public keys for fast verification
- Automatic key rotation handled by Firebase

---

## API Key Authentication

API keys provide long-lived authentication for programmatic access without requiring user interaction.

### Creating API Keys

**Endpoint:** `POST /api/v1/auth/api-keys`

**Authentication:** Requires valid JWT token

**Request:**

```json
{
  "name": "Trading Bot API Key",
  "scopes": ["insights:read", "alerts:write"]
}
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "utxoiq_live_abc123xyz789...",
  "key_prefix": "utxoiq_l",
  "name": "Trading Bot API Key",
  "scopes": ["insights:read", "alerts:write"],
  "created_at": "2024-01-01T12:00:00Z",
  "last_used_at": null
}
```

**Important:** The full `key` value is only returned once during creation. Store it securely.

### API Key Format

```
utxoiq_live_<32-character-random-string>
```

- Prefix: `utxoiq_live_` (production) or `utxoiq_test_` (development)
- Random string: 32 characters (URL-safe base64)
- Total length: 43 characters

### Using API Keys

Include the API key in the `X-API-Key` header:

```http
GET /api/v1/insights HTTP/1.1
Host: api.utxoiq.com
X-API-Key: utxoiq_live_abc123xyz789...
```

### API Key Scopes

Scopes limit what an API key can access:

| Scope | Description | Endpoints |
|-------|-------------|-----------|
| `insights:read` | Read insights | `GET /api/v1/insights/*` |
| `insights:write` | Create insights | `POST /api/v1/insights/*` |
| `alerts:read` | Read alerts | `GET /api/v1/alerts/*` |
| `alerts:write` | Create/update alerts | `POST /api/v1/alerts/*`, `PATCH /api/v1/alerts/*` |
| `feedback:write` | Submit feedback | `POST /api/v1/feedback/*` |
| `monitoring:read` | Read monitoring data | `GET /api/v1/monitoring/*` |

**Example:** API key with `["insights:read", "alerts:write"]` can:
- ✅ Read insights
- ✅ Create and update alerts
- ❌ Submit feedback
- ❌ Read monitoring data

### Managing API Keys

#### List API Keys

**Endpoint:** `GET /api/v1/auth/api-keys`

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "key_prefix": "utxoiq_l",
    "name": "Trading Bot API Key",
    "scopes": ["insights:read", "alerts:write"],
    "created_at": "2024-01-01T12:00:00Z",
    "last_used_at": "2024-01-02T08:30:00Z"
  }
]
```

#### Revoke API Key

**Endpoint:** `DELETE /api/v1/auth/api-keys/{key_id}`

**Response:**

```json
{
  "message": "API key revoked"
}
```

Revoked keys are marked with `revoked_at` timestamp and immediately stop working.

### API Key Limits

- **Maximum keys per user:** 5 active keys
- **Key rotation:** Recommended every 90 days
- **Storage:** Keys are hashed with SHA256 before storage
- **Revocation:** Immediate (no grace period)

---

## Role-Based Access Control

### Roles

utxoIQ implements three user roles:

| Role | Description | Access Level |
|------|-------------|--------------|
| `user` | Standard user | Access to public endpoints and own data |
| `admin` | Administrator | Access to all endpoints including monitoring |
| `service` | Service account | Inter-service communication only |

### Role Assignment

- **Default role:** `user` (assigned on registration)
- **Admin assignment:** Only existing admins can assign admin role
- **Service accounts:** Created manually for backend services

### Protected Endpoints by Role

#### User Endpoints (role: `user`)

```
GET    /api/v1/auth/profile
PATCH  /api/v1/auth/profile
GET    /api/v1/auth/api-keys
POST   /api/v1/auth/api-keys
DELETE /api/v1/auth/api-keys/{key_id}
GET    /api/v1/insights
GET    /api/v1/insights/{id}
POST   /api/v1/alerts
GET    /api/v1/alerts
PATCH  /api/v1/alerts/{id}
DELETE /api/v1/alerts/{id}
POST   /api/v1/feedback
```

#### Admin Endpoints (role: `admin`)

```
GET    /api/v1/monitoring/status
GET    /api/v1/monitoring/backfill
GET    /api/v1/monitoring/signals
GET    /api/v1/monitoring/insights
POST   /api/v1/auth/users/{user_id}/role
POST   /api/v1/auth/users/{user_id}/subscription
```

### Authorization Flow

```
Request → Extract Token → Validate Token → Check Role → Allow/Deny
```

**Example:**

```python
# Require admin role
@router.get("/monitoring/status")
async def get_status(current_user: User = Depends(require_admin)):
    # Only admins can access this endpoint
    return {"status": "healthy"}
```

---

## Subscription Tiers

### Tier Levels

| Tier | Monthly Price | Features |
|------|---------------|----------|
| **Free** | $0 | Basic insight access, 100 requests/hour |
| **Pro** | $29 | AI chat, custom alerts, 1,000 requests/hour |
| **Power** | $99 | Advanced filtering, unlimited chat, 10,000 requests/hour |

### Tier Enforcement

Subscription tiers are enforced at the API level:

```
Request → Validate Auth → Check Subscription Tier → Allow/Deny
```

### Feature Access by Tier

#### Free Tier

```
✅ GET  /api/v1/insights (read-only)
✅ GET  /api/v1/insights/{id}
❌ POST /api/v1/chat (Pro+)
❌ POST /api/v1/alerts (Pro+)
```

#### Pro Tier

```
✅ All Free tier features
✅ POST /api/v1/chat
✅ POST /api/v1/alerts
✅ GET  /api/v1/alerts
❌ GET  /api/v1/insights?filter=advanced (Power only)
```

#### Power Tier

```
✅ All Pro tier features
✅ GET  /api/v1/insights?filter=advanced
✅ Unlimited chat queries
✅ Priority support
```

### Subscription Management

#### Check Current Tier

**Endpoint:** `GET /api/v1/auth/profile`

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "display_name": "John Doe",
  "role": "user",
  "subscription_tier": "pro",
  "created_at": "2024-01-01T12:00:00Z",
  "last_login_at": "2024-01-02T08:30:00Z"
}
```

#### Upgrade Subscription

Subscriptions are managed through Stripe. When a user upgrades:

1. User selects tier on `/pricing` page
2. Frontend redirects to Stripe Checkout
3. User completes payment
4. Stripe webhook notifies backend
5. Backend updates `subscription_tier` in database
6. User immediately gains access to new features

#### Downgrade/Cancel

When a subscription is canceled:

1. User cancels in Stripe Customer Portal
2. Stripe webhook notifies backend
3. Backend updates tier at end of billing period
4. User retains access until period ends
5. After period ends, tier downgrades to Free

---

## Rate Limiting

### Rate Limit Policies

Rate limits are enforced per user (or API key) based on subscription tier:

| Tier | Requests per Hour | Window |
|------|-------------------|--------|
| Free | 100 | Rolling 1-hour window |
| Pro | 1,000 | Rolling 1-hour window |
| Power | 10,000 | Rolling 1-hour window |

### Rate Limit Headers

Every API response includes rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1704070800
```

**Headers:**

- `X-RateLimit-Limit`: Maximum requests allowed in window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when window resets

### Rate Limit Exceeded

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704070800
Retry-After: 3600

{
  "detail": "Rate limit exceeded",
  "limit": 100,
  "reset_at": "2024-01-01T13:00:00Z"
}
```

### Rate Limit Implementation

Rate limits use Redis for fast, distributed counting:

```python
# Check rate limit
allowed, remaining = await rate_limiter.check_rate_limit(
    user_id=current_user.id,
    tier=current_user.subscription_tier
)

if not allowed:
    raise HTTPException(
        status_code=429,
        detail="Rate limit exceeded"
    )
```

### Exempt Endpoints

The following endpoints are exempt from rate limiting:

- `GET /health` - Health check
- `GET /` - Root endpoint
- `POST /api/v1/auth/profile` - Initial profile creation

---

## API Usage Examples

### Example 1: Authenticate and Fetch Insights

```bash
# 1. Get JWT token from Firebase (frontend handles this)
# Assume token is stored in $TOKEN variable

# 2. Fetch insights
curl -X GET "https://api.utxoiq.com/api/v1/insights" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**

```json
{
  "insights": [
    {
      "id": "insight-123",
      "category": "mempool",
      "headline": "Mempool fees spike to 50 sat/vB",
      "summary": "Transaction fees increased sharply...",
      "confidence": 0.87,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

### Example 2: Create API Key

```bash
# Create API key with specific scopes
curl -X POST "https://api.utxoiq.com/api/v1/auth/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Trading Bot",
    "scopes": ["insights:read", "alerts:write"]
  }'
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "utxoiq_live_abc123xyz789...",
  "key_prefix": "utxoiq_l",
  "name": "Trading Bot",
  "scopes": ["insights:read", "alerts:write"],
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Example 3: Use API Key

```bash
# Use API key instead of JWT token
curl -X GET "https://api.utxoiq.com/api/v1/insights" \
  -H "X-API-Key: utxoiq_live_abc123xyz789..." \
  -H "Content-Type: application/json"
```

### Example 4: Create Custom Alert (Pro Tier)

```bash
# Create alert for high mempool fees
curl -X POST "https://api.utxoiq.com/api/v1/alerts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metric": "mempool_fee_median",
    "threshold": 50,
    "condition": "greater_than",
    "channel": "email",
    "note": "Alert me when fees spike"
  }'
```

**Response:**

```json
{
  "id": "alert-456",
  "metric": "mempool_fee_median",
  "threshold": 50,
  "condition": "greater_than",
  "channel": "email",
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Example 5: Check Rate Limit Status

```bash
# Make any API request and check headers
curl -I "https://api.utxoiq.com/api/v1/insights" \
  -H "Authorization: Bearer $TOKEN"
```

**Response Headers:**

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1704070800
```

---

## Error Handling

### Authentication Errors

#### 401 Unauthorized

**Causes:**

- Missing `Authorization` header
- Invalid JWT token
- Expired JWT token
- Invalid API key
- Revoked API key

**Response:**

```json
{
  "detail": "Invalid authentication credentials",
  "error_code": "AUTH_INVALID_TOKEN"
}
```

**Resolution:**

- Refresh JWT token
- Check API key is correct
- Verify API key hasn't been revoked

#### 403 Forbidden

**Causes:**

- Insufficient role (e.g., user trying to access admin endpoint)
- Insufficient subscription tier (e.g., Free user trying to create alerts)
- API key missing required scope

**Response:**

```json
{
  "detail": "Requires Pro subscription or higher",
  "error_code": "AUTH_INSUFFICIENT_TIER",
  "required_tier": "pro",
  "current_tier": "free"
}
```

**Resolution:**

- Upgrade subscription tier
- Request admin role from administrator
- Create new API key with required scopes

#### 429 Too Many Requests

**Cause:** Rate limit exceeded

**Response:**

```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "limit": 100,
  "reset_at": "2024-01-01T13:00:00Z"
}
```

**Resolution:**

- Wait until rate limit window resets
- Upgrade to higher subscription tier
- Implement request throttling in your application

### Error Response Format

All authentication errors follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "additional_field": "context-specific data"
}
```

---

## Security Best Practices

### For Users

1. **Never share JWT tokens or API keys**
   - Tokens grant full access to your account
   - API keys should be treated like passwords

2. **Use API keys for programmatic access**
   - Don't use JWT tokens in server-side applications
   - API keys can be scoped and revoked independently

3. **Rotate API keys regularly**
   - Recommended: Every 90 days
   - Immediately revoke compromised keys

4. **Use minimum required scopes**
   - Only grant scopes your application needs
   - Create separate keys for different applications

5. **Monitor API key usage**
   - Check `last_used_at` timestamp regularly
   - Revoke unused keys

6. **Enable email verification**
   - Verify your email address after registration
   - Prevents account takeover

7. **Use strong passwords**
   - Minimum 12 characters
   - Mix of letters, numbers, symbols
   - Don't reuse passwords

### For Developers

1. **Store tokens securely**
   - Never commit tokens to version control
   - Use environment variables or secret managers
   - Don't log tokens in application logs

2. **Implement token refresh**
   - Refresh tokens before expiration
   - Handle refresh failures gracefully
   - Redirect to login on auth failure

3. **Handle rate limits**
   - Check `X-RateLimit-Remaining` header
   - Implement exponential backoff
   - Cache responses when possible

4. **Validate on server-side**
   - Never trust client-side validation alone
   - Always validate tokens on backend
   - Check subscription tier for protected features

5. **Use HTTPS only**
   - Never send tokens over HTTP
   - Validate SSL certificates
   - Use certificate pinning for mobile apps

6. **Implement proper error handling**
   - Don't expose sensitive error details
   - Log authentication failures
   - Monitor for suspicious patterns

7. **Follow principle of least privilege**
   - Request minimum required scopes
   - Use service accounts for backend services
   - Separate production and development keys

### For Administrators

1. **Monitor authentication logs**
   - Review failed login attempts
   - Check for unusual access patterns
   - Set up alerts for suspicious activity

2. **Implement IP allowlisting**
   - Restrict admin access to known IPs
   - Use VPN for remote access
   - Monitor for unauthorized access attempts

3. **Regular security audits**
   - Review user roles and permissions
   - Audit API key usage
   - Check for inactive accounts

4. **Enforce password policies**
   - Require strong passwords
   - Implement password expiration
   - Prevent password reuse

5. **Enable multi-factor authentication**
   - Require MFA for admin accounts
   - Use hardware security keys when possible
   - Backup recovery codes securely

---

## Support

### Documentation

- [API Reference](./database-api-documentation.md)
- [Integration Guide](./INTEGRATION_README.md)
- [Quick Start](./quick-start.md)

### Contact

- **Email:** support@utxoiq.com
- **GitHub Issues:** https://github.com/utxoiq/utxoiq/issues
- **Discord:** https://discord.gg/utxoiq

### Rate Limit Increase Requests

If you need higher rate limits:

1. Email support@utxoiq.com with:
   - Your use case
   - Expected request volume
   - Current subscription tier
2. We'll review and respond within 2 business days

---

**Last Updated:** January 2024  
**Version:** 1.0.0
