#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PARENT_DIR=$(realpath "${SCRIPT_DIR}/..")


# See also
# https://docs.aws.amazon.com/lambda/latest/dg/limits.html
# - Function and layer storage: 75 GB
# - Deployment package size
#   - 50 MB (zipped, for direct upload)
#   - 250 MB (unzipped, including layers)
#   - 3 MB (console editor)

# AWS lambda bundles the python SDK in lambda layers, but advise that bundling it into
# a layer is a best practice.
# https://aws.amazon.com/blogs/compute/upcoming-changes-to-the-python-sdk-in-aws-lambda/
#
# See also the current versions of botocore in lambda - listed at
# https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html
#
# Also consider what is supported by aiobotocore, see:
# https://github.com/aio-libs/aiobotocore/blob/master/setup.py

# To sync layers to s3
# cp /tmp/*.zip layers/
# aws s3 sync layers/ s3://<your-bucket>/<app>

export PYTHONDONTWRITEBYTECODE=true

clean_python_packages () {
  site=$1
  find "$site" -type d -name '__pycache__' -exec rm -rf {} +
  find "$site" -type d -name 'tests' -exec rm -rf {} +
  #find "$site" -type d -name '*.dist-info' -exec rm -rf {} +
  #find "$site" -type d -name '*.egg-info' -exec rm -rf {} +
  #find "$site" -type d -name 'datasets' -exec rm -rf {} +
}

clean_boto3 () {
  site=$1
  find "$site" -type d -name 'boto3' -exec rm -rf {} +
  find "$site" -type d -name 'botocore' -exec rm -rf {} +
  find "$site" -type d -name 'aiobotocore' -exec rm -rf {} +
}

crash () {
  echo
  echo "OOPS - something went wrong!"
  echo
  exit 1
}

# The destination path should be where AWS lambda unpacks a layer .zip file
prefix="${PREFIX:-/opt}"
dst=${prefix}/python/lib/python${py_version}/site-packages
mkdir -p "${dst}"

#
# Note: similar variable names are in Makefile and terraform/*.tf
#
py_version="${APP_PY_VERSION:-3.7}"
py_ver="${APP_PY_VER:-py37}"

package="${APP_PACKAGE:-serverless-fast-api}"
version="${APP_VERSION:-0.1.0}"

app_name="${package}-${version}"
app_package="${py_ver}-${app_name}-app"
layer_package="${py_ver}-${app_name}-layer"

echo
echo "Building:"
echo "$app_package"
echo "$layer_package"
echo

#
# Application zip
#

pushd "$PARENT_DIR" || crash

make clean
zip_file="/tmp/${app_package}.zip"
rm -f "${zip_file}"
zip -q -r9 --symlinks "${zip_file}" example_app/*
unzip -t "${zip_file}" || crash
echo "created ${zip_file}"
cp -vp "${zip_file}" "${PARENT_DIR}/terraform/"
echo
echo

# TODO: when the app package and the code-dir are in sync,
#       change this to use poetry build and install the package
python ./scripts/poetry_requirements.py > /tmp/requirements.txt

popd || crash

#
# Dependencies layer zip
#

## Use `poetry show -t --no-dev`, `pip freeze` or `pipdeptree` to check poetry installed
## versions and pin common deps to use the same, consistent versions in lambda layers.

pushd "$prefix" || crash
rm -rf "${dst:?}"/*
python -m pip install -t "$dst" -r /tmp/requirements.txt
clean_python_packages "$dst"
python -m pip list --path "$dst"
zip_file="/tmp/${layer_package}.zip"
rm -f "${zip_file}"
zip -q -r9 --symlinks "${zip_file}" python
unzip -q -t "${zip_file}" || crash
echo "created ${zip_file}"
cp -vp "${zip_file}" "${PARENT_DIR}/terraform/"
echo
echo
popd || crash

# TODO: why does this fail to list the zip files - they exist OK - weird?
#echo
#echo "Outputs"
#ls -al "${PARENT_DIR}/terraform/${py_ver}-${app_name}*"
#echo
