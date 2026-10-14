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
    department: Optional[str] = Query(None),
    employee_code: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
) -> PaginatedResponse[EmployeeResponse]:
    return employee_service.list_employees(
        db=db,
        page=page,
        size=size,
        department=department,
        employee_code=employee_code,
        q=q,
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
