#!/usr/bin/env python3
"""
Grafana Observability Stack Validation Script

This script validates the Grafana and Prometheus setup for utxoIQ.
"""

import json
import sys
import requests
from pathlib import Path
from typing import List, Tuple


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def validate_json_files() -> Tuple[bool, List[str]]:
    """Validate all JSON dashboard files"""
    print_header("Validating Dashboard JSON Files")
    
    dashboard_dir = Path(__file__).parent / "dashboards"
    errors = []
    success = True
    
    if not dashboard_dir.exists():
        print_error(f"Dashboard directory not found: {dashboard_dir}")
        return False, ["Dashboard directory missing"]
    
    json_files = list(dashboard_dir.glob("*.json"))
    
    if not json_files:
        print_warning("No dashboard JSON files found")
        return True, []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Validate required fields
            required_fields = ['title', 'panels', 'uid']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                error_msg = f"{json_file.name}: Missing required fields: {', '.join(missing_fields)}"
                print_error(error_msg)
                errors.append(error_msg)
                success = False
            else:
                print_success(f"{json_file.name}: Valid JSON with {len(data.get('panels', []))} panels")
        
        except json.JSONDecodeError as e:
            error_msg = f"{json_file.name}: Invalid JSON - {str(e)}"
            print_error(error_msg)
            errors.append(error_msg)
            success = False
        except Exception as e:
            error_msg = f"{json_file.name}: Error - {str(e)}"
            print_error(error_msg)
            errors.append(error_msg)
            success = False
    
    return success, errors


def validate_alert_files() -> Tuple[bool, List[str]]:
    """Validate alert YAML files"""
    print_header("Validating Alert YAML Files")
    
    alerts_dir = Path(__file__).parent / "alerts"
    errors = []
    success = True
    
    if not alerts_dir.exists():
        print_error(f"Alerts directory not found: {alerts_dir}")
        return False, ["Alerts directory missing"]
    
    yaml_files = list(alerts_dir.glob("*.yml"))
    
    if not yaml_files:
        print_warning("No alert YAML files found")
        return True, []
    
    try:
        import yaml
    except ImportError:
        print_warning("PyYAML not installed, skipping YAML validation")
        print_warning("Install with: pip install pyyaml")
        return True, []
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Validate structure
            if 'groups' not in data:
                error_msg = f"{yaml_file.name}: Missing 'groups' key"
                print_error(error_msg)
                errors.append(error_msg)
                success = False
            else:
                alert_count = sum(len(group.get('rules', [])) for group in data['groups'])
                print_success(f"{yaml_file.name}: Valid YAML with {alert_count} alert rules")
        
        except yaml.YAMLError as e:
            error_msg = f"{yaml_file.name}: Invalid YAML - {str(e)}"
            print_error(error_msg)
            errors.append(error_msg)
            success = False
        except Exception as e:
            error_msg = f"{yaml_file.name}: Error - {str(e)}"
            print_error(error_msg)
            errors.append(error_msg)
            success = False
    
    return success, errors


def validate_provisioning_files() -> Tuple[bool, List[str]]:
    """Validate provisioning configuration files"""
    print_header("Validating Provisioning Configuration")
    
    provisioning_dir = Path(__file__).parent / "provisioning"
    errors = []
    success = True
    
    required_files = [
        "datasources/datasources.yml",
        "dashboards/dashboards.yml"
    ]
    
    for file_path in required_files:
        full_path = provisioning_dir / file_path
        if full_path.exists():
            print_success(f"{file_path}: Found")
        else:
            error_msg = f"{file_path}: Missing"
            print_error(error_msg)
            errors.append(error_msg)
            success = False
    
    return success, errors


def validate_docker_compose() -> Tuple[bool, List[str]]:
    """Validate docker-compose.yml file"""
    print_header("Validating Docker Compose Configuration")
    
    compose_file = Path(__file__).parent / "docker-compose.yml"
    errors = []
    success = True
    
    if not compose_file.exists():
        error_msg = "docker-compose.yml not found"
        print_error(error_msg)
        return False, [error_msg]
    
    try:
        import yaml
    except ImportError:
        print_warning("PyYAML not installed, skipping docker-compose validation")
        return True, []
    
    try:
        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Check for required services
        required_services = ['grafana', 'prometheus']
        services = data.get('services', {})
        
        for service in required_services:
            if service in services:
                print_success(f"Service '{service}': Configured")
            else:
                error_msg = f"Service '{service}': Missing"
                print_error(error_msg)
                errors.append(error_msg)
                success = False
    
    except Exception as e:
        error_msg = f"Error validating docker-compose.yml: {str(e)}"
        print_error(error_msg)
        errors.append(error_msg)
        success = False
    
    return success, errors


def check_services_running() -> Tuple[bool, List[str]]:
    """Check if Grafana and Prometheus services are running"""
    print_header("Checking Running Services")
    
    errors = []
    success = True
    
    # Check Grafana
    try:
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        if response.status_code == 200:
            print_success("Grafana: Running on http://localhost:3000")
        else:
            print_warning(f"Grafana: Responded with status {response.status_code}")
    except requests.exceptions.RequestException:
        print_warning("Grafana: Not running on http://localhost:3000")
        print_warning("  Start with: docker-compose up -d")
    
    # Check Prometheus
    try:
        response = requests.get("http://localhost:9090/-/healthy", timeout=5)
        if response.status_code == 200:
            print_success("Prometheus: Running on http://localhost:9090")
        else:
            print_warning(f"Prometheus: Responded with status {response.status_code}")
    except requests.exceptions.RequestException:
        print_warning("Prometheus: Not running on http://localhost:9090")
        print_warning("  Start with: docker-compose up -d")
    
    return success, errors


def main():
    """Main validation function"""
    print_header("utxoIQ Grafana Observability Stack Validation")
    
    all_success = True
    all_errors = []
    
    # Run validations
    validations = [
        validate_json_files,
        validate_alert_files,
        validate_provisioning_files,
        validate_docker_compose,
        check_services_running
    ]
    
    for validation_func in validations:
        success, errors = validation_func()
        all_success = all_success and success
        all_errors.extend(errors)
    
    # Print summary
    print_header("Validation Summary")
    
    if all_success and not all_errors:
        print_success("All validations passed!")
        print("\nNext steps:")
        print("  1. Start services: docker-compose up -d")
        print("  2. Access Grafana: http://localhost:3000")
        print("  3. Access Prometheus: http://localhost:9090")
        return 0
    else:
        print_error(f"Validation failed with {len(all_errors)} error(s)")
        print("\nErrors found:")
        for error in all_errors:
            print(f"  - {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
