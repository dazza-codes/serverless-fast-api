#!/usr/bin/env bash

#set -x

# This script depends on 'jq' to query JSON outputs from the awscli
if ! command -v jq > /dev/null; then
    curl -o jq-linux64 -sSL https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 \
       && mv jq-linux64 "${HOME}/bin/jq" \
       && chmod a+x "${HOME}/bin/jq" \
       && jq --version
fi

SCRIPT_PATH=$(dirname "$0")
SCRIPT_PATH=$(readlink -f "$SCRIPT_PATH")

ZIP_PATH=${ZIP_PATH:-'/tmp'}
ZIP_PATH=$(readlink -f "$ZIP_PATH")

PY_VERSION=$(python --version | grep -o -E '[0-9]+[.][0-9]+')

LIB_PREFIX=${LIB_PREFIX}

LAMBDA_REGION=${AWS_DEFAULT_REGION:-'us-west-2'}
LAMBDA_ACCOUNT=${AWS_ACCOUNT}
LAMBDA_BUCKET=${LAMBDA_BUCKET:-'app-serverless-deploys'}

S3_PREFIX=${S3_PREFIX:-'lambda-layers'}
S3_ROOT=s3://${LAMBDA_BUCKET}/${S3_PREFIX}
echo "$S3_ROOT"

crash () {
  echo "OOPS - something went wrong!"
  exit 1
}

create_or_update_layer () {

  zip_file=$1
  file_name=$(basename "$f")

  layer_name=$(echo "${file_name}" | sed -e 's/.zip//' -e 's/\./-/g')
  layer_arn="arn:aws:lambda:${LAMBDA_REGION}:${LAMBDA_ACCOUNT}:layer:${layer_name}"

  echo
  printf "CHECK LAYER VERSIONS %-40s -> %s\n" "${file_name}" "${layer_arn}"

  # To be smarter at detecting whether an update is required or not
  # - check some sha256 hashes and the zip archive file size
  # - see also https://stackoverflow.com/questions/9714139/why-does-zipping-the-same-content-twice-gives-two-files-with-different-sha1
  # - use the right options on zip to get the same archive for the same content

  ver_json='/tmp/layer_versions.json'
  rm -f "${ver_json}"
  aws lambda list-layer-versions \
    --layer-name "${layer_arn}" \
    --compatible-runtime "python${PY_VERSION}" \
    --no-paginate --output json > "${ver_json}"

  if [ -f "${ver_json}" ] && [ -s "${ver_json}" ]; then
    layer_ver_arn=$(jq '.LayerVersions | sort_by(.Version)[].LayerVersionArn' "${ver_json}" | tail -n1 | sed 's/"//g')

    if [ "${layer_ver_arn}" != "" ]; then
      printf "LATEST LAYER VERSION %-40s -> %s\n" "${file_name}" "${layer_ver_arn}"
      aws lambda get-layer-version-by-arn --arn "${layer_ver_arn}" > "${ver_json}"
      layer_hash=$(jq '.Content.CodeSha256' "${ver_json}" | tail -n1 | sed 's/"//g')
      layer_size=$(jq '.Content.CodeSize'   "${ver_json}" | tail -n1 | sed 's/"//g')

      # https://stackoverflow.com/questions/33825815/how-to-calculate-the-codesha256-of-aws-lambda-deployment-package-before-uploadin
      zip_size=$(stat --format '%s' "${zip_file}")
      zip_hash=$(openssl dgst -sha256 -binary "${zip_file}" | openssl enc -base64)

      echo -e "lambda size:      ${layer_size}"
      echo -e "zip file size:    ${zip_size}"
      echo -e "lambda sha256:    ${layer_hash}"
      echo -e "zip file sha256:  ${zip_hash}"

      [    "${zip_size}" == "${layer_size}" ] \
      && [ "${zip_hash}" == "${layer_hash}" ] \
      && echo -e "SKIP layer publication\n\n" \
      && return

    else
      echo "There is no lambda layer published"
    fi
  else
    echo "There is no lambda layer published"
  fi

  echo
  printf "CREATE or UPDATE LAYER %-40s -> %s\n" "${file_name}" "${layer_arn}"

  aws s3 ls "${S3_ROOT}/${file_name}" > /dev/null || crash
  # shellcheck disable=SC2140
  aws lambda publish-layer-version \
    --region "${LAMBDA_REGION}" \
    --layer-name "${layer_arn}" \
    --description "${layer_name}" \
    --license-info "MIT" \
    --content S3Bucket="${LAMBDA_BUCKET}",S3Key="${S3_PREFIX}/${file_name}" \
    --compatible-runtimes "python${PY_VERSION}"

  echo
}

cp -p "${ZIP_PATH}/${LIB_LIB_PREFIX}"*.zip ./

aws s3 sync ./ "${S3_ROOT}"/ --exclude '*' --include '*.zip' --dryrun

while true; do
    read -r -p "Proceed? (y || n) " yn
    case $yn in
        [Yy]* )
          echo "Proceeding with lambda layer publishing"
          break;;
        [Nn]* )
          echo "Skipping lambda layer publishing"
          exit
          break;;
        * ) echo "Please answer yes or no.";;
    esac
done

aws s3 sync ./ "${S3_ROOT}"/ --exclude '*' --include '*.zip'

for f in *.zip; do
    zip_file=$(basename "$f")
    create_or_update_layer "${zip_file}"
done
