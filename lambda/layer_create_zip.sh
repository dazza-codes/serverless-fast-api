#!/bin/bash

clean_python_metadata () {
  site=$1
  echo "Cleaning python package metadata from $site ..."
  find "$site" -type d -name '*.dist-info' -exec rm -rf {} +
  find "$site" -type d -name '*.egg-info' -exec rm -rf {} +
}

clean_python_packages () {
  site=$1
  echo "Optimizing python package installations in $site ..."
  find "$site" -type d -name '__pycache__' -exec rm -rf {} +
  find "$site" -type d -name 'tests' -exec rm -rf {} +
  find "$site" -type f -name '*.py[co]' -exec rm -f {} +
}

strip_binary_libs() {
  site=$1
  echo "Optimizing binary libraries *.so* in $site ..."
  find "$site" -type f -name '*.so*' -exec strip {} \;
}

strip_pydantic_binaries () {
  site=$1
  # This can reduce pydantic from 30Mb down to 6Mb
  if [ -d "${site}/pydantic" ]; then
    echo "Optimizing pydantic binaries in $site/pydantic ..."
    find "${site}/pydantic" -type f -name '*.cpython*.so*' -exec strip {} \;
  fi
}


# The lambda runtime should provide the following packages,
# so it should be possible to remove them all from layers.
#
# /var/runtime/boto3-1.12.49.dist-info
# /var/runtime/botocore-1.15.49.dist-info
# /var/runtime/docutils-0.15.2.dist-info
# /var/runtime/jmespath-0.9.5.dist-info
# /var/runtime/python_dateutil-2.8.1.dist-info  ->  dateutil
# /var/runtime/s3transfer-0.3.3.dist-info
# /var/runtime/six-1.14.0.dist-info
# /var/runtime/urllib3-1.25.9.dist-info

clean_aws_packages () {
  site=$1
  echo "Cleaning AWS SDK packages from $site ..."
  find "$site" -type d -name 'boto3' -exec rm -rf {} +
  find "$site" -type d -name 'boto3-*.dist-info' -exec rm -rf {} +
  find "$site" -type d -name 'botocore' -exec rm -rf {} +
  find "$site" -type d -name 'botocore-*.dist-info' -exec rm -rf {} +
  find "$site" -type d -name 'dateutil' -exec rm -rf {} +
  find "$site" -type d -name 'python_dateutil-*.dist-info' -exec rm -rf {} +
  find "$site" -type d -name 'docutils' -exec rm -rf {} +
  find "$site" -type d -name 'docutils-*.dist-info' -exec rm -rf {} +
  find "$site" -type d -name 'jmespath' -exec rm -rf {} +
  find "$site" -type d -name 'jmespath-*.dist-info' -exec rm -rf {} +
  find "$site" -type d -name 's3transfer' -exec rm -rf {} +
  find "$site" -type d -name 's3transfer-*.dist-info' -exec rm -rf {} +
  find "$site" -type d -name 'six' -exec rm -rf {} +
  find "$site" -type d -name 'six-*.dist-info' -exec rm -rf {} +
  find "$site" -type d -name 'urllib3' -exec rm -rf {} +
  find "$site" -type d -name 'urllib3-*.dist-info' -exec rm -rf {} +
}

#clean_aws_packages () {
#  # TODO: this doesn't work because pip has no -t (target) or --path
#  #       arguments to uninstall packages (only to install them)
#  site=$1
#  python -m pip uninstall -t "$site" -y boto3
#  python -m pip uninstall -t "$site" -y botocore
#  python -m pip uninstall -t "$site" -y dateutil
#  python -m pip uninstall -t "$site" -y docutils
#  python -m pip uninstall -t "$site" -y jmespath
#  python -m pip uninstall -t "$site" -y s3transfer
#  python -m pip uninstall -t "$site" -y six
#  python -m pip uninstall -t "$site" -y urllib3
#}

## TODO: find a way to archive a package file set
#package_archive () {
#  package=$1
#  python -m pip show --files "${package}" > /tmp/package_files.txt
#  location=$(awk '/Location/ { print $2 }' /tmp/package_files.txt)
#  files=$(grep -E "^\s+" /tmp/package_files.txt | sed "s#${package}#${location}/${package}#g")
#}

# Pin the AWS SDK lambda packages to the provided versions, so
# they can be removed from lambda layers.  The strategy is to
# add the SDK libs as explicit requirements to every layer build
# and then remove them from the build.  The `create_layer_zip`
# function will call `clean_aws_packages` to remove the AWS SDK
# libs listed below.
#
# fix boto3 and botocore to the current lambda layer versions
# https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html
# last checked on 2020-07: boto3-1.12.49 botocore-1.15.49
#
# This could also help to detect when a project dependency requires a version of these
# AWS SDK libs that is different from the lambda versions.  To get this list:
# `ls -1d /var/runtime/*.dist-info` in the lambci container.  These are
# essentially the `boto3` library and the dependency tree it requires.
#
# /var/runtime/boto3-1.12.49.dist-info
# /var/runtime/botocore-1.15.49.dist-info
# /var/runtime/docutils-0.15.2.dist-info
# /var/runtime/jmespath-0.9.5.dist-info
# /var/runtime/python_dateutil-2.8.1.dist-info
# /var/runtime/s3transfer-0.3.3.dist-info
# /var/runtime/six-1.14.0.dist-info
# /var/runtime/urllib3-1.25.9.dist-info

pin_lambda_sdk () {
  requirements_file=$1
  # remove and replace all the AWS SDK libs
  sed -i '/^boto3/d' "${requirements_file}"
  sed -i '/^botocore/d' "${requirements_file}"
  sed -i '/^docutils/d' "${requirements_file}"
  sed -i '/^jmespath/d' "${requirements_file}"
  sed -i '/^python_dateutil/d' "${requirements_file}"
  sed -i '/^s3transfer/d' "${requirements_file}"
  sed -i '/^six/d' "${requirements_file}"
  sed -i '/^urllib3/d' "${requirements_file}"

  cat >> "${requirements_file}" <<REQUIREMENTS
boto3==1.12.49
botocore==1.15.49
docutils==0.15.2
jmespath==0.9.5
python_dateutil==2.8.1
s3transfer==0.3.3
six==1.14.0
urllib3==1.25.9
REQUIREMENTS
}


crash () {
  echo "OOPS - something went wrong!"
  exit 1
}

create_layer_zip () {

  # These pip options do not work:
  # python -m pip install --platform 'linux' --implementation 'py'

  # The destination path should be where AWS lambda unpacks a layer .zip file
  # /opt/python/lib/python3.7/site-packages/

  py_version=$(python --version | grep -o -E '[0-9]+[.][0-9]+')
  py_ver=$(echo "py${py_version}" | sed -e 's/\.//g')

  package_dir=$(mktemp -d -t tmp_python_XXXXXX)
  package_dst=${package_dir}/python/lib/python${py_version}/site-packages
  mkdir -p "$package_dst"
  echo "$package_dst"

  venv_dir=$(mktemp -d -t tmp_venv_XXXXXX)
  python -m pip install virtualenv
  python -m virtualenv --clear "$venv_dir"
  # shellcheck disable=SC1090
  source "$venv_dir/bin/activate"
  echo "$venv_dir"

  pin_lambda_sdk /tmp/requirements.txt

  python -m pip install --no-compile -t "$package_dst" -r /tmp/requirements.txt
  #python -m pip list --path "$package_dst"

  clean_aws_packages "$package_dst"
  clean_python_packages "$package_dst"
  #strip_binary_libs "$package_dst"  # numpy might get broken by strip
  strip_pydantic_binaries "$package_dst"
  python -m pip list --path "$package_dst"
  clean_python_metadata "$package_dst"
  # a pip check is useless because it doesn't support a target path argument
  #python -m pip check -t "$package_dst"
  echo
  echo
  deactivate

  echo "Zipping packages for lambda layer..."
  zip_tmp=${ZIP_TMP:-/tmp/${py_ver}_lambda_layer.zip}
  rm -f "${zip_tmp}"
  pushd "${package_dir}" > /dev/null || crash

  zip -qr9 --compression-method deflate --symlinks "${zip_tmp}" python

  ls "${zip_tmp}" > /dev/null || crash
  unzip -q -t "${zip_tmp}" || crash

  echo "created ${zip_tmp}"
  popd > /dev/null || exit 1

  rm -rf "$package_dir"
  rm -rf "$venv_dir"
}
