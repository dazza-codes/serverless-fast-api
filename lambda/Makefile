# https://www.gnu.org/software/make/manual/html_node/Makefile-Conventions.html
SHELL = /bin/bash

# Tips for writing shell scripts within makefiles:
# - Escape the script's use of $ by replacing with $$
# - Convert the script to work as a single line by inserting ; between commands
# - If you want to write the script on multiple lines, escape end-of-line with \
# - Optionally start with set -e to match make's provision to abort on sub-command failure
# - This is totally optional, but you could bracket the script with () or {} to
#   emphasize the cohesiveness of a multiple line sequence -- note that this is
#   not a typical makefile command sequence

# https://www.gnu.org/software/make/manual/html_node/One-Shell.html
# If .ONESHELL is provided, then only the first line of the recipe
# will be checked for the special prefix characters (‘@’, ‘-’, and ‘+’).
.ONESHELL:
.SUFFIXES:


# For packaging lambda .zip archives, see also
# - https://github.com/aws-samples/aws-lambda-layer-awscli/blob/master/Makefile
#
# From https://github.com/UnitedIncome/serverless-python-requirements/tree/master/lib
#


PY_VERSION=$(shell python --version | grep -o -E '[0-9]+[.][0-9]+')
PY_VER=$(shell echo "py$(PY_VERSION)" | sed -e 's/\.//g')

LIB_NAME=app
LIB_VERSION=$(shell python -c 'import app; print(app.VERSION)')
LIB_PREFIX=$(PY_VER)-$(LIB_NAME)-$(LIB_VERSION)
LIB_PACKAGE=$(LIB_PREFIX).zip
LIB_TMPDIR=/tmp/$(LIB_NAME)

APP_IMAGE=$(LIB_NAME)-lambda-builds

USER_ID=$(shell id --user)
GROUP_ID=$(shell id --group)

docker-build:
	git rev-parse HEAD > version
	DOCKER_BUILDKIT=1 && export DOCKER_BUILDKIT
	docker build -t $(APP_IMAGE) --ssh=default  .
	rm version

docker-shell: docker-build poetry-export
	docker run -it --rm \
		-e LIB_NAME\=$(LIB_NAME) \
		-e LIB_VERSION\=$(LIB_VERSION) \
		-e LIB_PACKAGE\=$(LIB_PACKAGE) \
		-e ZIP_PATH\=$(LIB_TMPDIR) \
		-e USER_ID\=$(USER_ID) \
		-e GROUP_ID\=$(GROUP_ID) \
		-v $(HOME)/.ssh/id_rsa\:/root/.ssh/id_rsa\:z \
		-v $(HOME)/.ssh/known_hosts\:/root/.ssh/known_hosts\:z \
		-v /run/user/$(USER_ID)/keyring/ssh\:/tmp/ssh_sock\:z \
		-e SSH_AUTH_SOCK\=/tmp/ssh_sock \
		-v /tmp:/tmp \
		$(APP_IMAGE) /bin/bash

layer-package: docker-build poetry-export
	docker run -it --rm \
		-e LIB_NAME\=$(LIB_NAME) \
		-e LIB_VERSION\=$(LIB_VERSION) \
		-e LIB_PACKAGE\=$(LIB_PACKAGE) \
		-e ZIP_PATH\=$(LIB_TMPDIR) \
		-e USER_ID\=$(USER_ID) \
		-e GROUP_ID\=$(GROUP_ID) \
		-v $(HOME)/.ssh/id_rsa\:/root/.ssh/id_rsa\:z \
		-v $(HOME)/.ssh/known_hosts\:/root/.ssh/known_hosts\:z \
		-v /run/user/$(USER_ID)/keyring/ssh\:/tmp/ssh_sock\:z \
		-e SSH_AUTH_SOCK\=/tmp/ssh_sock \
		-v /tmp:/tmp \
		$(APP_IMAGE) ./layer_builds.sh
	ls -al $(LIB_TMPDIR)/*.zip
	echo
	ZIP_PATH=$(LIB_TMPDIR) ./layer_size.sh
	echo

layer-size: layer-tmpdir
	ls -al $(LIB_TMPDIR)/*.zip
	echo
	ZIP_PATH=$(LIB_TMPDIR) ./layer_size.sh
	echo

layer-publish: layer-tmpdir
	AWS_DEFAULT_REGION=$(AWS_DEFAULT_REGION) \
	AWS_ACCOUNT=$(AWS_ACCOUNT) \
	LIB_PREFIX=$(LIB_PREFIX) \
	ZIP_PATH=$(LIB_TMPDIR) \
	./layer_publish.sh

layer-tmpdir:
	mkdir -p $(LIB_TMPDIR)

# Export the project dependencies as a requirements.txt file, without
# any editable dependencies, and export the project library with no-deps
poetry-export: layer-tmpdir
	cd ..
	EXPORT_ARGS='--without-hashes --format requirements.txt --output requirements.txt'

	poetry export $${EXPORT_ARGS}
	sed -e 's/^-e //g' requirements.txt > $(LIB_TMPDIR)/requirements.txt

	# TODO: if extras are used as optional dependencies in the pyproject.toml
	#poetry export $${EXPORT_ARGS} --extras {extra-A}
	#sed -e 's/^-e //g' requirements.txt > $(LIB_TMPDIR)/requirements_{extra-A}.txt

	rm -f requirements.txt
	rm -rf dist/*
	poetry build
	wheel=$$(ls -1t dist/*.whl | head -n1)
	rm -rf $(LIB_TMPDIR)/project-no-deps
	python -m pip install --no-compile --no-deps -t $(LIB_TMPDIR)/project-no-deps "$${wheel}"


.PHONY: docker-build docker-shell layer-package layer-size layer-publish layer-tmpdir poetry-export
