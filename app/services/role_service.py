from typing import List, Optional
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.role import Role
from app.schemas.role import RoleResponse


class RoleService:
    @staticmethod
    def list_roles(
        db: Session,
        department_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[RoleResponse]:
        query = db.query(Role)
        if department_id is not None:
            d_str = str(department_id).strip()
            query = query.filter(func.lower(Role.department_id) == d_str.lower())
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        return query.order_by(Role.role_id.asc()).all()

    @staticmethod
    def get_role(db: Session, role_id: str) -> RoleResponse:
        id_str = role_id.strip()
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
            raise NotFoundException(f"Role with ID or code '{role_id}' not found", field="id")
        return role


role_service = RoleService()
