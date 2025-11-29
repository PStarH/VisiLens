#!/bin/bash
set -e

echo "🚀 Starting VisiLens v0.2.0 Build Protocol..."

# 1. Build Frontend
echo "📦 Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# 2. Prepare Static Assets
echo "📂 Copying assets to vdweb/static..."
mkdir -p vdweb/static
find vdweb/static -mindepth 1 -delete
cp -r frontend/dist/* vdweb/static/

# 3. Build Python Package
echo "🐍 Building Python Package..."
python -m pip install --upgrade build
rm -rf dist/*
python -m build

echo "✅ Build Complete! Artifacts are in dist/"
