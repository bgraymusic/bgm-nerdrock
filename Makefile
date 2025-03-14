SHELL=/bin/bash

ORG=bgm
PROJECT=nerdrock
ENV=sandbox
PREFIX=$(ORG)-$(PROJECT)-$(ENV)


###############################################################################
# Some fancy printing things

BOLD=\033[1m
GREEN=\033[32m
NORMAL=\033[0m
define DO
	printf "$(BOLD)($@)> $(NORMAL)$1$2$3$4$5$6$7$8$9… "
endef
DONE=printf "$(GREEN)done.$(NORMAL)\n"


###############################################################################
# Directory and file lists for building web and lambda artifacts

WEB_DIR := ./web
WEB_SRCS := ./web/.well-known/atproto-did ./web/favicon.ico \
	$(shell find $(WEB_DIR) -name '*.html' -or -name '*.css' -or -name '*.js' -or \
	-name '*.jpg' -or -name '*.png' -or -name '*.svg' -or -name '*.gif' )

LAMBDA_RUNTIME_DIR := ./api/runtime
LAMBDA_SRCS := pyproject.toml api/__init__.py api/config.yml \
	$(shell find $(LAMBDA_RUNTIME_DIR) -name '*.py' -or -name '*.yml' -or -name '*.json')


###############################################################################
# Build web package into assets directory

assets/$(PREFIX)-web.zip: $(WEB_SRCS)
	mkdir -p assets
	$(call DO,Packaging web directory);\
	cd web;zip -qr ../assets/$(PREFIX)-web.zip *;cd ..;\
	$(DONE)
web: assets/$(PREFIX)-web.zip


###############################################################################
# Build lambdas package into assets directory

assets/$(PREFIX)-lambdas.zip: $(LAMBDA_SRCS)
	mkdir -p assets
	$(call DO,Packaging lambda directory);\
	rm -rf pkg;\
	pip install --platform manylinux1_x86_64 --platform manylinux2014_x86_64 --only-binary=:all: --upgrade --force-reinstall . -t pkg;\
	cd pkg; zip -qr ../assets/$(PREFIX)-lambdas *; cd ..;\
	$(DONE)
lambdas: assets/$(PREFIX)-lambdas.zip


clean:
	@$(call DO,Removing artifacts);\
	rm -rf build *.egg-info dist pkg cdk.out assets/*-web.zip assets/*-lambdas.zip .venv*;\
	$(DONE)

.PHONY: web lambdas clean

.SILENT$(VERBOSE):
