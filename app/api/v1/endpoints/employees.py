from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    TeamResponse,
)
from app.schemas.assignment import EmployeeAssignmentResponse
from app.schemas.common import PaginatedResponse
from app.services.employee_service import employee_service

router = APIRouter()


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
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
)
def list_employees(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    department_id: Optional[str] = Query(None, description="Filter by department ID or code"),
    role_id: Optional[str] = Query(None, description="Filter by role ID or code"),
    employment_status: Optional[str] = Query(None, description="Filter by employment status (Active, Resigned, etc.)"),
    work_location: Optional[str] = Query(None, description="Filter by office city location"),
    work_mode: Optional[str] = Query(None, description="Filter by work mode (Onsite, Hybrid, Remote)"),
    manager_id: Optional[str] = Query(None, description="Filter by reporting manager ID"),
    hire_date_from: Optional[date] = Query(None, description="Filter by hire date on or after"),
    hire_date_to: Optional[date] = Query(None, description="Filter by hire date on or before"),
    department: Optional[str] = Query(None, description="Legacy alias for department_id"),
    employee_code: Optional[str] = Query(None, description="Filter by employee code substring"),
    q: Optional[str] = Query(None, description="Free-text search across name, email, employee ID"),
    sort: Optional[str] = Query(None, description="Sort field, prefix with '-' for descending (e.g. -hire_date)"),
    include_inactive: bool = Query(False, description="Include deactivated/exited employees"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[EmployeeResponse]:
    return employee_service.list_employees(
        db=db,
        page=page,
        size=size,
        department_id=department_id,
        role_id=role_id,
        employment_status=employment_status,
        work_location=work_location,
        work_mode=work_mode,
        manager_id=manager_id,
        hire_date_from=hire_date_from,
        hire_date_to=hire_date_to,
        department=department,
        employee_code=employee_code,
        q=q,
        sort=sort,
        include_inactive=include_inactive,
    )


@router.get(
    "/{id}",
    response_model=EmployeeResponse,
    status_code=status.HTTP_200_OK,
)
def get_employee(
    id: str = Path(...),
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    return employee_service.get_employee(db=db, employee_id=id)


@router.patch(
    "/{id}",
    response_model=EmployeeResponse,
    status_code=status.HTTP_200_OK,
)
def update_employee(
    employee_in: EmployeeUpdate,
    id: str = Path(...),
    db: Session = Depends(get_db),
) -> EmployeeResponse:
    return employee_service.update_employee(db=db, employee_id=id, employee_in=employee_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_employee(
    id: str = Path(...),
    db: Session = Depends(get_db),
) -> None:
    employee_service.delete_employee(db=db, employee_id=id)


@router.get(
    "/{id}/team",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
)
def get_employee_team(
    id: str = Path(...),
    db: Session = Depends(get_db),
) -> TeamResponse:
    return employee_service.get_employee_team(db=db, employee_id=id)


@router.get(
    "/{id}/assignments",
    response_model=List[EmployeeAssignmentResponse],
    status_code=status.HTTP_200_OK,
    tags=["Employees"],
)
def get_employee_assignments(
    id: str = Path(...),
    db: Session = Depends(get_db),
) -> List[EmployeeAssignmentResponse]:
    return employee_service.get_employee_assignments(db=db, employee_id=id)
