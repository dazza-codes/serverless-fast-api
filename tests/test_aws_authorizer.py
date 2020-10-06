"""
The auth module and tests are a derivative of various sources of JWT documentation and
source code samples that are covered by the Apache License, Version 2.0.

Copyright 2015-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use
this file except in compliance with the License. A copy of the License is
located at

     http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing permissions and
limitations under the License.
"""
import base64
import datetime
import json
import uuid
from copy import deepcopy
from typing import Dict

import jwcrypto.jwk as jwk
import jwcrypto.jwt as jwt
import pytest
import requests_mock

from example_app import aws_authorizer


# WARNING: moto provides python-jose as a dev-dep, which is not part of
#          the app-deps and should not be used in this test module:
# from jose import jwt
# from jose import jwk


def get_jwk():
    """An RSA JSON Web Key for asymmetric private/public keys
    - json.loads(rsa_jwk.export_private())
    - json.loads(rsa_jwk.export_public())
    """
    params = {"kid": str(uuid.uuid4())}
    return jwk.JWK.generate(kty="RSA", size=512, **params)


def generate_jwt_token(jwt_header, jwt_payload, rsa_jwk):
    token = jwt.JWT(header=jwt_header, claims=jwt_payload, key=rsa_jwk)
    token.make_signed_token(rsa_jwk)
    jwt_token = token.serialize(compact=True)

    # verify the token is OK before using it elsewhere in tests
    jwt_verify = jwt.JWT(jwt=jwt_token, key=rsa_jwk, algs=[jwt_header["alg"]])
    claims = json.loads(jwt_verify.claims)
    for k in jwt_payload:
        assert claims[k] == jwt_payload[k]

    return jwt_token


@pytest.fixture(scope="module")
def rsa_jwk():
    """An RSA JSON Web Key for asymmetric private/public keys
    - json.loads(rsa_jwk.export_private())
    - json.loads(rsa_jwk.export_public())
    """
    return get_jwk()


@pytest.fixture(scope="module")
def cognito_pool_public_keys(rsa_jwk) -> Dict:
    sample_key = {"alg": "RS256", "use": "sig"}
    sample_public_key = json.loads(rsa_jwk.export_public())
    sample_key.update(sample_public_key)

    extra_key = {"alg": "RS256", "use": "sig"}
    extra_jwk = get_jwk()
    extra_public_key = json.loads(extra_jwk.export_public())
    extra_key.update(extra_public_key)

    return {"keys": [sample_key, extra_key]}


@pytest.fixture
def cognito_client_id():
    return str(uuid.uuid4())


@pytest.fixture
def cognito_user_id():
    return str(uuid.uuid4())


@pytest.fixture
def cognito_pool(
    aws_region, cognito_client_id, cognito_moto_pool, cognito_pool_public_keys
):
    cognito_pool_id = cognito_moto_pool["UserPool"]["Id"]
    cognito_pool = aws_authorizer.CognitoPool(
        region=aws_region, id=cognito_pool_id, client_id=cognito_client_id
    )

    with requests_mock.Mocker() as request_mock:
        request_mock.get(cognito_pool.jwks_uri, json=cognito_pool_public_keys)
        yield cognito_pool


@pytest.fixture
def jwt_header(cognito_pool_public_keys) -> Dict:
    # aws documentation indicates the 'kid' is in the header of the JWT
    key = cognito_pool_public_keys["keys"][0]
    headers = {"alg": key["alg"], "kid": key["kid"]}
    return deepcopy(headers)


@pytest.fixture
def jwt_payload_id(cognito_pool, cognito_user_id) -> Dict:
    now = datetime.datetime.utcnow().timestamp()
    payload = {
        "sub": cognito_user_id,
        "aud": cognito_pool.client_id,
        "email_verified": True,
        "token_use": "id",
        "iss": f"https://cognito-idp.{cognito_pool.region}.amazonaws.com/{cognito_pool.id}",
        "cognito:username": "janedoe",
        "given_name": "Jane",
        "email": "janedoe@example.com",
        "auth_time": now,
        "exp": now + datetime.timedelta(minutes=10).total_seconds(),
    }
    return deepcopy(payload)


@pytest.fixture
def jwt_payload_access(cognito_pool, cognito_user_id) -> Dict:
    now = datetime.datetime.utcnow().timestamp()
    payload = {
        "sub": cognito_user_id,
        "device_key": f"{cognito_pool.region}_{cognito_user_id}",
        "cognito:groups": ["admin"],
        "token_use": "access",
        "scope": "aws.cognito.signin.user.admin",
        "iss": f"https://cognito-idp.{cognito_pool.region}.amazonaws.com/{cognito_pool.id}",
        "jti": cognito_user_id,
        "client_id": cognito_pool.client_id,
        "username": "janedoe@example.com",
        "auth_time": now,
        "exp": now + datetime.timedelta(minutes=10).total_seconds(),
    }
    return deepcopy(payload)


@pytest.fixture
def jwt_token_id(jwt_header, jwt_payload_id, rsa_jwk):
    return generate_jwt_token(jwt_header, jwt_payload_id, rsa_jwk)


@pytest.fixture
def jwt_token_access(jwt_header, jwt_payload_access, rsa_jwk):
    return generate_jwt_token(jwt_header, jwt_payload_access, rsa_jwk)


def test_cognito_pool_init(cognito_pool, aws_region):
    assert isinstance(cognito_pool, aws_authorizer.CognitoPool)
    assert cognito_pool.region == aws_region
    assert cognito_pool.id
    assert cognito_pool.client_id


def test_cognito_pool_public_keys(cognito_pool, cognito_pool_public_keys):
    assert (
        cognito_pool.jwks_uri == f"https://cognito-idp."
        f"{cognito_pool.region}.amazonaws.com"
        f"/{cognito_pool.id}/.well-known/jwks.json"
    )
    assert sorted(cognito_pool.jwks["keys"], key=lambda k: k["kid"]) == sorted(
        cognito_pool_public_keys["keys"], key=lambda k: k["kid"]
    )


def test_cognito_pool_jwt_decode(cognito_pool, jwt_token_id, jwt_token_access):
    for jwt_token in [jwt_token_id, jwt_token_access]:
        headers, payload, signature = cognito_pool.jwt_decode(jwt_token)
        assert isinstance(headers, dict)
        assert isinstance(payload, dict)
        assert isinstance(signature, str)


def test_cognito_pool_jwt_public_key(
    cognito_pool, cognito_pool_public_keys, jwt_token_id, jwt_token_access
):
    for jwt_token in [jwt_token_id, jwt_token_access]:
        public_key = cognito_pool.jwt_public_key(jwt_token)
        # it should be the first of the AWS public keys because the test fixture
        # uses the first 'kid' in the jwt_token_id header.
        assert public_key == cognito_pool_public_keys["keys"][0]


def test_cognito_pool_jwt_claims(cognito_pool, jwt_token_id, jwt_payload_id):
    claims = cognito_pool.jwt_claims(jwt_token_id)
    for k in jwt_payload_id:
        assert claims[k] == jwt_payload_id[k]


def test_cognito_pool_jwt_invalid(cognito_pool, jwt_token_id, jwt_payload_id):
    # modify the token payload somehow
    headers, _, signature = jwt_token_id.split(".")
    payload = deepcopy(jwt_payload_id)
    payload["email"] = "someone@example.com"
    payload = base64.urlsafe_b64encode(bytes(json.dumps(payload), encoding="utf-8"))
    jwt_token_id = ".".join([headers, payload.decode("utf-8"), signature])
    with pytest.raises(aws_authorizer.AuthError) as err:
        cognito_pool.jwt_claims(jwt_token_id)

    auth_error = err.value
    assert isinstance(auth_error, aws_authorizer.AuthError)
    assert auth_error.error == "Unauthorized - token failed to verify"
    assert auth_error.status_code == 401


@pytest.fixture
def api_event(cognito_pool):
    api_id = "api-id"  # where to keep this??
    api_stage = "dev"  # where to keep this??
    account_id = "account-id"  # where to keep this??
    api_gateway = f"arn:aws:execute-api:{cognito_pool.region}:{account_id}:{api_id}"
    method_arn = f"{api_gateway}/{api_stage}/GET/api/status"
    event = {"authorizationToken": "a-jwt-token", "methodArn": method_arn}
    return deepcopy(event)


def test_aws_auth_handler_with_missing_jwt(cognito_pool, api_event):
    # the cognito_pool fixture is required to mock the JWKS public keys
    aws_authorizer.COGNITO_POOL = cognito_pool
    del api_event["authorizationToken"]
    with pytest.raises(Exception) as err:
        aws_authorizer.aws_auth_handler(api_event, {})

    # API-GW requires a plain-vanilla Exception
    # auth_error = err.value
    # assert isinstance(auth_error, aws_authorizer.AuthError)
    # assert auth_error.error == "Unauthorized"
    # assert auth_error.status_code == 401
    assert err.value.args[0] == "Unauthorized"


def test_aws_auth_handler_with_invalid_client_id(
    cognito_pool, api_event, jwt_header, jwt_payload_id, rsa_jwk
):
    # the cognito_pool fixture is required to mock the JWKS public keys
    aws_authorizer.COGNITO_POOL = cognito_pool
    jwt_payload_id["aud"] = "invalid-audience"
    assert cognito_pool.client_id != jwt_payload_id["aud"]
    jwt_token = generate_jwt_token(jwt_header, jwt_payload_id, rsa_jwk)
    api_event["authorizationToken"] = jwt_token
    # All 403 responses require a policy document to deny-all.
    auth_policy = aws_authorizer.aws_auth_handler(api_event, {})
    assert auth_policy
    assert auth_policy["principalId"] == "nobody"
    assert isinstance(auth_policy["policyDocument"], dict)
    policy_statement = auth_policy["policyDocument"]["Statement"]
    assert isinstance(policy_statement, list)
    assert [s["Effect"] for s in policy_statement] == ["Deny"]


def test_aws_auth_handler_with_invalid_issuer(
    cognito_pool, api_event, jwt_header, jwt_payload_id, rsa_jwk
):
    # the cognito_pool fixture is required to mock the JWKS public keys
    aws_authorizer.COGNITO_POOL = cognito_pool
    assert jwt_payload_id["aud"] == cognito_pool.client_id  # ensure audience is OK
    jwt_payload_id["iss"] = "invalid-issuer"
    jwt_token = generate_jwt_token(jwt_header, jwt_payload_id, rsa_jwk)
    api_event["authorizationToken"] = jwt_token
    # All 403 responses require a policy document to deny-all.
    auth_policy = aws_authorizer.aws_auth_handler(api_event, {})
    assert auth_policy
    assert auth_policy["principalId"] == "nobody"
    assert isinstance(auth_policy["policyDocument"], dict)
    policy_statement = auth_policy["policyDocument"]["Statement"]
    assert isinstance(policy_statement, list)
    assert [s["Effect"] for s in policy_statement] == ["Deny"]


def test_aws_auth_handler_for_jwt_id(
    cognito_pool, api_event, jwt_payload_id, jwt_token_id
):
    # the cognito_pool fixture is required to mock the JWKS public keys
    aws_authorizer.COGNITO_POOL = cognito_pool
    assert jwt_payload_id["aud"] == cognito_pool.client_id  # check audience
    issuer = jwt_payload_id["iss"]
    assert cognito_pool.region in issuer and cognito_pool.id in issuer

    api_event["authorizationToken"] = jwt_token_id
    auth_policy = aws_authorizer.aws_auth_handler(api_event, {})
    assert auth_policy
    assert auth_policy["principalId"] == jwt_payload_id["email"]
    assert isinstance(auth_policy["policyDocument"], dict)
    policy_statement = auth_policy["policyDocument"]["Statement"]
    assert isinstance(policy_statement, list)
    # this test could be fragile when policies get more specific
    assert [s["Effect"] for s in policy_statement] == ["Allow", "Deny"]


def test_aws_auth_handler_for_jwt_id_bearer(
    cognito_pool, api_event, jwt_payload_id, jwt_token_id
):
    # the cognito_pool fixture is required to mock the JWKS public keys
    aws_authorizer.COGNITO_POOL = cognito_pool
    assert jwt_payload_id["aud"] == cognito_pool.client_id  # check audience
    issuer = jwt_payload_id["iss"]
    assert cognito_pool.region in issuer and cognito_pool.id in issuer

    api_event["authorizationToken"] = f"Bearer {jwt_token_id}"
    auth_policy = aws_authorizer.aws_auth_handler(api_event, {})
    assert auth_policy
    assert auth_policy["principalId"] == jwt_payload_id["email"]
    assert isinstance(auth_policy["policyDocument"], dict)
    policy_statement = auth_policy["policyDocument"]["Statement"]
    assert isinstance(policy_statement, list)
    # this test could be fragile when policies get more specific
    assert [s["Effect"] for s in policy_statement] == ["Allow", "Deny"]


def test_aws_auth_handler_for_jwt_access(
    cognito_pool, api_event, jwt_payload_access, jwt_token_access
):
    # the cognito_pool fixture is required to mock the JWKS public keys
    aws_authorizer.COGNITO_POOL = cognito_pool
    assert jwt_payload_access["client_id"] == cognito_pool.client_id  # check audience
    issuer = jwt_payload_access["iss"]
    assert cognito_pool.region in issuer and cognito_pool.id in issuer

    api_event["authorizationToken"] = jwt_token_access
    auth_policy = aws_authorizer.aws_auth_handler(api_event, {})
    assert auth_policy
    assert auth_policy["principalId"] == jwt_payload_access["username"]
    assert isinstance(auth_policy["policyDocument"], dict)
    policy_statement = auth_policy["policyDocument"]["Statement"]
    assert isinstance(policy_statement, list)
    # this test could be fragile when policies get more specific
    assert [s["Effect"] for s in policy_statement] == ["Allow", "Deny"]
