from fastapi import APIRouter, status
from app.schemas.health import HealthResponse
from app.services.health_service import health_service

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the operational status of the service.",
    tags=["Health"],
)
def get_health() -> HealthResponse:
    """
    Service health check endpoint returning {"status": "ok"}.
    """
    return health_service.get_health()
