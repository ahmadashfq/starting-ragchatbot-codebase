#!/bin/bash
# Check Python code formatting without modifying files

set -e

cd "$(dirname "$0")/.."

echo "Checking Python code formatting..."
uv run black --check backend/ main.py

echo "All files are properly formatted!"
