from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.health import HealthResponse
from app.services.health_service import health_service

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    return health_service.get_health(detailed=True, db=db)


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
def get_readiness(db: Session = Depends(get_db)) -> dict:
    return health_service.check_readiness(db=db)
