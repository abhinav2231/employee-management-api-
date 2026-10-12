from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    TeamResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.employee_service import employee_service

router = APIRouter()


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Employee",
    description="Create a new employee record with department and manager associations.",
)
def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    return employee_service.create_employee(db=db, employee_in=employee_in)


@router.get(
    "",
    response_model=PaginatedResponse[EmployeeResponse],
    status_code=status.HTTP_200_OK,
    summary="List Employees",
    description="List active employees with pagination, department filter, and search.",
)
def list_employees(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    department: Optional[str] = Query(None, description="Department code, name, or ID"),
    q: Optional[str] = Query(None, description="Search term matching name or email"),
    include_inactive: bool = Query(False, description="Include soft-deleted records"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[EmployeeResponse]:
    return employee_service.list_employees(
        db=db,
        page=page,
        size=size,
        department=department,
        q=q,
        include_inactive=include_inactive,
    )


@router.get(
    "/{id}",
    response_model=EmployeeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Employee by ID",
    description="Retrieve detailed profile of a single employee.",
)
def get_employee(
    id: int = Path(..., ge=1, description="Employee ID"),
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    return employee_service.get_employee(db=db, employee_id=id)


@router.patch(
    "/{id}",
    response_model=EmployeeResponse,
    status_code=status.HTTP_200_OK,
    summary="Patch Employee",
    description="Partially update an existing employee profile.",
)
def update_employee(
    employee_in: EmployeeUpdate,
    id: int = Path(..., ge=1, description="Employee ID"),
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    return employee_service.update_employee(db=db, employee_id=id, employee_in=employee_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Employee (Soft Delete)",
    description="Soft-deletes an employee by toggling is_active to false.",
)
def delete_employee(
    id: int = Path(..., ge=1, description="Employee ID"),
    db: Session = Depends(get_db),
) -> None:
    employee_service.delete_employee(db=db, employee_id=id)


@router.get(
    "/{id}/team",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Employee Team (Direct Reports)",
    description="Retrieve an employee's direct reports within the reporting hierarchy.",
)
def get_employee_team(
    id: int = Path(..., ge=1, description="Manager Employee ID"),
    db: Session = Depends(get_db),
) -> TeamResponse:
    return employee_service.get_employee_team(db=db, employee_id=id)
