# syntax=docker/dockerfile:1.0.2-experimental
# the above line is necessary, not a comment, do not delete!
# you must have a local environment variable of DOCKER_BUILDKIT=1 for this to work!

# For more information about this base image, see
# https://hub.docker.com/r/lambci/lambda
FROM lambci/lambda:build-python3.7

ENV PYTHONDONTWRITEBYTECODE=true

RUN --mount=type=ssh \
    mkdir -p ~/.ssh && \
    ssh-keyscan -H github.com >> ~/.ssh/known_hosts && \
    ssh-keyscan -H gitlab.com >> ~/.ssh/known_hosts

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python \
    && poetry --version

RUN curl -o jq-linux64 -sSL https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 \
    && mv jq-linux64 /usr/local/bin/jq \
    && chmod a+x /usr/local/bin/jq \
    && jq --version

# The layer_builds.sh should be the CMD, but it's not explicit (yet)
COPY layer_builds.sh layer_create_zip.sh layer_size.sh ./
