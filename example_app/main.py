import os
from typing import Optional

from fastapi import FastAPI
from example_app.api.api_v1.api import router as api_router
from example_app.core.config import API_V1_STR, PROJECT_NAME
from mangum import Mangum

app = FastAPI(
    title=PROJECT_NAME,
    # if not custom domain
    # openapi_prefix="/Prod"
)


app.include_router(api_router, prefix=API_V1_STR)


@app.get("/ping")
def pong():
    """
    Sanity check.

    This will let the user know that the service is operational.

    And this path operation will:
    * show a lifesign

    """
    return {"ping": "pong!"}


def get_asgi_handler(fast_api: FastAPI) -> Optional[Mangum]:
    """Initialize an AWS Lambda ASGI handler"""

    if os.getenv("AWS_EXECUTION_ENV"):
        return Mangum(fast_api, enable_lifespan=False)


handler = get_asgi_handler(app)