set -e

cd frontend
npm install
npm run build
cd ..

mkdir -p vdweb/static
find vdweb/static -mindepth 1 -delete
cp -r frontend/dist/* vdweb/static/

python -m pip install --upgrade build
rm -rf dist/*
python -m build

echo "Build Complete/"
