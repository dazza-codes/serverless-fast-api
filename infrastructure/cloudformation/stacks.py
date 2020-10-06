#!/usr/bin/env python3
import base64
import json
import logging
import os
import sys
from distutils.util import strtobool
from typing import Dict

import boto3
import botocore
import botocore.exceptions
import typer
from botocore.client import BaseClient
from dataclasses import dataclass

LOGGER = logging.getLogger("stacks")
LOGGER.addHandler(logging.StreamHandler(sys.stdout))
LOGGER.setLevel(logging.INFO)

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-west-2")


@dataclass
class StackConfig:
    name: str
    stage: str
    region_name: str
    data_domain: str
    namespace: str = None
    data_bucket_name: str = None
    stack_namespace: str = None
    stack_name: str = None
    database_name: str = None
    database_admin: str = None

    def __post_init__(self):
        # these should be in prefix-lower-case
        self.namespace = f"{self.name}-{self.stage}"
        self.data_bucket_name = f"{self.name}-data-{self.data_domain}-{self.stage}"

        # These parameters for CloudFormation templates should be in prefixCamelCase
        # - see restrictions on name patterns in template*.yml
        # - no DBInstanceIdentifier is specified so it is easier for CFN to update/replace it
        self.stack_namespace = self.title_words(self.namespace)
        self.stack_name = f"{self.stack_namespace}Stack"
        self.database_name = f"{self.stack_namespace}Db"
        self.database_admin = f"{self.stack_namespace}DbAdmin"

    @staticmethod
    def title_words(dash_string: str) -> str:
        """
        Replace '-.' with the '.' character upper case, e.g.
        this turns 'app-dev' into 'appDev'
        """
        words = dash_string.strip().split("-")
        for i, word in enumerate(words):
            if i > 0:
                words[i] = word.title()
        title_string = "".join(words)
        return title_string

    @staticmethod
    def get_stack_config(
        name: str, stage: str, data_domain: str, region_name: str
    ) -> "StackConfig":
        if not name:
            raise ValueError("name is undefined")

        if not stage:
            raise ValueError("stage is undefined")

        if not data_domain:
            raise ValueError("data_domain is undefined")

        if not region_name:
            region_name = AWS_DEFAULT_REGION

        stack = StackConfig(
            name=name, stage=stage, region_name=region_name, data_domain=data_domain
        )
        return stack


def boto_client(service_name: str, region_name: str = None) -> BaseClient:
    region = region_name or os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    return boto3.client(service_name=service_name, region_name=region)


def bucket_create(config: StackConfig) -> bool:
    bucket_name = config.data_bucket_name
    region_name = config.region_name
    s3_client = boto_client("s3", region_name=region_name)

    try:
        LOGGER.info("Searching for %s in %s", bucket_name, region_name)
        response = s3_client.head_bucket(Bucket=bucket_name)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if status_code and 200 <= status_code < 300:
            LOGGER.info("Bucket exists: %s", bucket_name)
            return True

    except botocore.exceptions.ClientError as err:
        err_code = err.response.get("Error", {}).get("Code", 0)
        if err_code in ["401", "403"]:
            LOGGER.info("Bucket cannot be accessed: %s", bucket_name)
            return False  # it might or might not exist, assume not

        elif err_code == "404":
            LOGGER.info("Bucket creation required for: %s", bucket_name)
            proceed = typer.prompt(f"Bucket creation confirmation: {bucket_name}?", "n")
            if not strtobool(proceed.strip()):
                LOGGER.info("Bucket creation skipped: %s", bucket_name)
                return False

            try:
                bucket_location = {"LocationConstraint": region_name}
                s3_client.create_bucket(
                    Bucket=bucket_name, CreateBucketConfiguration=bucket_location
                )
                waiter = s3_client.get_waiter("bucket_exists")
                waiter.wait(
                    Bucket=bucket_name, WaiterConfig={"Delay": 2, "MaxAttempts": 20}
                )
                LOGGER.info("Bucket creation complete for: %s", bucket_name)
                return True

            except (
                botocore.exceptions.ClientError,
                botocore.exceptions.WaiterError,
            ) as err:
                LOGGER.error(err)
                return False

    return False


def get_aws_secret(secret_id: str, client: BaseClient) -> Dict:
    """
    Retrieve from AWS Secrets Manager

    :param secret_id: secrets name in AWS Secrets Manager
    :param client: an AWS botocore client for "secretsmanager"
    :returns: JSON dictionary of keys:values for the specified secret
    """

    # if client is None:
    #     client = boto_client("secretsmanager")

    LOGGER.debug(
        "Get secrets using key=%s; region=%s", secret_id, client.meta.config.region_name
    )

    try:
        secret_response = client.get_secret_value(SecretId=secret_id)

    except botocore.exceptions.ClientError as e:
        LOGGER.exception(e)
        if e.response["Error"]["Code"] == "DecryptionFailureException":
            # Secrets Manager can't decrypt the protected secret text using the provided KMS
            # key. Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InternalServiceErrorException":
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            # You provided a parameter value that is not valid for the current state of the
            # resource. Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise e
    else:
        if "SecretString" in secret_response:
            secret = secret_response["SecretString"]
            return json.loads(secret)
        elif "SecretBinary" in secret_response:
            # Decrypts secret using the associated KMS CMK.
            secret = base64.b64decode(secret_response["SecretBinary"])
            return json.loads(secret)
        else:
            raise ValueError("Unknown secret response: %s", secret_response)


app = typer.Typer()


# TODO: use one top-level command to gather all the params?
#       - https://typer.tiangolo.com/tutorial/commands/callback/
# TODO: use a config-file or simple-settings for the required params?


@app.command()
def create_bucket(
    name: str = "app",
    stage: str = "test",
    data_domain: str = "domain",
    region_name: str = AWS_DEFAULT_REGION,
):
    # there is no delete-bucket yet but might be enabled only for `test` stage
    stack = StackConfig.get_stack_config(
        name=name, stage=stage, data_domain=data_domain, region_name=region_name
    )
    typer.echo(f"Bucket: {stack.data_bucket_name}")
    result = bucket_create(stack)
    typer.echo(f"Bucket exists: {result}")


@app.command()
def stack_config(
    name: str = "app",
    stage: str = "test",
    data_domain: str = "domain",
    region_name: str = AWS_DEFAULT_REGION,
):
    stack = StackConfig.get_stack_config(
        name=name, stage=stage, data_domain=data_domain, region_name=region_name
    )
    typer.echo(stack)


@app.command()
def stack_create(
    name: str = "app",
    stage: str = "test",
    data_domain: str = "domain",
    region_name: str = AWS_DEFAULT_REGION,
):
    stack = StackConfig.get_stack_config(
        name=name, stage=stage, data_domain=data_domain, region_name=region_name
    )
    typer.echo(f"Create {stage}")
    typer.echo(stack)


@app.command()
def stack_update(
    name: str = "app",
    stage: str = "test",
    data_domain: str = "domain",
    region_name: str = AWS_DEFAULT_REGION,
):
    stack = StackConfig.get_stack_config(
        name=name, stage=stage, data_domain=data_domain, region_name=region_name
    )
    typer.echo(f"Update {stage}")
    typer.echo(stack)


if __name__ == "__main__":
    app()
