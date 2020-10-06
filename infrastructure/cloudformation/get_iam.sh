#!/bin/bash

#  This requires awscli 2.x for YAML outputs

mkdir -p iam_roles

if [ ! -f roles.json ]; then
    aws iam list-roles --output json > iam_roles/roles.json
fi

app_roles=$(jq '.Roles[].RoleName' iam_roles/roles.json | sed -n '/app/s/"//gp')

for role in ${app_roles}; do
    echo "$role"
    aws iam get-role --role-name "$role" --output json > "iam_roles/${role}.json"
    aws iam list-attached-role-policies --role-name "$role" --output json > "iam_roles/${role}_policies.json"

    rm -f "iam_roles/${role}_policy_docs.json"
    rm -f "iam_roles/${role}_policy_docs.yaml"
    policies=$(jq '.AttachedPolicies[].PolicyArn' "iam_roles/${role}_policies.json" | sed 's/"//g')
    for policy in $policies; do
        echo "    $policy"
        policy_ver=$(aws iam get-policy --policy-arn "$policy" | jq '.Policy.DefaultVersionId' | sed 's/"//g')

        aws iam get-policy-version \
          --policy-arn "$policy" --version-id "$policy_ver" \
          --output json >> "iam_roles/${role}_policy_docs.json"

        echo "--- " >> "iam_roles/${role}_policy_docs.yaml"
        aws iam get-policy-version \
          --policy-arn "$policy" --version-id "$policy_ver" \
          --output yaml >> "iam_roles/${role}_policy_docs.yaml"
    done
done
