# Security Compliance Quick Start Guide

This guide helps you get started with the utxoIQ security compliance framework.

## Prerequisites

- Python 3.9 or higher
- Access to GCP project (for IAM reviews)
- Git repository access

## Installation

1. **Install Python dependencies:**
```bash
cd infrastructure/security/scripts
pip install -r requirements.txt
```

2. **Verify installation:**
```bash
python schedule_audit.py --help
python run_pentest.py --help
python iam_review.py --help
python remediation_tracker.py --help
```

## Quick Start Tasks

### 1. Schedule Annual Security Audit

Schedule the security audit for the current year:

```bash
python schedule_audit.py --year 2025 --vendor "Acme Security Auditors"
```

List all scheduled audits:

```bash
python schedule_audit.py --list
```

Update audit status:

```bash
python schedule_audit.py --update-status AUDIT-2025:in_progress
```

### 2. Plan Penetration Testing

Create a penetration test plan for the web API:

```bash
python run_pentest.py --target web-api --environment staging
```

Create plans for all services:

```bash
python run_pentest.py --target all --environment staging
```

List all penetration tests:

```bash
python run_pentest.py --list
```

Run automated security scan (placeholder):

```bash
python run_pentest.py --scan PENTEST-20251108-WEB-API:https://staging-api.utxoiq.com
```

### 3. Conduct IAM Policy Review

Create IAM review for current quarter:

```bash
python iam_review.py --quarter Q4 --year 2025
```

Run automated IAM checks:

```bash
python iam_review.py --check IAM-2025-Q4
```

List all IAM reviews:

```bash
python iam_review.py --list
```

### 4. Track Security Findings

Create a new security finding:

```bash
python remediation_tracker.py create \
  --title "SQL Injection in API endpoint" \
  --severity critical \
  --source pentest \
  --description "SQL injection vulnerability found in /api/v1/insights endpoint" \
  --component web-api \
  --steps "Implement parameterized queries,Add input validation,Deploy fix to production"
```

Update finding status:

```bash
python remediation_tracker.py update \
  --finding-id SEC-20251108-001 \
  --status in_progress \
  --assignee "John Doe" \
  --note "Started implementing parameterized queries"
```

List all open findings:

```bash
python remediation_tracker.py list --status open
```

List overdue findings:

```bash
python remediation_tracker.py list --overdue
```

Verify remediation:

```bash
python remediation_tracker.py verify \
  --finding-id SEC-20251108-001 \
  --verified-by "Security Team"
```

Generate status report:

```bash
python remediation_tracker.py report
```

## Quarterly Checklist

### Q1 (January - March)
- [ ] Conduct Q1 IAM policy review (Jan 15 - Feb 15)
- [ ] Issue RFP for annual security audit
- [ ] Run quarterly vulnerability scan
- [ ] Review and update security policies

### Q2 (April - June)
- [ ] Conduct Q2 IAM policy review (Apr 15 - May 15)
- [ ] Select security audit vendor
- [ ] Conduct semi-annual penetration test
- [ ] Run quarterly vulnerability scan

### Q3 (July - September)
- [ ] Conduct Q3 IAM policy review (Jul 15 - Aug 15)
- [ ] Run quarterly vulnerability scan
- [ ] Review security training materials

### Q4 (October - December)
- [ ] Conduct Q4 IAM policy review (Oct 15 - Nov 15)
- [ ] Conduct annual security audit
- [ ] Conduct semi-annual penetration test
- [ ] Run quarterly vulnerability scan
- [ ] Annual security policy review

## Automated Checks

The GitHub Actions workflow runs weekly security checks:

- Vulnerability scanning (Trivy)
- Dependency security checks (Safety, npm audit)
- Secret scanning (Gitleaks)
- IAM review status check
- Remediation tracking check

View workflow results:
```
https://github.com/utxoiq/utxoiq/actions/workflows/security-compliance.yml
```

## Integration with Grafana

Security metrics are tracked in Grafana dashboards:

- Open security findings by severity
- Remediation SLA compliance
- IAM review completion status
- Vulnerability scan results
- Penetration test findings

Access dashboards:
```
http://localhost:3000/d/security-compliance
```

## Best Practices

### Security Findings
1. **Triage immediately:** Assess severity within 24 hours
2. **Assign ownership:** Designate responsible engineer
3. **Track progress:** Update status regularly
4. **Verify fixes:** Always verify remediation before closing
5. **Document lessons:** Share learnings with team

### IAM Reviews
1. **Be thorough:** Review all users and service accounts
2. **Verify MFA:** Ensure all users have MFA enabled
3. **Check keys:** Rotate service account keys > 90 days old
4. **Remove unused:** Disable accounts not used in 90 days
5. **Document changes:** Record all permission changes

### Penetration Testing
1. **Test staging first:** Always test in staging environment
2. **Coordinate timing:** Schedule tests during low-traffic periods
3. **Monitor closely:** Watch for false positives
4. **Document findings:** Capture all evidence
5. **Retest fixes:** Verify remediation effectiveness

## Troubleshooting

### Common Issues

**Issue:** Script fails with "Module not found"
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Issue:** Permission denied when running scripts
```bash
# Solution: Make scripts executable
chmod +x *.py
```

**Issue:** JSON file not found
```bash
# Solution: Create the required directories
mkdir -p ../audits ../penetration-testing ../iam-reviews ../remediation
```

## Support

For questions or issues:
- Email: security@utxoiq.com
- Slack: #security-team
- Documentation: `/infrastructure/security/README.md`

## Next Steps

1. Review the [Security Compliance Framework](compliance/security-compliance-framework.md)
2. Read the [Information Security Policy](policies/information-security-policy.md)
3. Schedule your first security audit
4. Conduct quarterly IAM review
5. Set up automated security scanning
