#!/usr/bin/env bash

SCRIPT_PATH=$(dirname "$0")
SCRIPT_PATH=$(readlink -f "$SCRIPT_PATH")

ZIP_PATH=${ZIP_PATH:-'/tmp'}
ZIP_PATH=$(readlink -f "$ZIP_PATH")

echo -e "MAX BYTES\t262144000 bytes"
for f in "${ZIP_PATH}"/*.zip; do
    zip_file=$(basename "$f")
    zip_bytes=$(unzip -l "$f" | tail -n1 | awk '{ print $1 }')
    printf "\t\t%9u bytes in %s\n" "$zip_bytes" "$zip_file"
done

# additional details below are often not required
exit
echo

for f in "${ZIP_PATH}"/*.zip; do
    zip_file=$(basename "$f")
    zip_size=$(stat --format '%s' "${f}")
    zip_hash=$(openssl dgst -sha256 -binary "${f}" | openssl enc -base64)
    echo "zip file:    ${zip_file}"
    echo "    size:    ${zip_size}"
    echo "    sha256:  ${zip_hash}"
    echo
done
