export PYTHONPATH=$(pwd)
sphinx-apidoc --full --force -o docs/source kagtcprlib
cp docs/conf.py docs/source
cd docs/source
./make.bat html
echo DONE
