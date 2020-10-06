# https://www.gnu.org/software/make/manual/html_node/Makefile-Conventions.html

SHELL = /bin/bash

.ONESHELL:
.SUFFIXES:

LIB = example_app

#
# Note: similar variable names are in scripts/package_lambda.sh and terraform/*.tf
#

AWS_DEFAULT_PROFILE ?= ${AWS_DEFAULT_PROFILE:-default}

APP_PACKAGE = serverless-fast-api
APP_VERSION ?= 0.2.0

# The pyproject.toml defines the python version, keep these in sync
APP_PY_VER = py37
APP_PY_VERSION = 3.7

APP_S3_BUCKET = "app-serverless-deploys"
APP_S3_KEY    = "$(APP_PACKAGE)/$(APP_PACKAGE)-$(APP_VERSION)"


clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov prof report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

docker-build: clean
	@poetry export --without-hashes -f requirements.txt -o requirements.txt
	docker build . -t $(APP_PACKAGE):$(APP_VERSION)
	rm requirements.txt

docker-run: docker-build
	docker run --rm -p 8000:8000 $(APP_PACKAGE):$(APP_VERSION)

docker-shell: docker-build
	docker run -it --rm $(APP_PACKAGE):$(APP_VERSION) /bin/bash

make app-run:
	@poetry run uvicorn example_app.main:app --port 8000 --reload

flake8: clean
	@poetry run flake8 --ignore=E501 $(LIB)

format: clean
	@poetry run black $(LIB) tests scripts *.py

init: poetry
	# Install the latest project dependencies
	@source "$(HOME)/.poetry/env"
	@poetry run pip install --upgrade pip
	@poetry run pip install --upgrade -r requirements-dev.txt
	@poetry install -v --no-interaction

lint: clean
	@poetry run pylint $(LIB)

test: clean
	@poetry run pytest -v \
		--durations=10 \
		--show-capture=no \
		--cov-config .coveragerc \
		--cov-report html \
		--cov-report term \
		--cov=$(LIB) tests

test-ci: clean
	pytest -v \
		--cov-config .coveragerc \
		--cov-report term \
		--cov=$(LIB) tests

typehint: clean
	@poetry run mypy --follow-imports=skip $(LIB) tests

package: clean
	@poetry check
	@poetry build

package-check: package
	@poetry check

lambda-package: clean
	export APP_PACKAGE=$(APP_PACKAGE)
	export APP_VERSION=$(APP_VERSION)
	export APP_PY_VER=$(APP_PY_VER)
	export APP_PY_VERSION=$(APP_PY_VERSION)
	./scripts/package_lambda.sh

lambda-deploy: lambda-package
	cd infrastructure/terraform
	terraform apply -var="app_version=$(APP_VERSION)" -var="aws_default_profile=$(AWS_DEFAULT_PROFILE)"

poetry:
	@if ! which poetry > /dev/null; then \
		curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py -o /tmp/get-poetry.py; \
		python /tmp/get-poetry.py; \
	fi

.PHONY: clean flake8 format init lint test typehint package package-check poetry
