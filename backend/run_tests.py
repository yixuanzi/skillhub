#!/usr/bin/env python3
"""
Simple test runner that bypasses pytest plugin loading issues.
Run this directly: python run_tests.py
"""

import sys
import os

# Disable problematic plugins
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'

import pytest

# Run pytest with our configuration
if __name__ == '__main__':
    sys.exit(pytest.main([
        'tests/test_models.py',
        '-v',
        '--tb=short',
        '-p', 'no:langsmith'
    ]))
