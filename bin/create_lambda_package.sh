#!/bin/bash

rm -rf pkg
python3 -m venv tmp_deploy
source tmp_deploy/bin/activate
pip uninstall -y -r <(pip freeze)
pip cache purge
pip install --upgrade pip
pip install --platform manylinux1_x86_64 --platform manylinux2014_x86_64 --only-binary=:all: --upgrade . -t pkg
deactivate
cd pkg
zip -qr ../bgm-nerdrock-experimental-lambdas *
cd ..
# rm -rf pkg
