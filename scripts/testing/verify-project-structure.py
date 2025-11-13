#!/usr/bin/env python3
"""
Verify project structure follows organizational guidelines.
"""

import os
from pathlib import Path
from typing import List, Tuple

def check_root_directory() -> List[str]:
    """Check that root directory only contains allowed files."""
    issues = []
    root = Path(".")
    
    allowed_extensions = {'.md', '.json', '.yml', '.yaml', '.txt', '.ini', 
                         '.bat', '.sh', '.code-workspace'}
    allowed_names = {'Dockerfile', 'LICENSE', 'CODEOWNERS', '.gitignore', 
                    '.dockerignore', '.env', '.env.example', '.env.local'}
    allowed_dirs = {'docs', 'scripts', 'tests', 'services', 'frontend', 
                   'shared', 'infrastructure', 'node_modules', 'venv', 
                   'venv312', '.git', '.github', '.kiro', '.vscode', 
                   'data', 'logs', 'temp', 'sdks'}
    
    for item in root.iterdir():
        if item.is_file():
            if item.suffix not in allowed_extensions and item.name not in allowed_names:
                issues.append(f"Unexpected file in root: {item.name}")
        elif item.is_dir():
            if item.name not in allowed_dirs:
                issues.append(f"Unexpected directory in root: {item.name}")
    
    return issues

def check_test_structure() -> List[str]:
    """Check that tests follow naming conventions."""
    issues = []
    tests_dir = Path("tests")
    
    if not tests_dir.exists():
        return ["tests/ directory not found"]
    
    expected_dirs = {'unit', 'integration', 'e2e', 'performance', 'security'}
    existing_dirs = {d.name for d in tests_dir.iterdir() if d.is_dir()}
    
    # Allowed helper files
    allowed_helpers = {'helpers.py', 'conftest.py', '__init__.py', 'README.md', 
                      'requirements.txt', 'pytest.ini'}
    
    for test_file in tests_dir.rglob("*.py"):
        if test_file.name in allowed_helpers:
            continue
        if not any(test_file.name.endswith(suffix) for suffix in 
                  ['.unit.test.py', '.integration.test.py', '.e2e.test.py', 
                   '.performance.test.py', '.security.test.py']):
            issues.append(f"Test file doesn't follow naming convention: {test_file}")
    
    return issues

def check_docs_structure() -> List[str]:
    """Check that docs are properly organized."""
    issues = []
    docs_dir = Path("docs")
    
    if not docs_dir.exists():
        return ["docs/ directory not found"]
    
    expected_dirs = {'implementation', 'archive', 'specs'}
    
    # Check for task files in root
    for doc in docs_dir.glob("task-*.md"):
        issues.append(f"Task file should be in docs/implementation/: {doc.name}")
    
    # Check for status/summary files in root (exclude cleanup-summary.md and project-organization.md)
    excluded_files = {'cleanup-summary.md', 'project-organization.md', 'test-migration-guide.md'}
    for pattern in ['*-status.md', '*-summary.md', '*-complete.md']:
        for doc in docs_dir.glob(pattern):
            if doc.name not in excluded_files:
                issues.append(f"Status/summary file should be in docs/archive/: {doc.name}")
    
    return issues

def check_scripts_structure() -> List[str]:
    """Check that scripts are properly organized."""
    issues = []
    scripts_dir = Path("scripts")
    
    if not scripts_dir.exists():
        return ["scripts/ directory not found"]
    
    expected_dirs = {'setup', 'deployment', 'data', 'testing', 'bigquery'}
    
    # Check for deployment scripts in root
    for script in scripts_dir.glob("deploy-*"):
        if script.is_file():
            issues.append(f"Deployment script should be in scripts/deployment/: {script.name}")
    
    # Check for test scripts in root
    for script in scripts_dir.glob("test-*"):
        if script.is_file():
            issues.append(f"Test script should be in scripts/testing/: {script.name}")
    
    return issues

def check_service_tests() -> List[str]:
    """Check that service tests follow naming conventions."""
    issues = []
    services_dir = Path("services")
    
    if not services_dir.exists():
        return []
    
    # All services have been migrated
    migrated_services = [
        'utxoiq-ingestion',
        'chart-renderer',
        'data-ingestion',
        'email-service',
        'insight-generator',
        'web-api',
        'x-bot'
    ]
    
    for service_name in migrated_services:
        service = services_dir / service_name
        if not service.exists():
            continue
        
        tests_dir = service / "tests"
        if not tests_dir.exists():
            continue
        
        for test_file in tests_dir.rglob("*.py"):
            if test_file.name == "__init__.py":
                continue
            if test_file.name.startswith("test_"):
                issues.append(f"Service test should use new naming: {test_file}")
    
    return issues

def main():
    """Run all structure checks."""
    print("🔍 Verifying project structure...\n")
    
    all_issues = []
    
    checks = [
        ("Root Directory", check_root_directory),
        ("Test Structure", check_test_structure),
        ("Docs Structure", check_docs_structure),
        ("Scripts Structure", check_scripts_structure),
        ("Service Tests", check_service_tests),
    ]
    
    for check_name, check_func in checks:
        print(f"Checking {check_name}...")
        issues = check_func()
        if issues:
            all_issues.extend([(check_name, issue) for issue in issues])
            print(f"  ❌ Found {len(issues)} issue(s)")
        else:
            print(f"  ✅ OK")
    
    print("\n" + "="*60)
    
    if all_issues:
        print(f"\n⚠️  Found {len(all_issues)} total issue(s):\n")
        for check_name, issue in all_issues:
            print(f"  [{check_name}] {issue}")
        print("\nSee docs/project-organization.md for guidelines.")
        return 1
    else:
        print("\n✅ All structure checks passed!")
        return 0

if __name__ == "__main__":
    exit(main())
