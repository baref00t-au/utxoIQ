#!/usr/bin/env python3
"""
Security Remediation Tracker

Tracks security findings and ensures critical issues are remediated within 30 days.
Requirement: 24.5 - Create remediation process for critical security findings (< 30 days)
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class RemediationTracker:
    """Manages security finding remediation tracking."""
    
    SEVERITY_LEVELS = ['critical', 'high', 'medium', 'low', 'info']
    
    # SLA for remediation by severity
    REMEDIATION_SLA = {
        'critical': 30,  # days
        'high': 60,
        'medium': 90,
        'low': 180,
        'info': 365
    }
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path(__file__).parent.parent
        self.remediation_path = self.base_path / "remediation"
        self.remediation_path.mkdir(parents=True, exist_ok=True)
        
    def create_finding(
        self,
        title: str,
        severity: str,
        source: str,
        description: str,
        affected_component: str,
        remediation_steps: List[str]
    ) -> Dict:
        """
        Create a new security finding for tracking.
        
        Args:
            title: Finding title
            severity: Severity level (critical, high, medium, low, info)
            source: Source of finding (audit, pentest, scan)
            description: Detailed description
            affected_component: Affected service or component
            remediation_steps: List of remediation steps
            
        Returns:
            Dict containing finding details
        """
        if severity not in self.SEVERITY_LEVELS:
            raise ValueError(f"Severity must be one of: {self.SEVERITY_LEVELS}")
            
        # Generate finding ID
        finding_id = f"SEC-{datetime.now().strftime('%Y%m%d')}-{self._get_next_id()}"
        
        created_date = datetime.now()
        sla_days = self.REMEDIATION_SLA[severity]
        due_date = created_date + timedelta(days=sla_days)
        
        finding = {
            "finding_id": finding_id,
            "title": title,
            "severity": severity,
            "source": source,
            "description": description,
            "affected_component": affected_component,
            "remediation_steps": remediation_steps,
            "status": "open",
            "priority": self._calculate_priority(severity),
            "dates": {
                "created": created_date.isoformat(),
                "due": due_date.isoformat(),
                "sla_days": sla_days,
                "resolved": None
            },
            "assignee": None,
            "progress": [],
            "verification": {
                "verified": False,
                "verified_by": None,
                "verified_date": None
            },
            "created_at": created_date.isoformat()
        }
        
        # Save finding
        finding_file = self.remediation_path / f"{finding_id}.json"
        with open(finding_file, 'w') as f:
            json.dump(finding, f, indent=2)
            
        print(f"✓ Security finding created")
        print(f"  Finding ID: {finding_id}")
        print(f"  Severity: {severity.upper()}")
        print(f"  Due Date: {due_date.strftime('%Y-%m-%d')} ({sla_days} days)")
        print(f"  Finding file: {finding_file}")
        
        return finding
    
    def _get_next_id(self) -> str:
        """Generate next sequential ID for today."""
        today = datetime.now().strftime('%Y%m%d')
        existing = list(self.remediation_path.glob(f"SEC-{today}-*.json"))
        return f"{len(existing) + 1:03d}"
    
    def _calculate_priority(self, severity: str) -> int:
        """Calculate priority score (1-5, 1 being highest)."""
        priority_map = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4,
            'info': 5
        }
        return priority_map[severity]
    
    def update_finding(
        self,
        finding_id: str,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        progress_note: Optional[str] = None
    ):
        """
        Update finding status and progress.
        
        Args:
            finding_id: Finding identifier
            status: New status (open, in_progress, resolved, verified, closed)
            assignee: Person assigned to remediate
            progress_note: Progress update note
        """
        finding_file = self.remediation_path / f"{finding_id}.json"
        
        if not finding_file.exists():
            raise ValueError(f"Finding {finding_id} not found")
            
        with open(finding_file) as f:
            finding = json.load(f)
            
        if status:
            finding['status'] = status
            if status == 'resolved':
                finding['dates']['resolved'] = datetime.now().isoformat()
                
        if assignee:
            finding['assignee'] = assignee
            
        if progress_note:
            finding['progress'].append({
                'timestamp': datetime.now().isoformat(),
                'note': progress_note
            })
            
        finding['updated_at'] = datetime.now().isoformat()
            
        with open(finding_file, 'w') as f:
            json.dump(finding, f, indent=2)
            
        print(f"✓ Finding {finding_id} updated")
        if status:
            print(f"  Status: {status}")
        if assignee:
            print(f"  Assignee: {assignee}")
    
    def verify_remediation(self, finding_id: str, verified_by: str):
        """
        Verify that remediation is complete and effective.
        
        Args:
            finding_id: Finding identifier
            verified_by: Person verifying the remediation
        """
        finding_file = self.remediation_path / f"{finding_id}.json"
        
        if not finding_file.exists():
            raise ValueError(f"Finding {finding_id} not found")
            
        with open(finding_file) as f:
            finding = json.load(f)
            
        if finding['status'] != 'resolved':
            raise ValueError(f"Finding must be in 'resolved' status before verification")
            
        finding['verification'] = {
            'verified': True,
            'verified_by': verified_by,
            'verified_date': datetime.now().isoformat()
        }
        finding['status'] = 'verified'
        finding['updated_at'] = datetime.now().isoformat()
            
        with open(finding_file, 'w') as f:
            json.dump(finding, f, indent=2)
            
        print(f"✓ Finding {finding_id} verified")
        print(f"  Verified by: {verified_by}")
    
    def list_findings(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        overdue_only: bool = False
    ) -> List[Dict]:
        """
        List security findings with optional filters.
        
        Args:
            status: Filter by status
            severity: Filter by severity
            overdue_only: Show only overdue findings
            
        Returns:
            List of findings matching filters
        """
        findings = []
        
        for finding_file in self.remediation_path.glob("SEC-*.json"):
            with open(finding_file) as f:
                finding = json.load(f)
                
            # Apply filters
            if status and finding['status'] != status:
                continue
            if severity and finding['severity'] != severity:
                continue
            if overdue_only:
                due_date = datetime.fromisoformat(finding['dates']['due'])
                if datetime.now() <= due_date or finding['status'] in ['resolved', 'verified', 'closed']:
                    continue
                    
            findings.append(finding)
            
        return sorted(findings, key=lambda x: (x['priority'], x['dates']['due']))
    
    def generate_status_report(self) -> Dict:
        """Generate remediation status report."""
        all_findings = self.list_findings()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total": len(all_findings),
                "by_status": {},
                "by_severity": {},
                "overdue": 0,
                "critical_open": 0
            },
            "sla_compliance": {
                "critical": {"total": 0, "on_time": 0, "overdue": 0},
                "high": {"total": 0, "on_time": 0, "overdue": 0},
                "medium": {"total": 0, "on_time": 0, "overdue": 0},
                "low": {"total": 0, "on_time": 0, "overdue": 0}
            },
            "findings": []
        }
        
        for finding in all_findings:
            # Count by status
            status = finding['status']
            report['summary']['by_status'][status] = report['summary']['by_status'].get(status, 0) + 1
            
            # Count by severity
            severity = finding['severity']
            report['summary']['by_severity'][severity] = report['summary']['by_severity'].get(severity, 0) + 1
            
            # Check if overdue
            due_date = datetime.fromisoformat(finding['dates']['due'])
            is_overdue = datetime.now() > due_date and status not in ['resolved', 'verified', 'closed']
            
            if is_overdue:
                report['summary']['overdue'] += 1
                
            if severity == 'critical' and status == 'open':
                report['summary']['critical_open'] += 1
                
            # SLA compliance tracking
            if severity in ['critical', 'high', 'medium', 'low']:
                report['sla_compliance'][severity]['total'] += 1
                if is_overdue:
                    report['sla_compliance'][severity]['overdue'] += 1
                else:
                    report['sla_compliance'][severity]['on_time'] += 1
                    
            # Add to findings list
            report['findings'].append({
                'finding_id': finding['finding_id'],
                'title': finding['title'],
                'severity': finding['severity'],
                'status': finding['status'],
                'due_date': finding['dates']['due'],
                'overdue': is_overdue,
                'days_until_due': (due_date - datetime.now()).days
            })
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description="Track security finding remediation"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create finding
    create_parser = subparsers.add_parser('create', help='Create new finding')
    create_parser.add_argument('--title', required=True, help='Finding title')
    create_parser.add_argument('--severity', required=True, choices=RemediationTracker.SEVERITY_LEVELS)
    create_parser.add_argument('--source', required=True, help='Source (audit, pentest, scan)')
    create_parser.add_argument('--description', required=True, help='Description')
    create_parser.add_argument('--component', required=True, help='Affected component')
    create_parser.add_argument('--steps', required=True, help='Remediation steps (comma-separated)')
    
    # Update finding
    update_parser = subparsers.add_parser('update', help='Update finding')
    update_parser.add_argument('--finding-id', required=True, help='Finding ID')
    update_parser.add_argument('--status', choices=['open', 'in_progress', 'resolved', 'verified', 'closed'])
    update_parser.add_argument('--assignee', help='Assignee name')
    update_parser.add_argument('--note', help='Progress note')
    
    # Verify finding
    verify_parser = subparsers.add_parser('verify', help='Verify remediation')
    verify_parser.add_argument('--finding-id', required=True, help='Finding ID')
    verify_parser.add_argument('--verified-by', required=True, help='Verifier name')
    
    # List findings
    list_parser = subparsers.add_parser('list', help='List findings')
    list_parser.add_argument('--status', help='Filter by status')
    list_parser.add_argument('--severity', choices=RemediationTracker.SEVERITY_LEVELS)
    list_parser.add_argument('--overdue', action='store_true', help='Show only overdue')
    
    # Status report
    subparsers.add_parser('report', help='Generate status report')
    
    args = parser.parse_args()
    tracker = RemediationTracker()
    
    if args.command == 'create':
        steps = [s.strip() for s in args.steps.split(',')]
        tracker.create_finding(
            args.title,
            args.severity,
            args.source,
            args.description,
            args.component,
            steps
        )
    elif args.command == 'update':
        tracker.update_finding(
            args.finding_id,
            args.status,
            args.assignee,
            args.note
        )
    elif args.command == 'verify':
        tracker.verify_remediation(args.finding_id, args.verified_by)
    elif args.command == 'list':
        findings = tracker.list_findings(args.status, args.severity, args.overdue)
        print(f"\n{'='*80}")
        print("Security Findings")
        print(f"{'='*80}\n")
        for finding in findings:
            due_date = datetime.fromisoformat(finding['dates']['due'])
            days_until_due = (due_date - datetime.now()).days
            overdue = days_until_due < 0 and finding['status'] not in ['resolved', 'verified', 'closed']
            
            print(f"Finding ID: {finding['finding_id']}")
            print(f"  Title: {finding['title']}")
            print(f"  Severity: {finding['severity'].upper()}")
            print(f"  Status: {finding['status']}")
            print(f"  Due: {due_date.strftime('%Y-%m-%d')} ({days_until_due} days)")
            if overdue:
                print(f"  ⚠️  OVERDUE by {abs(days_until_due)} days")
            if finding['assignee']:
                print(f"  Assignee: {finding['assignee']}")
            print()
    elif args.command == 'report':
        report = tracker.generate_status_report()
        
        print(f"\n{'='*80}")
        print("Security Remediation Status Report")
        print(f"{'='*80}\n")
        print(f"Generated: {report['generated_at'][:10]}\n")
        
        print("Summary:")
        print(f"  Total Findings: {report['summary']['total']}")
        print(f"  Critical Open: {report['summary']['critical_open']}")
        print(f"  Overdue: {report['summary']['overdue']}")
        print()
        
        print("By Status:")
        for status, count in report['summary']['by_status'].items():
            print(f"  {status}: {count}")
        print()
        
        print("By Severity:")
        for severity, count in report['summary']['by_severity'].items():
            print(f"  {severity}: {count}")
        print()
        
        print("SLA Compliance:")
        for severity in ['critical', 'high', 'medium', 'low']:
            sla = report['sla_compliance'][severity]
            if sla['total'] > 0:
                compliance_rate = (sla['on_time'] / sla['total']) * 100
                print(f"  {severity.capitalize()}: {compliance_rate:.1f}% ({sla['on_time']}/{sla['total']} on time)")
        
        # Save report
        report_file = tracker.remediation_path / f"status_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Full report saved to: {report_file}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
