export PYTHONPATH="$(pwd)"
mkdir -p docs
cd docs_src
make html
echo "Copying output to docs/"
cp -r _build/html/* ../docs
touch ../docs/.nojekyll
echo DONE
