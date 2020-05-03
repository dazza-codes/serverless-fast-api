# fastapi-aws-lambda-example

For a detailed guide on how to deploy a fastapi application with AWS API Gateway
and AWS Lambda check [this](https://iwpnd.pw/articles/2020-01/deploy-fastapi-to-aws-lambda)


# Getting Started

```shell script
git clone https://github.com/dazza-codes/serverless-fast-api.git
cd serverless-fast-api
poetry install
poetry shell
pytest tests
```

### Docker

```shell script
make docker-build
make docker-run
```

In another terminal, try to `curl` the endpoints, e.g.

```shell script
curl http://127.0.0.1:8080/ping
curl http://127.0.0.1:8080/api/v1/example
```

A python example for the same thing is in:

```shell script
python scripts/example.py
```

That example script depends on `requests`, which is in the dev-dependencies.

### Using git pre-commit

Install [pre-commit](https://pre-commit.com/); it should be bundled by
poetry in the dev-dependencies.  Confirm it's available:

```shell script
$ pre-commit --version
pre-commit 2.3.0
```

It's configured by a file named `.pre-commit-config.yaml` and enabled by
running `pre-commit install`.
