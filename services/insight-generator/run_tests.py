#!/usr/bin/env python3
"""
Test runner for insight generator service
"""

import sys
import pytest

if __name__ == "__main__":
    # Run pytest with coverage
    args = [
        "tests/",
        "-v",
        "--tb=short",
        "--cov=src",
        "--cov-report=term-missing"
    ]
    
    sys.exit(pytest.main(args))
