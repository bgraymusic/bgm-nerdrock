SHELL=/bin/bash

LAMBDA_RUNTIME_DIR := ./api/runtime
LAMBDA_SRCS := pyproject.toml api/__init__.py api/config.yml \
	$(shell find $(LAMBDA_RUNTIME_DIR) -name '*.py' -or -name '*.yml' -or -name '*.json')

bgm-nerdrock-local-lambdas.zip: $(LAMBDA_SRCS)

lambdas: bgm-nerdrock-local-lambdas.zip
	rm -rf pkg
	python3 -m venv .venv_deploy
	source .venv_deploy/bin/activate
	pip uninstall -y -r <(pip freeze)
	pip cache purge
	pip install --upgrade pip
	pip install --platform manylinux1_x86_64 --platform manylinux2014_x86_64 --only-binary=:all: --upgrade . -t pkg
	deactivate
	cd pkg; zip -qr ../bgm-nerdrock-local-lambdas *; cd ..
