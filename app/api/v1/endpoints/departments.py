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
    summary="List Departments",
    description="List all organization departments with active headcounts.",
)
def list_departments(
    db: Session = Depends(get_db),
) -> List[DepartmentResponse]:
    return department_service.list_departments(db=db)


@router.get(
    "/{id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Department by ID",
    description="Retrieve a single department by its ID.",
)
def get_department(
    id: int = Path(..., ge=1, description="Department ID"),
    db: Session = Depends(get_db),
) -> DepartmentResponse:
    return department_service.get_department_details(db=db, department_id=id)


@router.get(
    "/{id}/employees",
    response_model=PaginatedResponse[EmployeeResponse],
    status_code=status.HTTP_200_OK,
    summary="List Department Employees",
    description="Retrieve paginated employees assigned to a specific department.",
)
def get_department_employees(
    id: int = Path(..., ge=1, description="Department ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[EmployeeResponse]:
    return department_service.get_department_employees(
        db=db,
        department_id=id,
        page=page,
        size=size,
    )
