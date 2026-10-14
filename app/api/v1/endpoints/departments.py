from typing import List
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.department import DepartmentResponse
from app.schemas.employee import EmployeeResponse
from app.schemas.common import PaginatedResponse
from app.services.department_service import department_service

router = APIRouter()


@router.get(
    "",
    response_model=List[DepartmentResponse],
    status_code=status.HTTP_200_OK,
)
def list_departments(
    db: Session = Depends(get_db),
) -> List[DepartmentResponse]:
    return department_service.list_departments(db=db)


@router.get(
    "/{id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
)
def get_department(
    id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    return department_service.get_department_details(db=db, department_id=id)


@router.get(
    "/{id}/employees",
    response_model=PaginatedResponse[EmployeeResponse],
    status_code=status.HTTP_200_OK,
)
def get_department_employees(
    id: int = Path(..., ge=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[EmployeeResponse]:
    return department_service.get_department_employees(
        db=db,
        department_id=id,
        page=page,
        size=size,
    )
