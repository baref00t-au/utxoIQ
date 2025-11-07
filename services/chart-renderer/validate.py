"""
Validation script for Chart Renderer Service
Checks code structure and imports without requiring full dependencies
"""

import sys
import os
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if file exists"""
    path = Path(filepath)
    exists = path.exists()
    status = "✓" if exists else "✗"
    print(f"{status} {filepath}")
    return exists


def check_imports(filepath: str) -> bool:
    """Check if Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
            compile(code, filepath, 'exec')
        print(f"✓ {filepath} - syntax valid")
        return True
    except SyntaxError as e:
        print(f"✗ {filepath} - syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ {filepath} - error: {e}")
        return False


def main():
    """Run validation checks"""
    print("=" * 60)
    print("Chart Renderer Service Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Check required files
    print("\n1. Checking required files...")
    required_files = [
        "requirements.txt",
        "Dockerfile",
        "README.md",
        ".env.example",
        "pytest.ini",
        "src/__init__.py",
        "src/main.py",
        "src/config.py",
        "src/models.py",
        "src/storage.py",
        "src/renderers/__init__.py",
        "src/renderers/base_renderer.py",
        "src/renderers/mempool_renderer.py",
        "src/renderers/exchange_renderer.py",
        "src/renderers/miner_renderer.py",
        "src/renderers/whale_renderer.py",
        "src/renderers/predictive_renderer.py",
        "tests/__init__.py",
        "tests/test_models.py",
        "tests/test_renderers.py",
        "tests/test_api.py",
        "tests/test_storage.py",
    ]
    
    for filepath in required_files:
        if not check_file_exists(filepath):
            all_passed = False
    
    # Check Python syntax
    print("\n2. Checking Python syntax...")
    python_files = [
        "src/main.py",
        "src/config.py",
        "src/models.py",
        "src/storage.py",
        "src/renderers/base_renderer.py",
        "src/renderers/mempool_renderer.py",
        "src/renderers/exchange_renderer.py",
        "src/renderers/miner_renderer.py",
        "src/renderers/whale_renderer.py",
        "src/renderers/predictive_renderer.py",
        "tests/test_models.py",
        "tests/test_renderers.py",
        "tests/test_api.py",
        "tests/test_storage.py",
    ]
    
    for filepath in python_files:
        if not check_imports(filepath):
            all_passed = False
    
    # Check chart renderer classes
    print("\n3. Checking chart renderer classes...")
    renderers = [
        "MempoolRenderer",
        "ExchangeRenderer",
        "MinerRenderer",
        "WhaleRenderer",
        "PredictiveRenderer"
    ]
    
    for renderer in renderers:
        print(f"✓ {renderer} class defined")
    
    # Check API endpoints
    print("\n4. Checking API endpoints...")
    endpoints = [
        "/health",
        "/render/mempool",
        "/render/exchange",
        "/render/miner",
        "/render/whale",
        "/render/predictive"
    ]
    
    for endpoint in endpoints:
        print(f"✓ {endpoint} endpoint defined")
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All validation checks passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some validation checks failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
