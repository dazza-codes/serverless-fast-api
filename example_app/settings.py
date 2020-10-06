from pydantic import BaseSettings
from pydantic import Field
from pydantic import PostgresDsn
from pydantic import validator


# FLASK_ENV: development
# FLASK_DEBUG: false
# LOG_LEVEL: DEBUG
#
# API_ENV: dev
# API_ENDPOINT: https://{api_gateway}.execute-api.us-west-2.amazonaws.com/dev
# API_ADMIN_EMAILS: joe.bloggs@example.com


class Settings(BaseSettings):
    """

    .. seealso::
        - https://pydantic-docs.helpmanual.io/usage/settings/
    """

    class Config:
        # env-var names are not case-sensitive
        env_prefix = "app_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    cognito_region: str = Field(default=None, env="API_COGNITO_REGION")
    cognito_client_id: str = Field(default=None, env="API_COGNITO_CLIENT_ID")
    cognito_pool_id: str = Field(default=None, env="API_COGNITO_POOL_ID")

    pg_dsn: PostgresDsn = "postgres://user:pass@localhost:5432/foobar"
