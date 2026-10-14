from fastapi import APIRouter, status
from app.schemas.health import HealthResponse
from app.services.health_service import health_service

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
def get_health() -> HealthResponse:
    return health_service.get_health()
