# Role-Based Access Control (RBAC) Implementation

## Overview

This document describes the implementation of role-based access control (RBAC) and authorization features for the utxoIQ web API service.

## Components Implemented

### 1. Authorization Decorators

Located in `src/middleware/auth.py`:

#### `require_role(required_role: Role)`
- Enforces role-based access control for endpoints
- Supports three roles: USER, ADMIN, SERVICE
- Returns 403 Forbidden if user doesn't have required role
- Logs all authorization failures

**Usage Example:**
```python
from src.middleware.auth import require_role
from src.models.auth import Role

@router.get("/admin/users")
async def list_users(user: User = Depends(require_role(Role.ADMIN))):
    # Only admin users can access this endpoint
    pass
```

#### `require_subscription(min_tier: UserSubscriptionTier)`
- Enforces subscription tier requirements for tiered features
- Supports tier hierarchy: FREE < PRO < POWER < WHITE_LABEL
- Returns 403 Forbidden if user's tier is insufficient
- Logs all authorization failures

**Usage Example:**
```python
from src.middleware.auth import require_subscription
from src.models.auth import UserSubscriptionTier

@router.post("/chat")
async def ai_chat(
    query: str,
    user: User = Depends(require_subscription(UserSubscriptionTier.PRO))
):
    # Only Pro and Power tier users can access AI chat
    pass
```

#### `require_scope(required_scope: str)`
- Enforces scope-based access control for API keys
- Validates API key has required scope (e.g., 'insights:read', 'alerts:write')
- Returns 401 Unauthorized if no API key provided
- Returns 403 Forbidden if API key lacks required scope
- Logs all scope validation failures

**Usage Example:**
```python
from src.middleware.auth import require_scope

@router.post("/alerts")
async def create_alert(
    alert: AlertCreate,
    user: User = Depends(require_scope("alerts:write"))
):
    # Only API keys with 'alerts:write' scope can access
    pass
```

### 2. Audit Logging Service

Located in `src/services/audit_service.py`:

The `AuditService` provides structured logging for security and compliance events:

#### Methods:
- `log_authorization_failure()` - Logs failed authorization attempts
- `log_role_change()` - Logs user role changes
- `log_subscription_tier_change()` - Logs subscription tier changes
- `log_api_key_scope_failure()` - Logs API key scope validation failures

All audit logs include:
- User identification (ID, email)
- Timestamp (ISO 8601 format)
- Event details (old/new values, reasons)
- Structured data for easy querying

### 3. Enhanced User Service

Located in `src/services/user_service.py`:

Updated methods to include audit logging:

#### `update_user_role()`
- Updates user role (user, admin, service)
- Logs role changes with audit trail
- Accepts optional `changed_by` parameter for tracking who made the change

#### `update_subscription_tier()`
- Updates user subscription tier
- Logs tier changes with reason (e.g., 'stripe_payment', 'admin_override')
- Accepts optional `changed_by` parameter for manual changes

## Testing

Comprehensive test suite in `tests/test_authorization.py`:

### Test Coverage:
- ✅ Role-based access control (admin, service roles)
- ✅ Subscription tier restrictions (free, pro, power)
- ✅ API key scope validation
- ✅ Authorization failure logging
- ✅ Role change logging
- ✅ Subscription tier change logging

**Test Results:** 16/16 tests passing

## Usage Patterns

### Protecting Admin Endpoints
```python
@router.post("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    admin: User = Depends(require_role(Role.ADMIN))
):
    # Only admins can change user roles
    pass
```

### Tiered Feature Access
```python
@router.get("/insights/advanced")
async def get_advanced_insights(
    user: User = Depends(require_subscription(UserSubscriptionTier.POWER))
):
    # Only Power tier users can access advanced insights
    pass
```

### API Key Scopes
```python
@router.get("/insights")
async def list_insights(
    user: User = Depends(require_scope("insights:read"))
):
    # API key must have 'insights:read' scope
    pass

@router.post("/insights/{id}/feedback")
async def submit_feedback(
    id: str,
    feedback: FeedbackCreate,
    user: User = Depends(require_scope("insights:write"))
):
    # API key must have 'insights:write' scope
    pass
```

### Combining Multiple Requirements
```python
from fastapi import Depends

# First check authentication, then role, then subscription
@router.get("/admin/analytics")
async def admin_analytics(
    user: User = Depends(require_role(Role.ADMIN)),
    _: User = Depends(require_subscription(UserSubscriptionTier.PRO))
):
    # Must be admin AND have Pro subscription
    pass
```

## Security Considerations

1. **Audit Logging**: All authorization failures are logged with user identity for security monitoring
2. **Structured Logs**: Logs use structured format for easy querying in Cloud Logging
3. **403 vs 401**: 
   - 401 Unauthorized: Missing or invalid authentication
   - 403 Forbidden: Authenticated but insufficient permissions
4. **Scope Validation**: API keys are validated against specific scopes for fine-grained access control
5. **Tier Hierarchy**: Subscription tiers follow strict hierarchy (higher tiers include lower tier permissions)

## Future Enhancements

- [ ] Add permission groups for more complex authorization scenarios
- [ ] Implement time-based access restrictions
- [ ] Add IP-based access controls for sensitive endpoints
- [ ] Create admin UI for managing user roles and permissions
- [ ] Add audit log retention policies and archival
