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
	docker run --rm -p 8000:8000 $(PACKAGE)

docker-shell: docker-build
	docker run -it --rm $(PACKAGE) /bin/bash

make app-run:
	@poetry run uvicorn example_app.main:app --port 8000 --reload

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

poetry:
	@if ! which poetry > /dev/null; then \
		curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py -o /tmp/get-poetry.py; \
		python /tmp/get-poetry.py; \
	fi

.PHONY: clean coverage docs flake8 format init lint test typehint package package-check package-test publish poetry
