SHELL=/bin/bash

ORG=bgm
PROJECT=nerdrock
ENV=sandbox
PREFIX=$(ORG)-$(PROJECT)-$(ENV)
STACK=$(PREFIX)-stack

WEB_DIR := ./web
WEB_SRCS := ./web/.well-known/atproto-did ./web/favicon.ico \
	$(shell find $(WEB_DIR) -name '*.html' -or -name '*.css' -or -name '*.js' -or \
	-name '*.jpg' -or -name '*.png' -or -name '*.svg' -or -name '*.gif' )

LAMBDA_RUNTIME_DIR := ./api/runtime
LAMBDA_SRCS := pyproject.toml api/__init__.py api/config.yml \
	$(shell find $(LAMBDA_RUNTIME_DIR) -name '*.py' -or -name '*.yml' -or -name '*.json')

deploy: $(PREFIX)-web.zip $(PREFIX)-lambdas.zip
	@echo "> Deploying stack $(STACK)…";\
	$$(command -v unbuffer) cdk deploy --require-approval never --context ENV=$(ENV) 2>&1 | tee /dev/stderr | grep -q "AWS::DynamoDB::Table";\
	if [ $$? == 0 ]; then\
		echo "> Table changes found, finding the database refresh function…";\
		function_name=$$(aws cloudformation describe-stacks \
			--stack-name $(STACK) \
			--query "Stacks[0].Outputs[?contains(OutputKey,'DatabaseLambdaName')].OutputValue" \
			--output text);\
		echo "> Found function $${function_name}, refreshing data from Bandcamp…";\
		aws lambda invoke --function-name $$function_name /dev/stdout;\
	fi;\
	echo "> Deployment complete."

undeploy:
	@echo "> Deleting stack $(STACK)…";\
	cdk destroy -f --context ENV=$(ENV) $(STACK);\
	echo "> Done."

test:
	python3 -m venv .venv_test;\
	source .venv_test/bin/activate;\
	pip uninstall -y -r <(pip freeze);\
	pip cache purge;\
	pip install --upgrade pip;\
	pip install '.[test]';\
	pytest;\
	deactivate

$(PREFIX)-web.zip: $(WEB_SRCS)
	cd web;zip -qr ../$(PREFIX)-web.zip *;cd ..

.PHONY: web
web: $(PREFIX)-web.zip

$(PREFIX)-lambdas.zip: $(LAMBDA_SRCS)
	rm -rf pkg
	python3 -m venv .venv_deploy;\
	source .venv_deploy/bin/activate;\
	pip uninstall -y -r <(pip freeze);\
	pip cache purge;\
	pip install --upgrade pip;\
	pip install --platform manylinux1_x86_64 --platform manylinux2014_x86_64 --only-binary=:all: --upgrade . -t pkg;\
	deactivate
	cd pkg; zip -qr ../$(PREFIX)-lambdas *; cd ..

.PHONY: lambdas
lambdas: $(PREFIX)-lambdas.zip

clean:
	rm -rf build *.egg-info dist pkg cdk.out *-web.zip *-lambdas.zip .venv*
