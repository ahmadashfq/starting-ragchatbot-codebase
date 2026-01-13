#!/bin/bash
# Format Python code with black

set -e

cd "$(dirname "$0")/.."

echo "Formatting Python code with black..."
uv run black backend/ main.py

echo "Done! All files formatted."
