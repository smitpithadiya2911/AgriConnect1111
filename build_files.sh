#!/bin/bash
set -e

# Add uv-managed Python to PATH so pip and python3 use the same interpreter
for dir in /uv/python/versions/*/bin; do
    export PATH="$dir:$PATH"
done

echo "Using Python: $(which python3)"
echo "Python version: $(python3 --version)"

python3 -m pip install -r requirements.txt --break-system-packages

# Use build_settings.py (SQLite in-memory) — no MySQL driver needed during build
DJANGO_SETTINGS_MODULE=agriconnect_project.build_settings python3 manage.py collectstatic --no-input --clear
