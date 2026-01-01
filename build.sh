#!/usr/bin/env bash
# Force Python 3.11 installation and build
set -e

echo "🔍 Checking Python version..."
python --version

# Verify we're using Python 3.11
PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ ! "$PYTHON_VERSION" =~ ^3\.11 ]]; then
    echo "❌ ERROR: Python $PYTHON_VERSION detected, but Python 3.11 is required!"
    echo "📋 Available Python versions:"
    ls -la /opt/render/project/python/ || true
    exit 1
fi

echo "✅ Python $PYTHON_VERSION confirmed"
echo "📦 Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing requirements..."
pip install -r requirements.txt

echo "✅ Build complete!"
