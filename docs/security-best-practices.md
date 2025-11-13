# Security Best Practices

## Overview

This document outlines security best practices for developers, users, and administrators working with the utxoIQ authentication system.

---

## For Application Developers

### Token Management

#### ✅ DO

- **Store tokens securely**
  ```javascript
  // Use secure storage mechanisms
  // Browser: httpOnly cookies or secure localStorage
  // Mobile: Keychain (iOS) or Keystore (Android)
  // Server: Environment variables or secret managers
  ```

- **Implement token refresh**
  ```javascript
  // Refresh tokens before expiration
  useEffect(() => {
    const interval = setInterval(async () => {
      if (user) {
        await user.getIdToken(true); // Force refresh
      }
    }, 50 * 60 * 1000); // Every 50 minutes
    
    return () => clearInterval(interval);
  }, [user]);
  ```

- **Handle authentication errors gracefully**
  ```javascript
  try {
    const response = await fetch('/api/v1/insights', {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    if (response.status === 401) {
      // Token expired or invalid
      await refreshToken();
      // Retry request
    }
  } catch (error) {
    // Handle error
  }
  ```

#### ❌ DON'T

- **Never commit tokens to version control**
  ```bash
  # Add to .gitignore
  .env
  .env.local
  *.key
  *.pem
  secrets/
  ```

- **Never log tokens**
  ```javascript
  // BAD
  console.log('Token:', token);
  logger.info(`User token: ${token}`);
  
  // GOOD
  console.log('Token received');
  logger.info('User authenticated', { userId: user.id });
  ```

- **Never send tokens over HTTP**
  ```javascript
  // BAD
  fetch('http://api.utxoiq.com/insights', { ... });
  
  // GOOD
  fetch('https://api.utxoiq.com/insights', { ... });
  ```

### API Key Management

#### ✅ DO

- **Use environment variables**
  ```bash
  # .env
  UTXOIQ_API_KEY=utxoiq_live_abc123...
  ```
  
  ```javascript
  const apiKey = process.env.UTXOIQ_API_KEY;
  ```

- **Use minimum required scopes**
  ```javascript
  // Only request scopes you need
  const apiKey = await createApiKey({
    name: 'Read-only Bot',
    scopes: ['insights:read'] // Not ['insights:read', 'insights:write']
  });
  ```

- **Rotate keys regularly**
  ```javascript
  // Implement key rotation every 90 days
  const keyAge = Date.now() - apiKey.created_at;
  const ninetyDays = 90 * 24 * 60 * 60 * 1000;
  
  if (keyAge > ninetyDays) {
    console.warn('API key is older than 90 days. Consider rotating.');
  }
  ```

- **Monitor key usage**
  ```javascript
  // Check last_used_at regularly
  const keys = await listApiKeys();
  const unusedKeys = keys.filter(key => {
    const daysSinceUse = (Date.now() - key.last_used_at) / (24 * 60 * 60 * 1000);
    return daysSinceUse > 30;
  });
  
  // Revoke unused keys
  for (const key of unusedKeys) {
    await revokeApiKey(key.id);
  }
  ```

#### ❌ DON'T

- **Never hardcode API keys**
  ```javascript
  // BAD
  const apiKey = 'utxoiq_live_abc123...';
  
  // GOOD
  const apiKey = process.env.UTXOIQ_API_KEY;
  ```

- **Never share keys between applications**
  ```javascript
  // BAD - One key for multiple apps
  const sharedKey = 'utxoiq_live_shared...';
  
  // GOOD - Separate keys per application
  const tradingBotKey = process.env.TRADING_BOT_API_KEY;
  const analyticsKey = process.env.ANALYTICS_API_KEY;
  ```

### Rate Limiting

#### ✅ DO

- **Check rate limit headers**
  ```javascript
  const response = await fetch('/api/v1/insights', {
    headers: { Authorization: `Bearer ${token}` }
  });
  
  const remaining = parseInt(response.headers.get('X-RateLimit-Remaining'));
  const reset = parseInt(response.headers.get('X-RateLimit-Reset'));
  
  if (remaining < 10) {
    console.warn('Approaching rate limit');
  }
  ```

- **Implement exponential backoff**
  ```javascript
  async function fetchWithRetry(url, options, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(url, options);
        
        if (response.status === 429) {
          const retryAfter = parseInt(response.headers.get('Retry-After'));
          const delay = Math.min(1000 * Math.pow(2, i), retryAfter * 1000);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        
        return response;
      } catch (error) {
        if (i === maxRetries - 1) throw error;
      }
    }
  }
  ```

- **Cache responses**
  ```javascript
  // Use TanStack Query or similar
  const { data } = useQuery({
    queryKey: ['insights'],
    queryFn: fetchInsights,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000 // 10 minutes
  });
  ```

#### ❌ DON'T

- **Never ignore rate limit errors**
  ```javascript
  // BAD
  try {
    await fetch('/api/v1/insights');
  } catch (error) {
    // Silently fail
  }
  
  // GOOD
  try {
    const response = await fetch('/api/v1/insights');
    if (response.status === 429) {
      const resetTime = response.headers.get('X-RateLimit-Reset');
      throw new Error(`Rate limit exceeded. Resets at ${resetTime}`);
    }
  } catch (error) {
    console.error('API error:', error);
    // Handle appropriately
  }
  ```

### Input Validation

#### ✅ DO

- **Validate on both client and server**
  ```typescript
  // Client-side validation (UX)
  const schema = z.object({
    name: z.string().min(1).max(100),
    scopes: z.array(z.string())
  });
  
  // Server always validates too
  ```

- **Sanitize user input**
  ```javascript
  // Prevent XSS
  const sanitizedName = DOMPurify.sanitize(userInput);
  ```

- **Use parameterized queries**
  ```python
  # GOOD - Parameterized query
  cursor.execute(
    "SELECT * FROM users WHERE email = %s",
    (email,)
  )
  
  # BAD - String concatenation (SQL injection risk)
  cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
  ```

### HTTPS/TLS

#### ✅ DO

- **Always use HTTPS**
  ```javascript
  // Enforce HTTPS in production
  if (process.env.NODE_ENV === 'production' && !req.secure) {
    return res.redirect(`https://${req.headers.host}${req.url}`);
  }
  ```

- **Validate SSL certificates**
  ```javascript
  // Don't disable certificate validation
  const agent = new https.Agent({
    rejectUnauthorized: true // Keep this true
  });
  ```

- **Use certificate pinning (mobile apps)**
  ```swift
  // iOS example
  let serverTrustPolicy = ServerTrustPolicy.pinCertificates(
    certificates: ServerTrustPolicy.certificates(),
    validateCertificateChain: true,
    validateHost: true
  )
  ```

---

## For End Users

### Account Security

#### ✅ DO

- **Use strong passwords**
  - Minimum 12 characters
  - Mix of uppercase, lowercase, numbers, symbols
  - Use a password manager
  - Don't reuse passwords

- **Enable email verification**
  - Verify your email after registration
  - Prevents account takeover

- **Monitor account activity**
  - Check `last_login_at` regularly
  - Review API key usage
  - Report suspicious activity

- **Use OAuth when possible**
  - Google or GitHub sign-in
  - Reduces password management burden
  - Leverages provider's security

#### ❌ DON'T

- **Never share credentials**
  - Don't share passwords
  - Don't share JWT tokens
  - Don't share API keys

- **Never use public computers**
  - Avoid logging in on shared devices
  - If necessary, always log out
  - Clear browser data after use

### API Key Security

#### ✅ DO

- **Create separate keys per use case**
  ```
  Trading Bot Key: insights:read, alerts:write
  Analytics Script: insights:read
  Monitoring Tool: monitoring:read
  ```

- **Revoke unused keys**
  - Review keys monthly
  - Revoke keys you no longer use
  - Revoke keys for decommissioned apps

- **Rotate keys regularly**
  - Every 90 days recommended
  - Immediately after suspected compromise
  - After team member departure

#### ❌ DON'T

- **Never share API keys**
  - Each user should have their own keys
  - Don't email or message keys
  - Don't post keys in public forums

- **Never commit keys to repositories**
  - Check before committing
  - Use `.gitignore`
  - Revoke if accidentally committed

---

## For Administrators

### User Management

#### ✅ DO

- **Monitor authentication logs**
  ```python
  # Review failed login attempts
  failed_logins = get_failed_logins(last_24_hours=True)
  
  # Alert on suspicious patterns
  if len(failed_logins) > 10:
    send_alert('Multiple failed login attempts detected')
  ```

- **Implement IP allowlisting for admins**
  ```python
  ADMIN_ALLOWED_IPS = [
    '203.0.113.0/24',  # Office network
    '198.51.100.0/24'  # VPN network
  ]
  
  @router.get('/admin/dashboard')
  async def admin_dashboard(request: Request):
    if request.client.host not in ADMIN_ALLOWED_IPS:
      raise HTTPException(403, 'Access denied')
  ```

- **Regular security audits**
  - Review user roles quarterly
  - Audit API key usage monthly
  - Check for inactive accounts
  - Review access logs

- **Enforce strong password policies**
  ```python
  PASSWORD_MIN_LENGTH = 12
  PASSWORD_REQUIRE_UPPERCASE = True
  PASSWORD_REQUIRE_LOWERCASE = True
  PASSWORD_REQUIRE_NUMBERS = True
  PASSWORD_REQUIRE_SYMBOLS = True
  ```

#### ❌ DON'T

- **Never use shared admin accounts**
  - Each admin should have their own account
  - Enables proper audit trails
  - Allows granular access control

- **Never disable security features**
  - Keep rate limiting enabled
  - Keep authentication required
  - Keep audit logging enabled

### Incident Response

#### ✅ DO

- **Have an incident response plan**
  ```markdown
  1. Detect: Monitor logs for anomalies
  2. Contain: Revoke compromised credentials
  3. Investigate: Review audit logs
  4. Remediate: Fix vulnerabilities
  5. Document: Record incident details
  6. Notify: Inform affected users
  ```

- **Revoke compromised credentials immediately**
  ```python
  # Revoke all user's API keys
  async def revoke_all_user_keys(user_id: UUID):
    keys = await get_user_api_keys(user_id)
    for key in keys:
      await revoke_api_key(key.id)
    
    # Force token refresh
    await firebase_admin.auth.revoke_refresh_tokens(user.firebase_uid)
  ```

- **Notify affected users**
  ```python
  # Send security notification
  await send_email(
    to=user.email,
    subject='Security Alert: Unusual Activity Detected',
    body='We detected unusual activity on your account...'
  )
  ```

### Monitoring & Alerting

#### ✅ DO

- **Set up security alerts**
  ```python
  # Alert on multiple failed logins
  if failed_login_count > 5:
    send_alert('Possible brute force attack')
  
  # Alert on admin role changes
  if role_changed_to_admin:
    send_alert('Admin role granted to user')
  
  # Alert on unusual API usage
  if request_count > normal_threshold * 2:
    send_alert('Unusual API usage detected')
  ```

- **Monitor for anomalies**
  ```python
  # Detect unusual access patterns
  user_locations = get_user_login_locations(user_id)
  if len(user_locations) > 3:  # Multiple countries
    flag_for_review(user_id)
  ```

- **Regular log reviews**
  - Review authentication logs daily
  - Review authorization failures weekly
  - Review API key usage monthly

---

## Security Checklist

### Development

- [ ] Tokens stored securely (not in code)
- [ ] Environment variables used for secrets
- [ ] HTTPS enforced in production
- [ ] Input validation on client and server
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (input sanitization)
- [ ] CSRF protection enabled
- [ ] Rate limiting implemented
- [ ] Error messages don't leak sensitive info
- [ ] Security headers configured

### Deployment

- [ ] SSL/TLS certificates valid
- [ ] Secrets in Secret Manager (not env files)
- [ ] Database connections encrypted
- [ ] API keys rotated regularly
- [ ] Backup encryption enabled
- [ ] Audit logging enabled
- [ ] Monitoring and alerting configured
- [ ] Incident response plan documented
- [ ] Security contact information published

### Operations

- [ ] Regular security audits scheduled
- [ ] User access reviewed quarterly
- [ ] API key usage monitored
- [ ] Failed login attempts tracked
- [ ] Unusual activity alerts configured
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
- [ ] Security training completed

---

## Compliance

### GDPR

- User data encrypted at rest and in transit
- Right to access: Users can export their data
- Right to deletion: Users can delete their accounts
- Data retention policies enforced
- Privacy policy published

### SOC 2

- Access controls implemented
- Audit logging enabled
- Encryption standards met
- Incident response procedures documented
- Regular security assessments conducted

---

## Resources

### Internal Documentation

- [Authentication Guide](./authentication-guide.md)
- [API Reference](./api-reference-auth.md)
- [Quick Reference](./api-authentication-quick-reference.md)

### External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Firebase Security Rules](https://firebase.google.com/docs/rules)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)

### Security Contacts

- **Security Issues:** security@utxoiq.com
- **Bug Bounty:** https://utxoiq.com/security/bug-bounty
- **General Support:** support@utxoiq.com

---

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email security@utxoiq.com with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
3. We'll respond within 24 hours
4. We'll work with you to understand and fix the issue
5. We'll credit you in our security acknowledgments (if desired)

---

**Last Updated:** January 2024  
**Version:** 1.0.0
