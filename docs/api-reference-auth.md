# API Reference - Authentication Endpoints

## Base URL

```
Production: https://api.utxoiq.com
Development: http://localhost:8000
```

## Authentication

All endpoints require authentication unless marked as public. Include credentials in request headers:

**JWT Token:**
```
Authorization: Bearer <jwt_token>
```

**API Key:**
```
X-API-Key: <api_key>
```

---

## User Profile Endpoints

### Get Current User Profile

Retrieve the authenticated user's profile information.

**Endpoint:** `GET /api/v1/auth/profile`

**Authentication:** Required (JWT or API Key)

**Request:**

```bash
curl -X GET "https://api.utxoiq.com/api/v1/auth/profile" \
  -H "Authorization: Bearer <token>"
```

**Response:** `200 OK`

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

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique user identifier |
| `email` | string | User's email address |
| `display_name` | string | User's display name (nullable) |
| `role` | string | User role: `user`, `admin`, or `service` |
| `subscription_tier` | string | Subscription tier: `free`, `pro`, or `power` |
| `created_at` | datetime | Account creation timestamp |
| `last_login_at` | datetime | Last login timestamp (nullable) |

**Errors:**

- `401 Unauthorized` - Invalid or missing authentication
- `500 Internal Server Error` - Server error

---

### Update User Profile

Update the authenticated user's profile information.

**Endpoint:** `PATCH /api/v1/auth/profile`

**Authentication:** Required (JWT only)

**Request:**

```bash
curl -X PATCH "https://api.utxoiq.com/api/v1/auth/profile" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Jane Smith"
  }'
```

**Request Body:**

```json
{
  "display_name": "Jane Smith"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `display_name` | string | No | User's display name (max 100 chars) |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "display_name": "Jane Smith",
  "role": "user",
  "subscription_tier": "pro",
  "created_at": "2024-01-01T12:00:00Z",
  "last_login_at": "2024-01-02T08:30:00Z"
}
```

**Errors:**

- `401 Unauthorized` - Invalid or missing authentication
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## API Key Management Endpoints

### Create API Key

Create a new API key for programmatic access.

**Endpoint:** `POST /api/v1/auth/api-keys`

**Authentication:** Required (JWT only)

**Limits:** Maximum 5 active API keys per user

**Request:**

```bash
curl -X POST "https://api.utxoiq.com/api/v1/auth/api-keys" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Trading Bot API Key",
    "scopes": ["insights:read", "alerts:write"]
  }'
```

**Request Body:**

```json
{
  "name": "Trading Bot API Key",
  "scopes": ["insights:read", "alerts:write"]
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Descriptive name for the API key (max 100 chars) |
| `scopes` | array | No | Array of scope strings (default: empty array) |

**Available Scopes:**

- `insights:read` - Read insights
- `insights:write` - Create insights (admin only)
- `alerts:read` - Read alerts
- `alerts:write` - Create/update alerts
- `feedback:write` - Submit feedback
- `monitoring:read` - Read monitoring data (admin only)

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "utxoiq_live_abc123xyz789defghijklmnopqrstuv",
  "key_prefix": "utxoiq_l",
  "name": "Trading Bot API Key",
  "scopes": ["insights:read", "alerts:write"],
  "created_at": "2024-01-01T12:00:00Z",
  "last_used_at": null
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique API key identifier |
| `key` | string | Full API key (only returned on creation) |
| `key_prefix` | string | First 8 characters of key for identification |
| `name` | string | API key name |
| `scopes` | array | Array of granted scopes |
| `created_at` | datetime | Creation timestamp |
| `last_used_at` | datetime | Last usage timestamp (nullable) |

**Important:** The `key` field is only returned once during creation. Store it securely.

**Errors:**

- `400 Bad Request` - Maximum 5 API keys limit reached
- `401 Unauthorized` - Invalid or missing authentication
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

### List API Keys

List all API keys for the authenticated user.

**Endpoint:** `GET /api/v1/auth/api-keys`

**Authentication:** Required (JWT only)

**Request:**

```bash
curl -X GET "https://api.utxoiq.com/api/v1/auth/api-keys" \
  -H "Authorization: Bearer <token>"
```

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "key_prefix": "utxoiq_l",
    "name": "Trading Bot API Key",
    "scopes": ["insights:read", "alerts:write"],
    "created_at": "2024-01-01T12:00:00Z",
    "last_used_at": "2024-01-02T08:30:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "key_prefix": "utxoiq_l",
    "name": "Analytics Script",
    "scopes": ["insights:read"],
    "created_at": "2024-01-05T10:00:00Z",
    "last_used_at": null
  }
]
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique API key identifier |
| `key_prefix` | string | First 8 characters for identification |
| `name` | string | API key name |
| `scopes` | array | Array of granted scopes |
| `created_at` | datetime | Creation timestamp |
| `last_used_at` | datetime | Last usage timestamp (nullable) |

**Note:** The full `key` value is never returned after creation.

**Errors:**

- `401 Unauthorized` - Invalid or missing authentication
- `500 Internal Server Error` - Server error

---

### Revoke API Key

Revoke an API key immediately. Revoked keys cannot be restored.

**Endpoint:** `DELETE /api/v1/auth/api-keys/{key_id}`

**Authentication:** Required (JWT only)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `key_id` | UUID | API key identifier |

**Request:**

```bash
curl -X DELETE "https://api.utxoiq.com/api/v1/auth/api-keys/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>"
```

**Response:** `200 OK`

```json
{
  "message": "API key revoked"
}
```

**Errors:**

- `401 Unauthorized` - Invalid or missing authentication
- `404 Not Found` - API key not found or doesn't belong to user
- `500 Internal Server Error` - Server error

---

## Admin Endpoints

### Update User Role

Update a user's role. Admin access required.

**Endpoint:** `POST /api/v1/auth/users/{user_id}/role`

**Authentication:** Required (JWT only, admin role)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | User identifier |

**Request:**

```bash
curl -X POST "https://api.utxoiq.com/api/v1/auth/users/550e8400-e29b-41d4-a716-446655440000/role" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin"
  }'
```

**Request Body:**

```json
{
  "role": "admin"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | Yes | New role: `user`, `admin`, or `service` |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "display_name": "John Doe",
  "role": "admin",
  "subscription_tier": "pro",
  "created_at": "2024-01-01T12:00:00Z",
  "last_login_at": "2024-01-02T08:30:00Z"
}
```

**Errors:**

- `401 Unauthorized` - Invalid or missing authentication
- `403 Forbidden` - Insufficient permissions (not admin)
- `404 Not Found` - User not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

### Update User Subscription Tier

Update a user's subscription tier. Admin access required.

**Endpoint:** `POST /api/v1/auth/users/{user_id}/subscription`

**Authentication:** Required (JWT only, admin role)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | User identifier |

**Request:**

```bash
curl -X POST "https://api.utxoiq.com/api/v1/auth/users/550e8400-e29b-41d4-a716-446655440000/subscription" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_tier": "power"
  }'
```

**Request Body:**

```json
{
  "subscription_tier": "power"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subscription_tier` | string | Yes | New tier: `free`, `pro`, or `power` |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "display_name": "John Doe",
  "role": "user",
  "subscription_tier": "power",
  "created_at": "2024-01-01T12:00:00Z",
  "last_login_at": "2024-01-02T08:30:00Z"
}
```

**Note:** In production, subscription tiers are typically updated via Stripe webhooks, not manually.

**Errors:**

- `401 Unauthorized` - Invalid or missing authentication
- `403 Forbidden` - Insufficient permissions (not admin)
- `404 Not Found` - User not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Rate Limiting

All authenticated endpoints are subject to rate limiting based on subscription tier:

| Tier | Requests per Hour |
|------|-------------------|
| Free | 100 |
| Pro | 1,000 |
| Power | 10,000 |

### Rate Limit Headers

Every response includes rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1704070800
```

### Rate Limit Exceeded

When rate limit is exceeded, the API returns:

**Response:** `429 Too Many Requests`

```json
{
  "detail": "Rate limit exceeded",
  "limit": 100,
  "reset_at": "2024-01-01T13:00:00Z"
}
```

**Headers:**

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704070800
Retry-After: 3600
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE"
}
```

### Common Error Codes

| Status | Error Code | Description |
|--------|------------|-------------|
| 401 | `AUTH_INVALID_TOKEN` | Invalid or expired JWT token |
| 401 | `AUTH_INVALID_API_KEY` | Invalid or revoked API key |
| 403 | `AUTH_INSUFFICIENT_ROLE` | User lacks required role |
| 403 | `AUTH_INSUFFICIENT_TIER` | Subscription tier too low |
| 403 | `AUTH_INSUFFICIENT_SCOPE` | API key missing required scope |
| 429 | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 500 | `INTERNAL_ERROR` | Internal server error |

---

## Examples

### Complete Authentication Flow

```python
import requests

# 1. User logs in via Firebase (frontend)
# Assume we have jwt_token from Firebase

# 2. Get user profile
response = requests.get(
    "https://api.utxoiq.com/api/v1/auth/profile",
    headers={"Authorization": f"Bearer {jwt_token}"}
)
user = response.json()
print(f"User: {user['email']}, Tier: {user['subscription_tier']}")

# 3. Create API key for programmatic access
response = requests.post(
    "https://api.utxoiq.com/api/v1/auth/api-keys",
    headers={
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    },
    json={
        "name": "My Bot",
        "scopes": ["insights:read", "alerts:write"]
    }
)
api_key_data = response.json()
api_key = api_key_data["key"]
print(f"API Key created: {api_key_data['key_prefix']}...")

# 4. Use API key for subsequent requests
response = requests.get(
    "https://api.utxoiq.com/api/v1/insights",
    headers={"X-API-Key": api_key}
)
insights = response.json()
print(f"Fetched {len(insights)} insights")

# 5. Check rate limit status
print(f"Rate limit remaining: {response.headers['X-RateLimit-Remaining']}")
```

---

## See Also

- [Authentication Guide](./authentication-guide.md) - Comprehensive authentication documentation
- [Quick Reference](./api-authentication-quick-reference.md) - Quick reference for common tasks
- [API Documentation](./database-api-documentation.md) - Full API reference

---

**Last Updated:** January 2024  
**Version:** 1.0.0
