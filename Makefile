SHELL=/bin/bash

ORG=bgm
PROJECT=nerdrock
ENV=sandbox
PREFIX=$(ORG)-$(PROJECT)-$(ENV)
STACK=$(PREFIX)-stack
MIN_BOOTSTRAP_VER=25
BOLD=$$([ -t 1 ] && tput bold)
GREEN=$$([ -t 1 ] && tput setaf 2)
NORMAL=$$([ -t 1 ] && tput sgr0)
TARGET=$(BOLD)($@)> $(NORMAL)
define DO
	printf "$(TARGET)$1$2$3$4$5$6$7$8$9… "
endef
DONE=printf "$(GREEN)done.$(NORMAL)\n"
define SUCCESS
$(GREEN)$1$2$3$4$5$6$7$8$9$(NORMAL)
endef
ENDL=printf "\n"
define SETUP_VENV
	$(call DO,Creating venv_$(1));python3 -m venv .venv_$(1);$(DONE);\
	$(call DO,Activating venv_$(1));source .venv_$(1)/bin/activate;$(DONE);\
	$(call DO,Uninstalling all extant modules);pip -qqq uninstall -y -r <(pip freeze) 2> /dev/null;$(DONE);\
	$(call DO,Purging cache);pip -qqq cache purge;$(DONE);\
	$(call DO,Updating pip);pip -qqq install --upgrade pip;$(DONE);\
	$(call DO,Installing dependencies);pip -qqq install '.[$(1)]';$(DONE)
endef
define TEARDOWN_VENV
	printf "$(BOLD)($@)> $(NORMAL)Tearing down venv_$(1)… ";deactivate;sleep 2;rm -rf .venv_$(1);$(DONE)
endef

WEB_DIR := ./web
WEB_SRCS := ./web/.well-known/atproto-did ./web/favicon.ico \
	$(shell find $(WEB_DIR) -name '*.html' -or -name '*.css' -or -name '*.js' -or \
	-name '*.jpg' -or -name '*.png' -or -name '*.svg' -or -name '*.gif' )

LAMBDA_RUNTIME_DIR := ./api/runtime
LAMBDA_SRCS := pyproject.toml api/__init__.py api/config.yml \
	$(shell find $(LAMBDA_RUNTIME_DIR) -name '*.py' -or -name '*.yml' -or -name '*.json')

deploy: bootstrap
	@$(call DO,Deploying stack $(STACK));$(ENDL);\
	$(call SETUP_VENV,cdk);\
		$(call DO,Deploying with ENV=$(ENV));$(ENDL);\
		cert=$$(aws acm list-certificates --query "CertificateSummaryList[?contains(SubjectAlternativeNameSummaries, '*.briangraymusic.com')].CertificateArn" --output text);\
		$$(command -v unbuffer) cdk deploy --require-approval never --c ENV=$(ENV) -c CERT="$$cert" 2>&1 | tee /dev/stderr | grep -q "AWS::DynamoDB::Table";\
		if [ $$? == 0 ]; then\
			$(call DO,Table changes found; finding the database refresh function);\
			function_name=$$(aws cloudformation describe-stacks --stack-name $(STACK)\
				--query "Stacks[0].Outputs[?contains(OutputKey,'DatabaseLambdaName')].OutputValue" --output text);\
			$(DONE);\
			$(call DO,Found function $${function_name}, refreshing data from Bandcamp);\
			aws lambda invoke --function-name $$function_name /dev/stdout;\
			$(DONE);\
		fi;\
	$(call TEARDOWN_VENV,cdk);\
	printf "$(TARGET)$(call SUCCESS,Deployment complete.)\n"

undeploy: bootstrap
	@$(call DO,Deleting stack $(STACK));\
	$(call SETUP_VENV,cdk);\
		$(call DO,Undeploying with ENV=$(ENV));$(ENDL);\
		cert=$$(aws acm list-certificates --query "CertificateSummaryList[?contains(SubjectAlternativeNameSummaries, '*.briangraymusic.com')].CertificateArn" --output text);\
		cdk destroy -f -c ENV=$(ENV) -c CERT="$$cert" --stack-name $(STACK);\
		$(DONE);\
	$(call TEARDOWN_VENV,cdk);\
	printf "$(TARGET)$(call SUCCESS,Undeployment complete.)\n"

synth: bootstrap
	@$(call DO,Synthesizing stack $(STACK));$(ENDL);\
	$(call SETUP_VENV,cdk);\
		$(call DO,Synthesizing with ENV=$(ENV));\
		cert=$$(aws acm list-certificates --query "CertificateSummaryList[?contains(SubjectAlternativeNameSummaries, '*.briangraymusic.com')].CertificateArn" --output text);\
		$$(command -v unbuffer) cdk synth -q --require-approval never -c ENV=$(ENV) -c CERT="$$cert";\
		$(DONE);\
	$(call TEARDOWN_VENV,cdk);\
	printf "$(TARGET)$(call SUCCESS,Synthesis complete;) find template in cdk.out\n"

test:
	@$(call SETUP_VENV,test);pytest;$(call TEARDOWN_VENV,test)

$(PREFIX)-web.zip: $(WEB_SRCS)
	@$(call DO,Packaging web directory);\
	cd web;zip -qr ../$(PREFIX)-web.zip *;cd ..;\
	$(DONE)
web: $(PREFIX)-web.zip

$(PREFIX)-lambdas.zip: $(LAMBDA_SRCS)
	@$(call DO,Packaging lambda directory);\
	rm -rf pkg;\
	pip -qqq install --platform manylinux1_x86_64 --platform manylinux2014_x86_64 --only-binary=:all: --upgrade . -t pkg;\
	cd pkg; zip -qr ../$(PREFIX)-lambdas *; cd ..;\
	$(DONE)
lambdas: $(PREFIX)-lambdas.zip

bootstrap: $(PREFIX)-web.zip $(PREFIX)-lambdas.zip
	@cdk_bs_needed=false;\
	bs_ver=$$(aws cloudformation describe-stacks --stack-name CDKToolkit --query "Stacks[].Outputs[?OutputKey == 'BootstrapVersion'].OutputValue" --output text 2> /dev/null);\
	if [ -z $$bs_ver ]; then\
		$(call DO,CDK not bootstrapped yet, bootstrapping);cdk_bs_needed=true;\
	elif [ $$bs_ver -lt 25 ]; then\
		$(call DO,CDK bootstrap is old, updating);cdk_bs_needed=true;\
	else\
		printf "$(TARGET)$(call SUCCESS,CDK already bootstrapped.)\n";\
	fi;\
	if [ cdk_bs_needed == true ]; then\
		@$(call SETUP_VENV,cdk);\
			cdk bootstrap -c ENV=$(ENV);\
		$(call TEARDOWN_VENV,cdk);\
		$(DONE);\
	fi;\
	if [ $$(aws s3api list-buckets --query "Buckets[?Name=='$(ORG)-$(PROJECT)-secrets'] | length(@)") == 0 ]; then\
		$(call DO,Bootstrapping skeleton secrets bucket & yml with encryption key);\
		$(call SETUP_VENV,bootstrap);\
			key=$$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode("utf-8"))');\
			printf "badges:\n\tencryptionKey: %s" "$$key" > secrets.yml;\
			aws s3api create-bucket --bucket $(ORG)-$(PROJECT)-secrets;\
			aws s3 cp secrets.yml s3://$(ORG)-$(PROJECT)-secrets/;\
		$(call TEARDOWN_VENV,bootstrap);\
		rm secrets.yml;\
		$(DONE);\
	else\
		printf "$(TARGET)$(call SUCCESS,Secrets bucket already bootstrapped.)\n";\
	fi;\

clean:
	@$(call DO,Removing artifacts);\
	rm -rf build *.egg-info dist pkg cdk.out *-web.zip *-lambdas.zip .venv*;\
	$(DONE)

.PHONY: web lambdas test
