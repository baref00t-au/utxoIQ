"""
Test runner for Chart Renderer Service
"""

import sys
import pytest


def main():
    """Run all tests"""
    args = [
        "tests/",
        "-v",
        "--tb=short",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html"
    ]
    
    # Add any additional arguments passed to this script
    args.extend(sys.argv[1:])
    
    # Run pytest
    exit_code = pytest.main(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
