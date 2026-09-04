#!/bin/bash
set -e

echo "=== Starting Plasticprecious Backend Build ==="
echo "Python version:"
python --version

echo ""
echo "=== Upgrading pip ==="
pip install --upgrade pip

echo ""
echo "=== Installing requirements ==="
pip install -r requirements.txt

echo ""
echo "=== Running migrations ==="
python manage.py migrate

echo ""
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo ""
echo "=== Build Complete ==="
