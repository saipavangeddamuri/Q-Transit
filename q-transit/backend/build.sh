#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing backend dependencies..."
pip install -r requirements.txt

echo "Backend build completed successfully."
