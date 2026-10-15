from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.role import Role
from app.schemas.role import RoleResponse

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
    query = db.query(Role)
    if department_id is not None:
        d_str = str(department_id).strip()
        query = query.filter(func.lower(Role.department_id) == d_str.lower())
    if is_active is not None:
        query = query.filter(Role.is_active == is_active)
    return query.order_by(Role.role_id.asc()).all()


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
    id_str = id.strip()
    role = db.query(Role).filter(
        or_(
            func.lower(Role.role_id) == id_str.lower(),
            func.lower(Role.role_title) == id_str.lower(),
        )
    ).first()
    if not role and id_str.isdigit():
        cand = f"R{int(id_str):03d}"
        role = db.query(Role).filter(Role.role_id == cand).first()

    if not role:
        raise NotFoundException(f"Role with ID or code '{id}' not found", field="id")
    return role
