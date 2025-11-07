#!/usr/bin/env python3
"""
Security Audit Scheduler

Manages annual third-party security audit scheduling and tracking.
Requirement: 24.1 - Annual third-party security audits
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List


class AuditScheduler:
    """Manages security audit scheduling and vendor coordination."""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path(__file__).parent.parent
        self.audits_path = self.base_path / "audits"
        self.audits_path.mkdir(parents=True, exist_ok=True)
        
    def schedule_audit(self, year: int, vendor: str = None) -> Dict:
        """
        Schedule annual security audit.
        
        Args:
            year: Year for the audit
            vendor: Preferred security audit vendor
            
        Returns:
            Dict containing audit schedule details
        """
        audit_id = f"AUDIT-{year}"
        
        # Calculate audit windows (typically Q4 of each year)
        audit_start = datetime(year, 10, 1)
        audit_end = datetime(year, 11, 30)
        report_due = datetime(year, 12, 31)
        
        audit_schedule = {
            "audit_id": audit_id,
            "year": year,
            "vendor": vendor or "TBD - RFP Required",
            "scope": [
                "Cloud infrastructure security (GCP)",
                "Application security (web-api, frontend)",
                "Data security (BigQuery, Cloud SQL, Redis)",
                "Authentication and authorization (Firebase Auth)",
                "API security and rate limiting",
                "Secrets management (Cloud Secret Manager)",
                "Network security and firewall rules",
                "Logging and monitoring security",
                "Incident response procedures",
                "Data privacy and GDPR compliance"
            ],
            "schedule": {
                "rfp_deadline": (audit_start - timedelta(days=120)).isoformat(),
                "vendor_selection": (audit_start - timedelta(days=90)).isoformat(),
                "kickoff_meeting": (audit_start - timedelta(days=30)).isoformat(),
                "audit_start": audit_start.isoformat(),
                "audit_end": audit_end.isoformat(),
                "draft_report": (report_due - timedelta(days=14)).isoformat(),
                "final_report": report_due.isoformat()
            },
            "deliverables": [
                "Executive summary",
                "Detailed findings report",
                "Risk assessment matrix",
                "Remediation recommendations",
                "Compliance gap analysis",
                "Security posture scorecard"
            ],
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        # Save schedule
        schedule_file = self.audits_path / f"{audit_id}_schedule.json"
        with open(schedule_file, 'w') as f:
            json.dump(audit_schedule, f, indent=2)
            
        print(f"✓ Security audit scheduled for {year}")
        print(f"  Audit ID: {audit_id}")
        print(f"  RFP Deadline: {audit_schedule['schedule']['rfp_deadline']}")
        print(f"  Audit Window: {audit_start.date()} to {audit_end.date()}")
        print(f"  Schedule saved to: {schedule_file}")
        
        return audit_schedule
    
    def list_audits(self) -> List[Dict]:
        """List all scheduled and completed audits."""
        audits = []
        for schedule_file in self.audits_path.glob("AUDIT-*_schedule.json"):
            with open(schedule_file) as f:
                audits.append(json.load(f))
        return sorted(audits, key=lambda x: x['year'], reverse=True)
    
    def update_audit_status(self, audit_id: str, status: str, notes: str = None):
        """
        Update audit status.
        
        Args:
            audit_id: Audit identifier
            status: New status (scheduled, in_progress, completed, cancelled)
            notes: Optional status notes
        """
        schedule_file = self.audits_path / f"{audit_id}_schedule.json"
        
        if not schedule_file.exists():
            raise ValueError(f"Audit {audit_id} not found")
            
        with open(schedule_file) as f:
            audit = json.load(f)
            
        audit['status'] = status
        audit['updated_at'] = datetime.now().isoformat()
        
        if notes:
            if 'notes' not in audit:
                audit['notes'] = []
            audit['notes'].append({
                'timestamp': datetime.now().isoformat(),
                'note': notes
            })
            
        with open(schedule_file, 'w') as f:
            json.dump(audit, f, indent=2)
            
        print(f"✓ Audit {audit_id} status updated to: {status}")


def main():
    parser = argparse.ArgumentParser(
        description="Schedule and manage annual security audits"
    )
    parser.add_argument(
        '--year',
        type=int,
        default=datetime.now().year,
        help='Year for the security audit'
    )
    parser.add_argument(
        '--vendor',
        type=str,
        help='Preferred security audit vendor'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all scheduled audits'
    )
    parser.add_argument(
        '--update-status',
        type=str,
        help='Update audit status (format: AUDIT-YYYY:status)'
    )
    
    args = parser.parse_args()
    scheduler = AuditScheduler()
    
    if args.list:
        audits = scheduler.list_audits()
        print(f"\n{'='*60}")
        print("Scheduled Security Audits")
        print(f"{'='*60}\n")
        for audit in audits:
            print(f"Audit ID: {audit['audit_id']}")
            print(f"  Year: {audit['year']}")
            print(f"  Vendor: {audit['vendor']}")
            print(f"  Status: {audit['status']}")
            print(f"  Audit Window: {audit['schedule']['audit_start'][:10]} to {audit['schedule']['audit_end'][:10]}")
            print()
    elif args.update_status:
        audit_id, status = args.update_status.split(':')
        scheduler.update_audit_status(audit_id, status)
    else:
        scheduler.schedule_audit(args.year, args.vendor)


if __name__ == '__main__':
    main()
