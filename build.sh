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
echo "=== Build Complete ==="
echo "Note: Static files and migrations will run on app startup"
