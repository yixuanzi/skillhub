#!/bin/bash
# Test runner script that disables problematic pytest plugins

cd /Users/guisheng.guo/Documents/workspace/skillhub/backend
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest "$@"
