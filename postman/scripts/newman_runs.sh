#!/bin/bash

# After running this script, use diff to compare the runtimes, e.g.
#
# diff logs/2020-06-23/postman_api_run_2020-06-23_01.log logs/2020-06-23/postman_api_run_2020-06-23_02.log
#

#
# Gather arguments

usage() {
    cat <<- USAGE
usage: $0 [options]

options:
--runs            number of runs (defaults to 3)
--timefmt         +FORMAT in 'man date' including the '+'
                  (defaults to '+%Y%m%dT%H%MZ')
-h  | --help
USAGE
}

# defaults
RUNS=3
FILE_TIMEFMT='+%Y%m%dT%H%MZ'

while [ "$1" != "" ]; do
    case $1 in
        --runs )        shift
                        RUNS=$1
                        ;;
        --timefmt )     shift
                        FILE_TIMEFMT=$1
                        ;;
        -h | --help )   usage
                        exit
                        ;;
        * )             usage
                        exit 1
    esac
    shift
done

fail_auth () {
  echo "Failed to get Cognito authentication, check config file values"
  exit 1
}

yarn install
yarn test-app-dev-cognito-auth || fail_auth

LOG_DIR_TS=$(date -u +%Y-%m-%d)
output_path="./logs/$LOG_DIR_TS"
mkdir -p "$output_path" || exit 1

FILE_TS=$(date -u "${FILE_TIMEFMT}")

for run in $(seq 1 "$RUNS"); do
  run=$(printf "%02d" "$run")
  output="${output_path}/postman_api_run_${FILE_TS}_${run}.log"
  echo "Saving newman test run into $output"
  yarn test-app-dev-api > "${output}" 2> /dev/null
done
