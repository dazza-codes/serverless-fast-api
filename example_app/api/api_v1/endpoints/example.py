from fastapi import APIRouter

from example_app.core.models.input import InputExample
from example_app.core.models.output import OutputExample

router = APIRouter()


@router.get("/example", tags=["example get"])
def example_get():
    """
    Say hey!

    This will greet you properly

    And this path operation will:
    * return {"msg": "Hey!"}
    """
    return {"msg": "Hey!"}


@router.post("/example", response_model=OutputExample, tags=["example post"])
def example_endpoint(inputs: InputExample):
    """
    Multiply two values

    This will multiply two inputs.

    And this path operation will:
    * return a*b
    """
    return {"a": inputs.a, "b": inputs.b, "result": inputs.a * inputs.b}
