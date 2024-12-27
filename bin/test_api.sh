#!/bin/bash

python3 -m venv .venv_test
source .venv_test/bin/activate
pip uninstall -y -r <(pip freeze)
pip cache purge
pip install --upgrade pip
pip install '.[test]'
pytest
deactivate
