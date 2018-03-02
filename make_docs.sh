export PYTHONPATH=$(pwd)
mkdir -p docs_build
sphinx-apidoc --full --force -o docs_build/ kagtcprlib
cp sphinx_config.py docs_build/
cd docs_build/
make html
echo "Copying files output to docs/"
cp -r _build/html/* ../docs
echo DONE
