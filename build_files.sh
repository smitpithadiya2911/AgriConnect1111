#!/bin/bash
set -e

# Add uv-managed Python to PATH so pip and python3 use the same interpreter
for dir in /uv/python/versions/*/bin; do
    export PATH="$dir:$PATH"
done

echo "Using Python: $(which python3)"
echo "Python version: $(python3 --version)"

python3 -m pip install -r requirements.txt --break-system-packages

# Use temporary SQLite DB — no MySQL needed for collectstatic
DATABASE_URL=sqlite:////tmp/db.sqlite3 python3 manage.py collectstatic --no-input --clear
