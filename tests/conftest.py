"""
Define common fixtures for testing
"""

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Dict

import boto3
import pytest
from moto import mock_cognitoidp
from moto import mock_s3
from moto import mock_secretsmanager

from example_app.aws_secrets import get_aws_secret
from example_app.settings import Settings


@pytest.fixture(scope="session")
def fixture_path() -> Path:
    return Path(__file__).absolute().parent / "fixtures"


@pytest.fixture
def s3_event_json(fixture_path):
    json_path = fixture_path / "s3_event.json"
    json_text = json_path.read_text()
    return json.loads(json_text)


@pytest.fixture
def aws_region() -> str:
    return "us-west-2"


@pytest.fixture
def app_env(aws_region, monkeypatch):
    # see also:
    # - example_app/settings/*.yaml settings
    # - various .env* files
    monkeypatch.setenv("AWS_DEFAULT_REGION", aws_region)

    # TODO: replace the cognito-env with a moto-mock cognito
    monkeypatch.setenv("API_COGNITO_REGION", aws_region)
    monkeypatch.setenv("API_COGNITO_CLIENT_ID", "testing-client")
    monkeypatch.setenv("API_COGNITO_POOL_ID", "testing-pool-id")


@pytest.fixture
def app_settings(app_env, monkeypatch) -> Settings:
    # By using lazy-loading in Settings, there is no need to set all env values;
    # the Settings object is loaded at runtime, when the pytest sets the env-vars.
    yield Settings()


@pytest.fixture
def aws_moto_credentials(aws_region, monkeypatch):
    """Mocked AWS Credentials for moto."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", aws_region)
    # monkeypatch.setenv("AWS_DEFAULT_PROFILE", "testing")
    # monkeypatch.setenv("AWS_PROFILE", "testing")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    yield


@pytest.fixture
def app_moto_env(aws_moto_credentials, app_env):
    """Mocked AWS Credentials for moto with app env."""
    yield


@pytest.fixture
def app_moto_settings(app_moto_env) -> Settings:
    """Mocked AWS Credentials for moto with app settings."""
    yield Settings()


@pytest.fixture
def s3_moto_client(app_moto_settings, aws_region):
    with mock_s3():
        yield boto3.client("s3", region_name=aws_region)


@pytest.fixture
def app_bucket_name() -> str:
    suffix = str(uuid.uuid4())
    return f"bucket-{suffix}"


@pytest.fixture
def mock_app_bucket(s3_moto_client, app_bucket_name, aws_region) -> str:
    s3_moto_client.create_bucket(
        Bucket=app_bucket_name,
        CreateBucketConfiguration={"LocationConstraint": aws_region},
    )
    print(f"CREATED {app_bucket_name}")

    yield app_bucket_name


@pytest.fixture
def mock_s3_event(app_bucket_name) -> Dict:
    # based on a generic s3 put event
    return {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-west-2",
                "eventTime": "2020-01-01T22:48:25.883Z",
                "eventName": "FOO_EVENT_TYPE",
                "userIdentity": {"principalId": "AWS:ABOAZCMHCRJOF3YWQ36F5:app-func"},
                "requestParameters": {"sourceIPAddress": "154.186.54.126"},
                "responseElements": {
                    "x-amz-request-id": "BADB5DBCD4C1",
                    "x-amz-id-2": "c0wp52Y/71aedgNSbP8Ju2CSox78+sm40FW9n8XO5VA3l/v7Rn2iTTRt91HgFacUBe5T/Omundl9UpsIAFDH6jJBs+",
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "0f972f7b-523d-401b-b2b8-f3ffc42557da",
                    "bucket": {
                        "name": app_bucket_name,
                        "ownerIdentity": {"principalId": "A1ZYG2WCDXS3EZ"},
                        "arn": f"arn:aws:s3:::{app_bucket_name}",
                    },
                    "object": {
                        "key": "foo/bar",
                        "size": 20,
                        "eTag": "23b68380dc2b957a2d07bfed67",
                        "versionId": "w_6Fa42d_3IeJBR1fm2vM3QtBuM",
                        "sequencer": "00B09BBC4C7DB3",
                    },
                },
            }
        ]
    }


@pytest.fixture
def mock_s3_event_put(mock_s3_event) -> Dict:
    event = deepcopy(mock_s3_event)
    event["Records"][0]["eventName"] = "ObjectCreated:Put"
    return event


@pytest.fixture
def mock_s3_event_complete_multipart_upload(mock_s3_event) -> Dict:
    event = deepcopy(mock_s3_event)
    event["Records"][0]["eventName"] = "ObjectCreated:CompleteMultipartUpload"
    return event


@pytest.fixture
def secrets_moto_client(aws_moto_credentials, aws_region):
    with mock_secretsmanager():
        yield boto3.client("secretsmanager", region_name=aws_region)


@pytest.fixture
def cognito_moto_client(aws_moto_credentials, aws_region):
    # https://github.com/spulec/moto/blob/master/tests/test_cognitoidp/test_cognitoidp.py
    with mock_cognitoidp():
        yield boto3.client("cognito-idp", region_name=aws_region)


@pytest.fixture
def cognito_moto_pool(cognito_moto_client, aws_region):
    name = str(uuid.uuid4())
    value = str(uuid.uuid4())
    response = cognito_moto_client.create_user_pool(
        PoolName=name, LambdaConfig={"PreSignUp": value}
    )
    yield response


@pytest.fixture
def cognito_moto_pool_client(cognito_moto_client, cognito_moto_pool):
    user_pool_id = cognito_moto_pool["UserPool"]["Id"]
    yield cognito_moto_client.create_user_pool_client(
        UserPoolId=user_pool_id, ClientName=str(uuid.uuid4())
    )


@pytest.fixture
def app_ro_secrets_name() -> str:
    return "app-rds-readonly"


@pytest.fixture
def app_rw_secrets_name() -> str:
    return "app-rds-write"


@pytest.fixture
def app_rds_secrets() -> Dict:
    return {
        "username": "app_ro",
        "password": "app_passwd",
        "engine": "postgres",
        # "engine": "postgresql",  # aws uses:  "Engine": "postgres"
        "host": "app-dev.stuff.us-west-2.rds.amazonaws.com",
        "port": 5432,
        "dbname": "app_db",
        "dbInstanceIdentifier": "app-dev-db-id",
    }


@pytest.fixture
def app_ro_secrets(app_rds_secrets) -> Dict:
    app_rds_secrets.update({"username": "app_ro", "password": "app_passwd"})
    return app_rds_secrets


@pytest.fixture
def app_rw_secrets(app_rds_secrets) -> Dict:
    app_rds_secrets.update({"username": "app_rw", "password": "app_passwd"})
    return app_rds_secrets


@pytest.fixture
def mock_app_ro_secrets(
    secrets_moto_client, app_ro_secrets_name, app_ro_secrets, mocker
):
    secrets_moto_client.create_secret(
        Name=app_ro_secrets_name, SecretString=json.dumps(app_ro_secrets)
    )
    secrets = get_aws_secret(secret_id=app_ro_secrets_name, client=secrets_moto_client)
    assert secrets
    mocker.patch(
        "example_app.aws_secrets.boto3.client", return_value=secrets_moto_client
    )
    yield secrets


@pytest.fixture
def mock_app_rw_secrets(
    secrets_moto_client, app_rw_secrets_name, app_rw_secrets, mocker
):
    secrets_moto_client.create_secret(
        Name=app_rw_secrets_name, SecretString=json.dumps(app_rw_secrets)
    )
    secrets = get_aws_secret(secret_id=app_rw_secrets_name, client=secrets_moto_client)
    assert secrets
    mocker.patch(
        "example_app.aws_secrets.boto3.client", return_value=secrets_moto_client
    )
    yield secrets
