#!/bin/bash
set -e

# Add uv-managed Python to PATH so pip and python3 use the same interpreter
for dir in /uv/python/versions/*/bin; do
    if [ -d "$dir" ]; then
        export PATH="$dir:$PATH"
    fi
done

echo "Python binary: $(which python3)"
echo "Python version: $(python3 --version)"

echo "Installing project dependencies..."
python3 -m pip install -r requirements.txt --break-system-packages --no-warn-script-location --root-user-action=ignore

echo "Collecting static files..."
DJANGO_SETTINGS_MODULE=agriconnect_project.build_settings python3 manage.py collectstatic --no-input --clear

echo "Build completed successfully!"
