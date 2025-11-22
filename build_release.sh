#!/bin/bash
set -e  # Exit on error

echo "🚀 Starting VisiLens v0.1.0 Build Protocol..."

# 1. Build Frontend
echo "📦 Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# 2. Prepare Static Assets
echo "📂 Copying assets to vdweb/static..."
mkdir -p vdweb/static
# Clean old assets
rm -rf vdweb/static/*
# Copy new assets
cp -r frontend/dist/* vdweb/static/

# 3. Build Python Package
echo "🐍 Building Python Package..."
# Ensure build tool is installed
python -m pip install --upgrade build
python -m build

echo "✅ Build Complete! Artifacts are in dist/"
