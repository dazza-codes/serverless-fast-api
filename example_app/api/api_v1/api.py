from fastapi import APIRouter

from example_app.api.api_v1.endpoints.example import router as v1_router

router = APIRouter()
router.include_router(v1_router)
