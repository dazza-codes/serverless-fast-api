"""
AWS Secrets Manager
-------------------

.. code-block::

    # The default AWS-API client may not use the region where the
    # secret was defined, so the following default may not work.
    secrets: Dict = get_aws_secret("app-secrets")

    # To use a different client in the same region as the secret:
    import boto3
    client = boto3.client(service_name="secretsmanager", region_name="us-east-1")
    secrets: Dict = get_aws_secret("app-secrets", client)

.. seealso::
    https://docs.aws.amazon.com/secretsmanager/latest/userguide/tutorials_basic.html
    https://github.com/aws/aws-secretsmanager-caching-python
    https://github.com/awslabs/secrets-helper

"""

import base64
import json
import os
from typing import Dict

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from .logger import get_logger

LOGGER = get_logger(__name__)


def boto_default_client(
    service_name: str, region_name: str = "us-west-2"
) -> BaseClient:
    region = region_name or os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    return boto3.client(service_name=service_name, region_name=region)


def get_aws_secret(secret_id: str, client: BaseClient = None) -> Dict:
    """
    Retrieve from AWS Secrets Manager

    :param secret_id: secrets name in AWS Secrets Manager
    :param client: an optional AWS botocore client for "secretsmanager";
        a client is created if this is not given.
    :returns: JSON dictionary of keys:values for the specified secret
    """

    if client is None:
        client = boto_default_client("secretsmanager")

    LOGGER.debug(
        "Get secrets using key=%s; region=%s", secret_id, client.meta.config.region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        secret_response = client.get_secret_value(SecretId=secret_id)
    except ClientError as e:
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
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Depending on whether the secret is a string or binary, one of these fields will be
        # populated.
        if "SecretString" in secret_response:
            secret = secret_response["SecretString"]
            return json.loads(secret)
        else:
            # Decrypts secret using the associated KMS CMK.
            secret = base64.b64decode(secret_response["SecretBinary"])
            return json.loads(secret)
