# Security Guidelines for Firebase Credentials

## 🔒 Critical Security Information

### Firebase Service Account Credentials

The file `firebase-credentials.json` contains **HIGHLY SENSITIVE** credentials that provide full administrative access to your Firebase project. **NEVER commit this file to version control.**

## ✅ Protection Measures in Place

### 1. Git Ignore Configuration

**Root `.gitignore`:**
```gitignore
# GCP credentials
*-key.json
service-account*.json
firebase-credentials.json
*firebase-credentials*.json
```

**Service `.gitignore` (`services/web-api/.gitignore`):**
```gitignore
# Firebase credentials - NEVER commit these!
firebase-credentials.json
*firebase-credentials*.json
```

### 2. Verification Steps

Before committing, always verify credentials are not tracked:

```bash
# Check if file is tracked
git ls-files | grep firebase-credentials

# Check git status
git status

# If accidentally staged, remove from staging
git rm --cached services/web-api/firebase-credentials.json
```

### 3. If Credentials Are Leaked

**IMMEDIATE ACTIONS REQUIRED:**

1. **Revoke the compromised service account:**
   ```bash
   # Go to Firebase Console
   # Settings → Service Accounts → Manage service account permissions
   # Delete the compromised service account
   ```

2. **Generate new credentials:**
   - Firebase Console → Settings → Service Accounts
   - Click "Generate new private key"
   - Download and save securely

3. **Remove from git history (if committed):**
   ```bash
   # Use BFG Repo-Cleaner or git filter-branch
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch services/web-api/firebase-credentials.json" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push (WARNING: This rewrites history)
   git push origin --force --all
   ```

4. **Notify your team** about the security incident

5. **Audit Firebase logs** for unauthorized access

## 📋 Best Practices

### Development Environment

1. **Local Development:**
   - Store credentials in `services/web-api/firebase-credentials.json`
   - File is automatically ignored by git
   - Never share credentials via email, Slack, or other channels

2. **Team Sharing:**
   - Use secure password managers (1Password, LastPass, etc.)
   - Share via encrypted channels only
   - Each developer should download their own copy from Firebase Console

### Production Environment

1. **Use Secret Manager:**
   ```bash
   # Store in GCP Secret Manager
   gcloud secrets create firebase-credentials \
     --data-file=firebase-credentials.json \
     --project=utxoiq
   
   # Grant access to service account
   gcloud secrets add-iam-policy-binding firebase-credentials \
     --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   ```

2. **Environment Variables:**
   ```bash
   # In Cloud Run, set secret as environment variable
   gcloud run services update web-api \
     --update-secrets=FIREBASE_CREDENTIALS=/secrets/firebase-credentials:latest
   ```

3. **Never hardcode credentials** in source code

### CI/CD Pipeline

1. **GitHub Actions:**
   ```yaml
   # Store credentials as GitHub Secret
   # Settings → Secrets → Actions → New repository secret
   # Name: FIREBASE_CREDENTIALS
   # Value: <paste JSON content>
   
   # In workflow:
   - name: Setup Firebase credentials
     run: echo '${{ secrets.FIREBASE_CREDENTIALS }}' > firebase-credentials.json
   ```

2. **Clean up after use:**
   ```yaml
   - name: Cleanup
     if: always()
     run: rm -f firebase-credentials.json
   ```

## 🔍 Audit Checklist

Before every commit:

- [ ] Run `git status` to check for untracked files
- [ ] Verify `.gitignore` includes `firebase-credentials.json`
- [ ] Check no credentials in environment files (`.env`)
- [ ] Ensure no API keys or secrets in code comments
- [ ] Review diff for any sensitive data

## 📚 Additional Resources

- [Firebase Security Best Practices](https://firebase.google.com/docs/admin/setup#initialize-sdk)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Git Secrets Tool](https://github.com/awslabs/git-secrets)

## 🚨 Emergency Contacts

If credentials are compromised:

1. **Revoke immediately** in Firebase Console
2. **Notify team lead** or security officer
3. **Document the incident** for audit trail
4. **Generate new credentials** and update all environments

---

**Remember: Security is everyone's responsibility. When in doubt, ask!**
