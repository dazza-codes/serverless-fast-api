#!/bin/bash

SCRIPT_PATH=$(dirname "$0")
SCRIPT_PATH=$(readlink -f "$SCRIPT_PATH")

# shellcheck disable=SC1090
source "$SCRIPT_PATH/layer_create_zip.sh"

py_version=$(python --version | grep -o -E '[0-9]+[.][0-9]+')
py_ver=$(echo "py${py_version}" | sed -e 's/\.//g')

# environment variables should define the following:
#LIB_NAME
#LIB_VERSION
#LIB_REPO
#LIB_PACKAGE
LAYER_PREFIX="${py_ver}-${LIB_NAME}-${LIB_VERSION}"

ZIP_PATH=${ZIP_PATH:-'/tmp'}
ZIP_PATH=$(readlink -f "$ZIP_PATH")
ZIP_TMP="${ZIP_PATH}/${py_ver}_lambda_layer.zip"

REQUIREMENTS_FILE="${ZIP_PATH}/requirements.txt"

if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "ERROR: there is no $REQUIREMENTS_FILE"
  exit 1
fi

crash() {
  echo "OOPS - something went wrong!"
  exit 1
}

#
# Package Default Dependencies
#

cp -p "${ZIP_PATH}/requirements.txt" /tmp/requirements.txt
create_layer_zip
mv "${ZIP_TMP}" "${ZIP_PATH}/${LIB_PACKAGE}" || crash
echo "Created ${ZIP_PATH}/${LIB_PACKAGE}"
echo
echo

#
# Package Optional Extras
#

for f in "${ZIP_PATH}"/requirements_*.txt; do
  if [ -f "${f}" ]; then
    # shellcheck disable=SC2001
    extra=$(echo "${f}" | sed 's/.*requirements_\(.*\)\.txt/\1/')
    cp -p "${f}" /tmp/requirements.txt
    create_layer_zip
    mv "${ZIP_TMP}" "${ZIP_PATH}/${LAYER_PREFIX}-${extra}.zip" || crash
    echo "Created ${ZIP_PATH}/${LAYER_PREFIX}-${extra}.zip"
    echo
    echo
  fi
done


#
# Package - No Dependencies
#
# This section depends on the Makefile recipe for `poetry-export` to
# create /tmp/project installation using
# 	pip install --no-compile --no-deps -t /tmp/project-no-deps {wheel}

py_version=$(python --version | grep -o -E '[0-9]+[.][0-9]+')
py_ver=$(echo "py${py_version}" | sed -e 's/\.//g')
package_dir=$(mktemp -d -t tmp_python_XXXXXX)
package_dst=${package_dir}/python/lib/python${py_version}/site-packages
mkdir -p "$package_dst"
echo "$package_dst"

cp -rf "${ZIP_PATH}"/project-no-deps/* "$package_dst/"

echo "Zipping packages for lambda layer..."
layer_zip="${ZIP_PATH}/${LAYER_PREFIX}-nodeps.zip"
rm -f "${layer_zip}"
pushd "${package_dir}" >/dev/null || crash

zip -rq -D -X -9 -A --compression-method deflate --symlinks "${layer_zip}" python
zip -rq -D -X -9 -A --compression-method deflate --symlinks "${ZIP_PATH}/${LIB_PACKAGE}" python
for f in "${ZIP_PATH}"/requirements_*.txt; do
  if [ -f "${f}" ]; then
    # shellcheck disable=SC2001
    extra=$(echo "${f}" | sed 's/.*requirements_\(.*\)\.txt/\1/')
    extra_zip="${ZIP_PATH}/${LAYER_PREFIX}-${extra}.zip"
    zip -rq -D -X -9 -A --compression-method deflate --symlinks "${extra_zip}" python
  fi
done

ls "${layer_zip}" >/dev/null || crash
unzip -q -t "${layer_zip}" || crash
echo "created ${layer_zip}"
popd >/dev/null || exit 1
rm -rf "$package_dir"
echo
echo

# When this runs in a docker container with the root user, try
# to set permissions and ownership on the .zip artifacts
USER_ID=${USER_ID:-$(id --user)}
GROUP_ID=${GROUP_ID:-$(id --group)}
chmod a+rw "${ZIP_PATH}"/*.zip || true
chown "${USER_ID}":"${GROUP_ID}" "${ZIP_PATH}"/*.zip || true
