import json

import pytest
from botocore.exceptions import ClientError

from example_app.aws_secrets import get_aws_secret


def test_mock_app_secrets(secrets_moto_client):
    secret_name = "app-rds"
    app_secret = {
        "username": "app_user",
        "password": "app_passwd",
        "engine": "postgres",
        "host": "app-rds-dev.stuff.us-west-2.rds.amazonaws.com",
        "port": 5432,
        "dbname": "appdb",
        "dbInstanceIdentifier": "app-rds-dev-id",
    }
    secrets_moto_client.create_secret(
        Name=secret_name, SecretString=json.dumps(app_secret)
    )
    secret = get_aws_secret(secret_id=secret_name, client=secrets_moto_client)
    assert secret == app_secret


def test_mock_app_secrets_failure(secrets_moto_client):
    with pytest.raises(ClientError):
        get_aws_secret(secret_id="missing-secret", client=secrets_moto_client)
