SHELL := /bin/bash
dirname := $(notdir $(patsubst %/,%,$(CURDIR)))
project_name = eligibility-signposting-api

list:
	@grep '^[^#[:space:]].*:' Makefile

build:
	docker compose -f docker-compose.yaml build

tag-service-image:
		$(eval IMAGE_ID=$(shell docker images -q sandbox-combined-service:latest))
		@if [ -z "$(IMAGE_ID)" ]; then \
				echo "ERROR: No image ID found for sandbox-combined-service:latest. Did you build it?"; \
				exit 1; \
		fi
		docker tag $(IMAGE_ID) 958002497996.dkr.ecr.eu-west-2.amazonaws.com/eligibility-signposting-api:latest
		@echo "Tagged image $(IMAGE_ID) as 958002497996.dkr.ecr.eu-west-2.amazonaws.com/eligibility-signposting-api:latest"

build-and-tag:
		make build
		make tag-service-image

proxygen-docker-login: # Login to Proxygen Docker registry
	make -C .. setup-proxygen-credentials
	proxygen docker get-login | bash

publish-to-docker-repo:
	proxygen-docker-login
	docker push 958002497996.dkr.ecr.eu-west-2.amazonaws.com/eligibility-signposting-api:latest

build-and-publish-sandbox-image:
	make build-and-tag
	make publish-to-docker-repo

deploy-sandbox-spec:
	make -C .. construct-spec APIM_ENV=sandbox
	proxygen instance deploy sandbox eligibility-signposting-api ./build/specification/sandbox/eligibility-signposting-api.yaml

up: build
	docker compose -f docker-compose.yaml up -d

down:
	docker compose -f docker-compose.yaml down

clean:
	rm -rf ./node_modules

install:
	npm install --dev

update:
	npm update

spec:
	mkdir -p specification
	make -C .. construct-spec APIM_ENV=sandbox
	make -C .. generate-sandbox-spec

test:
	UPSTREAM_HOST=test poetry run pytest

.PHONY: build run spec test
