"""
AWS API-Gateway Authorizer
==========================

This authorizer is designed to be attached to an AWS API-Gateway, as a
Lambda authorizer.  It assumes that AWS Cognito is used to authenticate
a client (UI) and then API requests will pass a JSON Web Token to be
validated for authorization of API method calls.  The initial designs
for authorization are very limited in scope.

This auth module is using a recent release of jwcrypto for several reasons:
- jwcrypto supports all JOSE features (see jwt.io libs for python)
- jwcrypto has well designed and documented APIs (python-jose does not)
- it can generate keys as well as other functions for JOSE

.. seealso::
    - https://jwcrypto.readthedocs.io/en/latest/index.html
    - https://auth0.com/docs/tokens/concepts/jwts
    - https://jwt.io/
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html
    - https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
    - https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html

License
*******

This auth module is a derivative of various sources of JWT documentation and
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

# WARNING: moto provides python-jose as a dev-dep, which is not part of
#          the app-deps and should not be used in this auth module, that is,
#          do not use imports like these:
# from jose import jwt
# from jose import jwk

import json
import os
import re
from typing import Dict

import jwcrypto
import jwcrypto.jwk
import jwcrypto.jwt
import requests
from dataclasses import dataclass

from example_app.logger import get_logger

LOGGER = get_logger(__name__)


API_ADMIN_EMAILS = [
    email.strip() for email in os.getenv("API_ADMIN_EMAILS", "").split(",")
]
COGNITO_REGION = os.getenv("API_COGNITO_REGION", "us-west-2")
COGNITO_CLIENT_ID = os.getenv("API_COGNITO_CLIENT_ID")
COGNITO_POOL_ID = os.getenv("API_COGNITO_POOL_ID")


@dataclass
class AuthError(Exception):
    error: str
    status_code: int


@dataclass
class CognitoPool:
    id: str
    client_id: str
    region: str
    _jwks: Dict = None

    @property
    def jwks_uri(self) -> str:
        return "https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json".format(
            self.region, self.id
        )

    @property
    def jwks(self) -> Dict:
        if self._jwks is None:
            LOGGER.debug(self.jwks_uri)
            response = requests.get(self.jwks_uri)
            LOGGER.debug(response)
            response.raise_for_status()
            # use jwcrypto to parse the JWKS (it takes a json string)
            jwks = jwcrypto.jwk.JWKSet.from_json(response.text)
            self._jwks = json.loads(jwks.export())
            LOGGER.debug(self._jwks)
        return self._jwks

    @staticmethod
    def jwt_decode(jwt_token: str):
        try:
            jwt_headers, jwt_payload, jwt_signature = jwt_token.split(".")
            if not isinstance(jwt_headers, str):
                raise AuthError("Unauthorized - JWT is malformed", 401)
            if not isinstance(jwt_payload, str):
                raise AuthError("Unauthorized - JWT is malformed", 401)
            if not isinstance(jwt_signature, str):
                raise AuthError("Unauthorized - JWT is malformed", 401)

            unverified_token = jwcrypto.jwt.JWT(jwt=jwt_token)
            jwt_headers = unverified_token.token.jose_header

            if not isinstance(jwt_headers, dict):
                raise AuthError("Unauthorized - JWT has malformed headers", 401)
            if not jwt_headers.get("alg"):
                raise AuthError("Unauthorized - JWT-alg is not in headers", 401)
            if not jwt_headers.get("kid"):
                raise AuthError("Unauthorized - JWT-kid is not in headers", 401)

            jwt_payload = unverified_token.token.objects["payload"].decode("utf-8")
            jwt_payload = json.loads(jwt_payload)
            if not isinstance(jwt_payload, dict):
                raise AuthError("Unauthorized - JWT has malformed payload", 401)
            if not jwt_payload.get("token_use") in ["id", "access"]:
                raise AuthError("Unauthorized - JWT has malformed payload", 401)

            return jwt_headers, jwt_payload, jwt_signature

        except Exception as err:
            LOGGER.error(err)
            raise AuthError("Unauthorized - JWT is malformed", 401)

    def jwt_public_key(self, jwt_token: str):
        unverified_token = jwcrypto.jwt.JWT(jwt=jwt_token)
        jwt_headers = unverified_token.token.jose_header
        kid = jwt_headers.get("kid")
        if kid is None:
            raise AuthError("Unauthorized - JWT-kid is missing", 401)
        LOGGER.debug(kid)
        for pub_key in self.jwks.get("keys"):
            if kid == pub_key.get("kid"):
                LOGGER.info("JWT-kid has matching public-kid")
                return pub_key
        raise AuthError("Unauthorized - JWT-kid has no matching public-kid", 401)

    def jwt_claims(self, jwt_token: str):
        try:
            public_key = self.jwt_public_key(jwt_token)
            public_jwk = jwcrypto.jwk.JWK(**public_key)
            verified_token = jwcrypto.jwt.JWT(
                key=public_jwk, jwt=jwt_token, algs=[public_key["alg"]]
            )
            return json.loads(verified_token.claims)

        except Exception as err:
            LOGGER.error(err)
            raise AuthError("Unauthorized - token failed to verify", 401)


COGNITO_POOL = CognitoPool(
    region=COGNITO_REGION, client_id=COGNITO_CLIENT_ID, id=COGNITO_POOL_ID
)

if os.getenv("AWS_EXECUTION_ENV"):
    # instead of re-downloading the public keys every time, memoize them only on cold start
    # https://aws.amazon.com/blogs/compute/container-reuse-in-lambda/
    # https://docs.aws.amazon.com/lambda/latest/dg/runtimes-context.html
    assert COGNITO_POOL.jwks


@dataclass
class APIGateway:
    aws_region: str
    aws_account_id: str
    api_gateway_arn: str
    rest_api_id: str
    rest_api_stage: str

    @staticmethod
    def from_method_arn(method_arn):
        tmp = method_arn.split(":")
        api_gateway_arn = tmp[5].split("/")
        return APIGateway(
            aws_region=tmp[3],
            aws_account_id=tmp[4],
            api_gateway_arn=tmp[5],
            rest_api_id=api_gateway_arn[0],
            rest_api_stage=api_gateway_arn[1],
        )

    def get_auth_policy(self, principal_id: str):
        policy = AuthPolicy(principal_id, self.aws_account_id)
        policy.restApiId = self.rest_api_id
        policy.stage = self.rest_api_stage
        policy.region = self.aws_region
        return policy


def aws_auth_handler(event, context):
    """AWS Authorizer for JWT tokens provided by AWS Cognito

    event should have this form:
    {
        "type": "TOKEN",
        "authorizationToken": "{caller-supplied-token}",
        "methodArn": "arn:aws:execute-api:{regionId}:{accountId}:{apiId}/{stage}/{httpVerb}/[{resource}/[{child-resources}]]"
    }

    .. seealso::
        - https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
    """

    LOGGER.debug("event: %s", event)
    LOGGER.debug("context: %s", context)

    try:

        # validate the incoming token
        # and produce the principal user identifier associated with the token
        # this could be accomplished in a number of ways:
        # 1. Call out to OAuth provider
        # 2. Decode a JWT token inline
        # 3. Lookup in a self-managed DB

        # TODO: try 2. Decode a JWT token inline
        # https://docs.authlib.org/en/stable/jose/index.html
        # https://aws.amazon.com/premiumsupport/knowledge-center/decode-verify-cognito-json-token/
        # https://github.com/awslabs/aws-support-tools/tree/master/Cognito/decode-verify-jwt
        # there are flask plugins for this, but the API-Gateway solution is different
        # https://flask-jwt-extended.readthedocs.io/en/stable/basic_usage/
        # https://auth0.com/docs/quickstart/backend/python

        token = event.get("authorizationToken")
        if token is None:
            raise AuthError("Unauthorized - authorizationToken is missing", 401)

        if token.startswith("Bearer"):
            token = token.strip("Bearer").strip()

        # TODO: handle a SigV4 token?
        # 'authorizationToken': 'AWS4-HMAC-SHA256
        # Credential=<secret_id>/20200529/us-west-2/execute-api/aws4_request,
        # Signature=xyz'

        claims = COGNITO_POOL.jwt_claims(token)  # also validates JWT

        issuer = claims.get("iss")
        if not (COGNITO_POOL.region in issuer and COGNITO_POOL.id in issuer):
            raise AuthError("Unauthorized - invalid issuer in JWT claims", 403)

        if claims["token_use"] == "id":
            audience = claims.get("aud")
            if audience != COGNITO_POOL.client_id:
                raise AuthError("Unauthorized - invalid client-id in JWT claims", 403)
        elif claims["token_use"] == "access":
            client_id = claims.get("client_id")
            if client_id != COGNITO_POOL.client_id:
                raise AuthError("Unauthorized - invalid client-id in JWT claims", 403)
        else:
            # token validation should check this already, so should not get here
            raise AuthError("Unauthorized - invalid client-id in JWT claims", 403)

        if claims["token_use"] == "id":
            principle_id = claims.get("email")
            if not principle_id:
                raise AuthError(
                    "Unauthorized - invalid principle-id in JWT claims", 403
                )
            if not claims.get("email_verified"):
                raise AuthError(
                    "Unauthorized - email is not verified in JWT claims", 403
                )
        elif claims["token_use"] == "access":
            principle_id = claims.get("username")
            if not principle_id:
                raise AuthError(
                    "Unauthorized - invalid principle-id in JWT claims", 403
                )
        else:
            # token validation should check this already, so should not get here
            raise AuthError("Unauthorized - invalid principle-id in JWT claims", 403)

        # if the token is valid, a policy must be generated which will allow or deny
        # access to the client

        # if access is denied, the client will receive a 403 Access Denied response
        # if access is allowed, API Gateway will proceed with the backend
        # integration configured on the method that was called

        # this function must generate a policy that is associated with the
        # recognized principal user identifier.  depending on your use case, you
        # might store policies in a DB, or generate them on the fly

        # keep in mind, the policy is cached for 5 minutes by default (TTL is
        # configurable in the authorizer) and will apply to subsequent calls to any
        # method/resource in the RestApi made with the same token

        # the example policy below denies access to all resources in the RestApi
        LOGGER.info("Method ARN: %s", event["methodArn"])
        api_gateway = APIGateway.from_method_arn(event.get("methodArn"))
        policy = api_gateway.get_auth_policy(principle_id)
        policy.allowAllMethods()  # a valid signed JWT is sufficient

        #
        # TODO: use cognito-groups with an JWT-access token?
        #
        if principle_id not in API_ADMIN_EMAILS:
            policy.denyMethod(HttpVerb.GET, "/api/healthz")

        # TODO: restrict the policy by additional options:
        # #: The API Gateway API id. By default this is set to '*'
        # restApiId = "*"
        # #: The region where the API is deployed. By default this is set to '*'
        # region = "*"
        # #: The name of the stage used in the policy. By default this is set to '*'
        # stage = "*"

        # Finally, build the policy
        auth_response = policy.build()

        # # Add additional key-value pairs associated with the authenticated principal
        # # these are made available by API-GW like so: $context.authorizer.<key>
        # # additional context is cached
        # context = {"key": "value", "number": 1, "bool": True}  # $context.authorizer.key -> value
        # # context['arr'] = ['foo'] <- this is invalid, API-GW will not accept it
        # # context['obj'] = {'foo':'bar'} <- also invalid
        # auth_response["context"] = context

        # TODO: use "usageIdentifierKey": "{api-key}" for API-key use plans, if any.

        return auth_response

    except AuthError as auth_error:
        if auth_error.status_code == 403:
            api_gateway = APIGateway.from_method_arn(event.get("methodArn"))
            policy = api_gateway.get_auth_policy("nobody")
            policy.denyAllMethods()
            auth_response = policy.build()
            auth_response["error"] = auth_error.error
            return auth_response

        # API-GW requires the message text to be only "Unauthorized" for a 401
        raise Exception("Unauthorized")


class HttpVerb:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    HEAD = "HEAD"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    ALL = "*"


class AuthPolicy(object):
    #: The AWS account id the policy will be generated for.
    #: This is used to create the method ARNs.
    awsAccountId = ""
    #: The principal used for the policy, this should be a unique identifier for the end user.
    principalId = ""
    #: The policy version used for the evaluation. This should always be '2012-10-17'
    version = "2012-10-17"
    #: The regular expression used to validate resource paths for the policy
    pathRegex = "^[/.a-zA-Z0-9-\*]+$"

    #: These are the internal lists of allowed and denied methods. These are lists
    #: of objects and each object has 2 properties: A resource ARN and a nullable
    #: conditions statement. The build method processes these lists and generates
    #: the appropriate statements for the final policy
    allowMethods = []
    denyMethods = []

    #: The API Gateway API id. By default this is set to '*'
    restApiId = "*"
    #: The region where the API is deployed. By default this is set to '*'
    region = "*"
    #: The name of the stage used in the policy. By default this is set to '*'
    stage = "*"

    def __init__(self, principal, awsAccountId):
        self.awsAccountId = awsAccountId
        self.principalId = principal
        self.allowMethods = []
        self.denyMethods = []

    def _addMethod(self, effect, verb, resource, conditions):
        """Adds a method to the internal lists of allowed or denied methods. Each object in
        the internal list contains a resource ARN and a condition statement. The condition
        statement can be null."""
        if verb != "*" and not hasattr(HttpVerb, verb):
            raise NameError(
                "Invalid HTTP verb " + verb + ". Allowed verbs in HttpVerb class"
            )
        resourcePattern = re.compile(self.pathRegex)
        if not resourcePattern.match(resource):
            raise NameError(
                "Invalid resource path: "
                + resource
                + ". Path should match "
                + self.pathRegex
            )

        if resource[:1] == "/":
            resource = resource[1:]

        resourceArn = (
            "arn:aws:execute-api:"
            + self.region
            + ":"
            + self.awsAccountId
            + ":"
            + self.restApiId
            + "/"
            + self.stage
            + "/"
            + verb
            + "/"
            + resource
        )

        if effect.lower() == "allow":
            self.allowMethods.append(
                {"resourceArn": resourceArn, "conditions": conditions}
            )
        elif effect.lower() == "deny":
            self.denyMethods.append(
                {"resourceArn": resourceArn, "conditions": conditions}
            )

    def _getEmptyStatement(self, effect):
        """Returns an empty statement object prepopulated with the correct action and the
        desired effect."""
        statement = {
            "Action": "execute-api:Invoke",
            "Effect": effect[:1].upper() + effect[1:].lower(),
            "Resource": [],
        }

        return statement

    def _getStatementForEffect(self, effect, methods):
        """This function loops over an array of objects containing a resourceArn and
        conditions statement and generates the array of statements for the policy."""
        statements = []

        if len(methods) > 0:
            statement = self._getEmptyStatement(effect)

            for curMethod in methods:
                if curMethod["conditions"] is None or len(curMethod["conditions"]) == 0:
                    statement["Resource"].append(curMethod["resourceArn"])
                else:
                    conditionalStatement = self._getEmptyStatement(effect)
                    conditionalStatement["Resource"].append(curMethod["resourceArn"])
                    conditionalStatement["Condition"] = curMethod["conditions"]
                    statements.append(conditionalStatement)

            statements.append(statement)

        return statements

    def allowAllMethods(self):
        """Adds a '*' allow to the policy to authorize access to all methods of an API"""
        self._addMethod("Allow", HttpVerb.ALL, "*", [])

    def denyAllMethods(self):
        """Adds a '*' allow to the policy to deny access to all methods of an API"""
        self._addMethod("Deny", HttpVerb.ALL, "*", [])

    def allowMethod(self, verb, resource):
        """Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods for the policy"""
        self._addMethod("Allow", verb, resource, [])

    def denyMethod(self, verb, resource):
        """Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods for the policy"""
        self._addMethod("Deny", verb, resource, [])

    def allowMethodWithConditions(self, verb, resource, conditions):
        """Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide
        /reference_policies_elements.html#Condition"""
        self._addMethod("Allow", verb, resource, conditions)

    def denyMethodWithConditions(self, verb, resource, conditions):
        """Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide
        /reference_policies_elements.html#Condition"""
        self._addMethod("Deny", verb, resource, conditions)

    def build(self):
        """Generates the policy document based on the internal lists of allowed and denied
        conditions. This will generate a policy with two main statements for the effect:
        one statement for Allow and one statement for Deny.
        Methods that includes conditions will have their own statement in the policy."""
        if (self.allowMethods is None or len(self.allowMethods) == 0) and (
            self.denyMethods is None or len(self.denyMethods) == 0
        ):
            raise NameError("No statements defined for the policy")

        policy = {
            "principalId": self.principalId,
            "policyDocument": {"Version": self.version, "Statement": []},
        }

        policy["policyDocument"]["Statement"].extend(
            self._getStatementForEffect("Allow", self.allowMethods)
        )
        policy["policyDocument"]["Statement"].extend(
            self._getStatementForEffect("Deny", self.denyMethods)
        )

        return policy
