# https://www.gnu.org/software/make/manual/html_node/Makefile-Conventions.html

SHELL = /bin/bash

.ONESHELL:
.SUFFIXES:

LIB = example_app
PACKAGE = serverless-fast-api

clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov prof report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

docker-build: clean
	./scripts/poetry_requirements.py > requirements.txt
	docker build . -t $(PACKAGE)
	rm requirements.txt

docker-run: docker-build
	docker run --rm -p 8080:8080 $(PACKAGE)

docker-shell: docker-build
	docker run -it --rm $(PACKAGE) /bin/bash

make app-run:
	@poetry run uvicorn example_app.main:app --port 8080 --reload

flake8: clean
	@poetry run flake8 --ignore=E501 $(LIB)

format: clean
	@poetry run black $(LIB) tests scripts

init: poetry
	# Install the latest project dependencies (ignore the lock file)
	@source "$(HOME)/.poetry/env"
	@poetry run pip install --upgrade pip
	@poetry install -v --no-interaction

lint: clean
	@poetry run pylint --disable=missing-docstring tests
	@poetry run pylint $(LIB)

test: clean
	@poetry run pytest -q -n auto -r f --durations=10 --show-capture=no tests

test-ci: clean
	@poetry run pytest \
		-m "not s3_live" \
		-W ignore::DeprecationWarning \
		--cov-config .coveragerc \
		--verbose \
		--cov-report term \
		--cov-report xml \
		--cov=$(LIB) tests

typehint: clean
	@poetry run mypy --follow-imports=skip $(LIB) tests

package: clean
	@poetry check
	@poetry build

package-check: package
	@poetry check

poetry:
	@if ! which poetry > /dev/null; then \
		curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py -o /tmp/get-poetry.py; \
		python /tmp/get-poetry.py; \
	fi

.PHONY: clean coverage docs flake8 format init lint test typehint package package-check package-test publish poetry
