#!/usr/bin/env python3
"""
IAM Policy Review Tool

Conducts quarterly reviews of GCP IAM policies and permissions.
Requirement: 24.3 - Implement quarterly IAM policy reviews
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class IAMReviewer:
    """Manages quarterly IAM policy reviews."""
    
    # IAM roles that require review
    CRITICAL_ROLES = [
        'roles/owner',
        'roles/editor',
        'roles/iam.securityAdmin',
        'roles/iam.serviceAccountAdmin',
        'roles/resourcemanager.organizationAdmin'
    ]
    
    # Service accounts that require review
    SERVICE_ACCOUNTS = [
        'feature-engine@utxoiq.iam.gserviceaccount.com',
        'insight-generator@utxoiq.iam.gserviceaccount.com',
        'chart-renderer@utxoiq.iam.gserviceaccount.com',
        'web-api@utxoiq.iam.gserviceaccount.com',
        'x-bot@utxoiq.iam.gserviceaccount.com',
        'email-service@utxoiq.iam.gserviceaccount.com',
        'dataflow-worker@utxoiq.iam.gserviceaccount.com'
    ]
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path(__file__).parent.parent
        self.reviews_path = self.base_path / "iam-reviews"
        self.reviews_path.mkdir(parents=True, exist_ok=True)
        
    def create_review(self, quarter: str, year: int) -> Dict:
        """
        Create IAM policy review for a quarter.
        
        Args:
            quarter: Quarter identifier (Q1, Q2, Q3, Q4)
            year: Year for the review
            
        Returns:
            Dict containing review details
        """
        if quarter not in ['Q1', 'Q2', 'Q3', 'Q4']:
            raise ValueError("Quarter must be Q1, Q2, Q3, or Q4")
            
        review_id = f"IAM-{year}-{quarter}"
        
        review = {
            "review_id": review_id,
            "quarter": quarter,
            "year": year,
            "review_date": datetime.now().isoformat(),
            "reviewer": "Security Team",
            "scope": {
                "project_id": "utxoiq-production",
                "organization_id": "utxoiq-org",
                "critical_roles": self.CRITICAL_ROLES,
                "service_accounts": self.SERVICE_ACCOUNTS
            },
            "checklist": [
                {
                    "item": "Review all users with Owner role",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Review all users with Editor role",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Review service account permissions",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Verify principle of least privilege",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Check for unused service accounts",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Review custom IAM roles",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Verify MFA enabled for all users",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Review API key usage and rotation",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Check service account key rotation",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Review Cloud IAM conditions",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Verify separation of duties",
                    "status": "pending",
                    "notes": ""
                },
                {
                    "item": "Review external identity providers",
                    "status": "pending",
                    "notes": ""
                }
            ],
            "findings": [],
            "recommendations": [],
            "status": "in_progress",
            "created_at": datetime.now().isoformat()
        }
        
        # Save review
        review_file = self.reviews_path / f"{review_id}_review.json"
        with open(review_file, 'w') as f:
            json.dump(review, f, indent=2)
            
        print(f"✓ IAM policy review created")
        print(f"  Review ID: {review_id}")
        print(f"  Quarter: {quarter} {year}")
        print(f"  Review file: {review_file}")
        
        # Generate review template
        self._generate_review_template(review_id, review)
        
        return review
    
    def _generate_review_template(self, review_id: str, review: Dict):
        """Generate IAM review documentation template."""
        template_file = self.reviews_path / f"{review_id}_template.md"
        
        template = f"""# IAM Policy Review - {review['quarter']} {review['year']}

**Review ID:** {review_id}  
**Review Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Reviewer:** {review['reviewer']}  
**Status:** {review['status']}

## Scope

- **GCP Project:** {review['scope']['project_id']}
- **Organization:** {review['scope']['organization_id']}

## Review Checklist

"""
        for i, item in enumerate(review['checklist'], 1):
            template += f"{i}. [ ] {item['item']}\n"
            template += f"   - Status: {item['status']}\n"
            template += f"   - Notes: {item['notes'] or '_To be completed_'}\n\n"
        
        template += """
## Critical Roles Review

### Owner Role
| User/Service Account | Justification | Last Activity | Action |
|---------------------|---------------|---------------|--------|
| [user@example.com]  | [Reason]      | [Date]        | [Keep/Remove] |

### Editor Role
| User/Service Account | Justification | Last Activity | Action |
|---------------------|---------------|---------------|--------|
| [user@example.com]  | [Reason]      | [Date]        | [Keep/Remove] |

### Security Admin Role
| User/Service Account | Justification | Last Activity | Action |
|---------------------|---------------|---------------|--------|
| [user@example.com]  | [Reason]      | [Date]        | [Keep/Remove] |

## Service Account Review

"""
        for sa in review['scope']['service_accounts']:
            template += f"### {sa}\n"
            template += f"- **Purpose:** [Description]\n"
            template += f"- **Permissions:** [List key permissions]\n"
            template += f"- **Last Used:** [Date]\n"
            template += f"- **Key Rotation:** [Last rotation date]\n"
            template += f"- **Action:** [Keep/Modify/Remove]\n\n"
        
        template += """
## Findings

### Finding 1: [Title]
- **Severity:** [Critical/High/Medium/Low]
- **Description:** [Details]
- **Risk:** [Potential impact]
- **Recommendation:** [Remediation steps]

## Recommendations

### Immediate Actions
1. [Action 1]
2. [Action 2]

### Short-term Improvements
1. [Action 1]
2. [Action 2]

### Long-term Enhancements
1. [Action 1]
2. [Action 2]

## Compliance Status

- [ ] Principle of least privilege enforced
- [ ] Separation of duties implemented
- [ ] MFA enabled for all users
- [ ] Service account keys rotated (< 90 days)
- [ ] Unused accounts disabled
- [ ] Custom roles reviewed and justified

## Sign-off

**Reviewed by:** _____________________ Date: _____  
**Approved by:** _____________________ Date: _____

## Next Review

**Scheduled for:** [Next quarter] [Year]
"""
        
        with open(template_file, 'w') as f:
            f.write(template)
            
        print(f"✓ Review template generated: {template_file}")
    
    def run_automated_checks(self, review_id: str) -> Dict:
        """
        Run automated IAM policy checks.
        
        Args:
            review_id: Review identifier
            
        Returns:
            Dict containing automated check results
        """
        print(f"\n{'='*60}")
        print(f"Running Automated IAM Checks")
        print(f"{'='*60}\n")
        print(f"Review ID: {review_id}")
        print(f"\nNote: This is a placeholder for actual GCP IAM checks.")
        print(f"In production, this would execute:")
        print(f"  - gcloud iam list-grantable-roles")
        print(f"  - gcloud projects get-iam-policy")
        print(f"  - gcloud iam service-accounts list")
        print(f"  - Custom policy analyzer scripts")
        
        results = {
            "review_id": review_id,
            "check_type": "automated",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "owner_role_count": 0,
                "editor_role_count": 0,
                "service_accounts_count": len(self.SERVICE_ACCOUNTS),
                "unused_service_accounts": [],
                "keys_requiring_rotation": [],
                "users_without_mfa": [],
                "overprivileged_accounts": []
            },
            "status": "completed",
            "note": "Placeholder check - integrate with GCP IAM API"
        }
        
        # Save results
        results_file = self.reviews_path / f"{review_id}_automated_checks.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"\n✓ Automated check results saved to: {results_file}")
        
        return results
    
    def list_reviews(self) -> List[Dict]:
        """List all IAM reviews."""
        reviews = []
        for review_file in self.reviews_path.glob("IAM-*_review.json"):
            with open(review_file) as f:
                reviews.append(json.load(f))
        return sorted(reviews, key=lambda x: (x['year'], x['quarter']), reverse=True)


def main():
    parser = argparse.ArgumentParser(
        description="Conduct quarterly IAM policy reviews"
    )
    parser.add_argument(
        '--quarter',
        type=str,
        choices=['Q1', 'Q2', 'Q3', 'Q4'],
        help='Quarter for the review'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=datetime.now().year,
        help='Year for the review'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all IAM reviews'
    )
    parser.add_argument(
        '--check',
        type=str,
        help='Run automated checks for review ID'
    )
    
    args = parser.parse_args()
    reviewer = IAMReviewer()
    
    if args.list:
        reviews = reviewer.list_reviews()
        print(f"\n{'='*60}")
        print("IAM Policy Reviews")
        print(f"{'='*60}\n")
        for review in reviews:
            print(f"Review ID: {review['review_id']}")
            print(f"  Quarter: {review['quarter']} {review['year']}")
            print(f"  Status: {review['status']}")
            print(f"  Created: {review['created_at'][:10]}")
            print()
    elif args.check:
        reviewer.run_automated_checks(args.check)
    elif args.quarter:
        reviewer.create_review(args.quarter, args.year)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
