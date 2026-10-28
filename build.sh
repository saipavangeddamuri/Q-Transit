#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "==> Step 1: Building React Frontend with Vite..."
cd q-transit/frontend
npm install
npm run build
cd ../..

echo "==> Step 2: Installing Python Backend Dependencies..."
pip install --upgrade pip
pip install -r q-transit/backend/requirements.txt

echo "==> Build finished successfully!"
