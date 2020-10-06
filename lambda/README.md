
# AWS Lambda Deployment

The following notes relate to optimized packaging for AWS lambda.
The creation of a lambda layer for some projects is not trivial, for
several reasons:

- library versions and APIs are complicated
- the size of the dependency libraries and restrictions on lambda package size

The builds follow the guidelines from the
[AWS knowledge center](https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-simulated-docker/).
It recommends using the [lambci/lambda](https://hub.docker.com/r/lambci/lambda/) Docker images,
to simulate the live Lambda environment and create a layer that's compatible
with the runtimes that you specify. For more information, see
[lambci/lambda](https://hub.docker.com/r/lambci/lambda/) on the Docker website.
Note that lambci/lambda images are not an exact copy of the Lambda environment
and some files may be missing. The AWS Serverless Application Model (AWS SAM)
also uses the lambci/lambda Docker images when you run `sam local start-api`

## Lambda Limits

See https://docs.aws.amazon.com/lambda/latest/dg/limits.html
- Function and layer storage: 75 GB
- Deployment package size
  - 250 MB (unzipped, including layers)
  -  50 MB (zipped, for direct upload)
  -   3 MB (console editor)

## AWS SDK packages

Use `poetry show -t --no-dev`, `pip freeze` or `pipdeptree` to check poetry installed
versions and pin common deps to use the same, consistent versions in lambda layers.

AWS lambda bundles the python SDK in lambda layers, but they advise that bundling it into
a project layer is a best practice.

- https://aws.amazon.com/blogs/compute/upcoming-changes-to-the-python-sdk-in-aws-lambda/

See also the current versions of botocore in lambda - listed at

- https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html

Also consider what is supported by aiobotocore, see:

- https://github.com/aio-libs/aiobotocore/blob/master/setup.py

release 0.12.0 of aiobotocore uses:

```text
1.15.3 < botocore < 1.15.16
boto3 == 1.12.3
```

To view the packages installed in the [lambci/lambda](https://hub.docker.com/r/lambci/lambda/)
image for python (3.6):

```sh
bash-4.2# ls -1d /var/runtime/*.dist-info
/var/runtime/boto3-1.12.49.dist-info
/var/runtime/botocore-1.15.49.dist-info
/var/runtime/docutils-0.15.2.dist-info
/var/runtime/jmespath-0.9.5.dist-info
/var/runtime/python_dateutil-2.8.1.dist-info
/var/runtime/s3transfer-0.3.3.dist-info
/var/runtime/six-1.14.0.dist-info
/var/runtime/urllib3-1.25.9.dist-info
```

The `layer_create_zip.sh:clean_aws_packages` function will remove all
of these SDK packages from layer zip files.  It might not discriminate
package versions that differ from the SDK versions.

The `lambda/layer_builds.sh` will use the SDK versions provided to
try to pin dependencies to those versions.  For project dependencies
that require incompatible versions, a `pip check` should identify
the problem for that layer during the build.

## Splitting Layers for Large Packages:

There are several large packages common to python projects, such as:

```text
$ du -sh /opt/python/lib/python3.7/site-packages/* | grep -E '^[0-9]*M' | sort
11M	/opt/python/lib/python3.7/site-packages/numba
14M	/opt/python/lib/python3.7/site-packages/numpy
24M	/opt/python/lib/python3.7/site-packages/pandas
32M	/opt/python/lib/python3.7/site-packages/numpy.libs
57M	/opt/python/lib/python3.7/site-packages/llvmlite
```

The `pip show` command can list a package dependencies and
the packages that depend on it, e.g.

```text
$ python -m pip show boto3
Name: boto3
Version: 1.12.49
Summary: The AWS SDK for Python
Home-page: https://github.com/boto/boto3
Author: Amazon Web Services
Author-email: UNKNOWN
License: Apache License 2.0
Location: /opt/conda/envs/app/lib/python3.7/site-packages
Requires: s3transfer, jmespath, botocore
Required-by:
```

The dependency graph can be displayed and explored using
`poetry show -t` and `poetry show -t {package}`.  For example,
the `llvmlite` package is a dependency of `numba`, which is a
dependency of `fastparquet`, which also depends on `pandas`
and therefore `numpy`:

```text
$ poetry show -t fastparquet
fastparquet 0.3.3 Python support for Parquet file format
├── numba >=0.28
│   ├── llvmlite >=0.33.0.dev0,<0.34
│   ├── numpy >=1.15
│   └── setuptools *
├── numpy >=1.11
├── pandas >=0.19
│   ├── numpy >=1.13.3
│   ├── python-dateutil >=2.6.1
│   │   └── six >=1.5
│   └── pytz >=2017.2
├── six *
└── thrift >=0.11.0
    └── six >=1.7.2
```

Using `pipdeptree` can also identify package dependencies, including
reverse dependencies.  For example, it is useful to remove all the packages
that lambda already provides, like `boto3`, and it can help to find
anything that depends on it:

```text
$ pip install pipdeptree
$ pipdeptree --help
$ pipdeptree -r -p boto3
boto3==1.12.49
  - aws-sam-translator==1.25.0 [requires: boto3~=1.5]
    - cfn-lint==0.34.1 [requires: aws-sam-translator>=1.25.0]
      - moto==1.3.14 [requires: cfn-lint>=0.4.0]
  - moto==1.3.14 [requires: boto3>=1.9.201]
  - s3fs==0.3.5 [requires: boto3>=1.9.91]
```

To isolate the dependency tree to only the package libs without any
development libs, it can help to create a clean virtualenv and only
install the required packages.  After initial analysis of the dep-tree,
then install package extras and repeat the analysis.

```
# create and activate a new venv any way you like
$ poetry install  # only required packages
$ pip install pipdeptree
$ pipdeptree -p boto3  # what does boto3 depend on
$ pipdeptree -r -p boto3  # what depends on boto3
```

In a similar way, continue with dependencies of a dependency, such
as the dependencies of boto3 and so on.
