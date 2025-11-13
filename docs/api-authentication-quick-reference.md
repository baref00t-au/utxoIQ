# API Authentication Quick Reference

## Quick Start

### 1. Get JWT Token (Frontend)

```javascript
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';

const auth = getAuth();
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const token = await userCredential.user.getIdToken();
```

### 2. Make Authenticated Request

```bash
curl -X GET "https://api.utxoiq.com/api/v1/insights" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Create API Key (for programmatic access)

```bash
curl -X POST "https://api.utxoiq.com/api/v1/auth/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "scopes": ["insights:read"]}'
```

### 4. Use API Key

```bash
curl -X GET "https://api.utxoiq.com/api/v1/insights" \
  -H "X-API-Key: utxoiq_live_abc123..."
```

---

## Authentication Methods

| Method | Header | Use Case | Expiration |
|--------|--------|----------|------------|
| JWT Token | `Authorization: Bearer <token>` | User sessions | 1 hour |
| API Key | `X-API-Key: <key>` | Programmatic access | Never (until revoked) |

---

## Common Endpoints

### Authentication

```bash
# Get user profile
GET /api/v1/auth/profile
Authorization: Bearer <token>

# Update profile
PATCH /api/v1/auth/profile
Authorization: Bearer <token>
Content-Type: application/json
{"display_name": "New Name"}

# Create API key
POST /api/v1/auth/api-keys
Authorization: Bearer <token>
Content-Type: application/json
{"name": "Key Name", "scopes": ["insights:read"]}

# List API keys
GET /api/v1/auth/api-keys
Authorization: Bearer <token>

# Revoke API key
DELETE /api/v1/auth/api-keys/{key_id}
Authorization: Bearer <token>
```

### Insights

```bash
# List insights
GET /api/v1/insights
Authorization: Bearer <token>

# Get specific insight
GET /api/v1/insights/{id}
Authorization: Bearer <token>
```

### Alerts (Pro+ only)

```bash
# Create alert
POST /api/v1/alerts
Authorization: Bearer <token>
Content-Type: application/json
{
  "metric": "mempool_fee_median",
  "threshold": 50,
  "condition": "greater_than",
  "channel": "email"
}

# List alerts
GET /api/v1/alerts
Authorization: Bearer <token>

# Update alert
PATCH /api/v1/alerts/{id}
Authorization: Bearer <token>
Content-Type: application/json
{"status": "paused"}

# Delete alert
DELETE /api/v1/alerts/{id}
Authorization: Bearer <token>
```

---

## API Key Scopes

| Scope | Permissions |
|-------|-------------|
| `insights:read` | Read insights |
| `insights:write` | Create insights (admin only) |
| `alerts:read` | Read alerts |
| `alerts:write` | Create/update alerts |
| `feedback:write` | Submit feedback |
| `monitoring:read` | Read monitoring data (admin only) |

---

## Rate Limits

| Tier | Requests/Hour | Cost |
|------|---------------|------|
| Free | 100 | $0 |
| Pro | 1,000 | $29/mo |
| Power | 10,000 | $99/mo |

**Check rate limit status:**

```bash
curl -I "https://api.utxoiq.com/api/v1/insights" \
  -H "Authorization: Bearer <token>"

# Response headers:
# X-RateLimit-Limit: 1000
# X-RateLimit-Remaining: 847
# X-RateLimit-Reset: 1704070800
```

---

## Error Codes

| Status | Error Code | Meaning | Solution |
|--------|------------|---------|----------|
| 401 | `AUTH_INVALID_TOKEN` | Invalid/expired token | Refresh token |
| 401 | `AUTH_INVALID_API_KEY` | Invalid API key | Check key value |
| 403 | `AUTH_INSUFFICIENT_ROLE` | Missing required role | Contact admin |
| 403 | `AUTH_INSUFFICIENT_TIER` | Subscription tier too low | Upgrade plan |
| 403 | `AUTH_INSUFFICIENT_SCOPE` | API key missing scope | Create new key |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests | Wait or upgrade |

---

## Code Examples

### Python

```python
import requests

# Using JWT token
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
response = requests.get("https://api.utxoiq.com/api/v1/insights", headers=headers)

# Using API key
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}
response = requests.get("https://api.utxoiq.com/api/v1/insights", headers=headers)
```

### JavaScript/TypeScript

```typescript
// Using JWT token
const response = await fetch('https://api.utxoiq.com/api/v1/insights', {
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  }
});

// Using API key
const response = await fetch('https://api.utxoiq.com/api/v1/insights', {
  headers: {
    'X-API-Key': apiKey,
    'Content-Type': 'application/json'
  }
});
```

### cURL

```bash
# JWT token
curl -X GET "https://api.utxoiq.com/api/v1/insights" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# API key
curl -X GET "https://api.utxoiq.com/api/v1/insights" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

---

## Security Checklist

- [ ] Never commit tokens/keys to version control
- [ ] Use environment variables for secrets
- [ ] Rotate API keys every 90 days
- [ ] Use minimum required scopes
- [ ] Monitor API key usage
- [ ] Revoke unused keys
- [ ] Use HTTPS only
- [ ] Implement token refresh logic
- [ ] Handle rate limits gracefully
- [ ] Log authentication failures

---

## Support

- **Full Documentation:** [Authentication Guide](./authentication-guide.md)
- **API Reference:** [API Documentation](./database-api-documentation.md)
- **Email:** support@utxoiq.com
- **GitHub:** https://github.com/utxoiq/utxoiq/issues

---

**Last Updated:** January 2024
