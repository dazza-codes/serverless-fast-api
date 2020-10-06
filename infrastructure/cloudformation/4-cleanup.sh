#!/bin/bash

#
# Things that cleanup will not remove:
# - aws secrets manager secrets
#   - even when they are deleted manually, they are not removed immediately
# - RDS instances are created with 'delete protection' enabled
#   - disable the delete protection to allow the cloudformation stack to remove an RDS
#

# TODO: may be removed to prevent scripted tear-down mistakes
exit

set -eo pipefail


STACK=app-dev-rds

if [[ $# -eq 1 ]] ; then
    STACK=$1
    echo "Deleting stack $STACK"
fi

aws cloudformation delete-stack --stack-name "$STACK"
echo "Deleted $STACK stack."

if [ -f bucket-name.txt ]; then
    ARTIFACT_BUCKET=$(cat bucket-name.txt)
    if [[ ! $ARTIFACT_BUCKET =~ app-serverless-deploys-[a-z0-9]{16} ]] ; then
        echo "Bucket was not created by this application. Skipping."
    else
        while true; do
            read -rp "Delete deployment artifacts and bucket ($ARTIFACT_BUCKET)? (y/n) " response
            case $response in
                [Yy]* ) aws s3 rb --force "s3://$ARTIFACT_BUCKET"; rm bucket-name.txt; break;;
                [Nn]* ) break;;
                * ) echo "Response must start with y or n.";;
            esac
        done
    fi
fi

rm -f out.yml out.json
