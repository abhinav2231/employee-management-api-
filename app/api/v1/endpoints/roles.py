from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.role import RoleResponse
from app.services.role_service import role_service

router = APIRouter()


@router.get(
    "",
    response_model=List[RoleResponse],
    status_code=status.HTTP_200_OK,
    summary="List all organization roles",
)
def list_roles(
    department_id: Optional[str] = Query(None, description="Filter by department ID or code"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
) -> List[RoleResponse]:
    return role_service.list_roles(db=db, department_id=department_id, is_active=is_active)


@router.get(
    "/{id}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get role details by ID",
)
def get_role(
    id: str = Path(..., description="Role ID (e.g. R001) or title"),
    db: Session = Depends(get_db),
) -> RoleResponse:
    return role_service.get_role(db=db, role_id=id)
