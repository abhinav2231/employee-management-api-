import math
from typing import List, Any
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.department import Department
from app.models.employee import Employee
from app.models.role import Role
from app.models.assignment import EmployeeAssignment
from app.schemas.department import DepartmentResponse, DepartmentCreate, DepartmentUpdate
from app.schemas.employee import EmployeeResponse
from app.schemas.common import PaginatedResponse
from app.services.formatters import format_employee_response


class DepartmentService:
    @staticmethod
    def _find_dept(db: Session, identifier: Any) -> Department:
        if identifier is None:
            raise NotFoundException("Department ID is required", field="department_id")
        ident_str = str(identifier).strip()
        dept = db.query(Department).filter(
            or_(
                func.lower(Department.department_id) == ident_str.lower(),
                func.lower(Department.department_name) == ident_str.lower(),
            )
        ).first()
        if not dept and ident_str.isdigit():
            cand = f"D{int(ident_str):02d}"
            dept = db.query(Department).filter(Department.department_id == cand).first()
        if not dept:
            raise NotFoundException(f"Department with ID or code '{identifier}' not found", field="department_id")
        return dept

    @staticmethod
    def list_departments(db: Session) -> List[DepartmentResponse]:
        departments = db.query(Department).order_by(Department.department_name.asc()).all()

        active_counts = dict(
            db.query(Employee.department_id, func.count(Employee.employee_id))
            .filter(Employee.is_active.is_(True))
            .group_by(Employee.department_id)
            .all()
        )

        return [
            DepartmentResponse(
                id=d.department_id,
                department_id=d.department_id,
                name=d.department_name,
                code=d.department_id,
                cost_center=d.cost_center,
                description=d.description,
                is_active=d.is_active,
                employee_count=active_counts.get(d.department_id, 0),
            )
            for d in departments
        ]

    @staticmethod
    def get_department(db: Session, department_id: Any) -> Department:
        return DepartmentService._find_dept(db, department_id)

    @staticmethod
    def get_department_details(db: Session, department_id: Any) -> DepartmentResponse:
        dept = DepartmentService.get_department(db, department_id)
        active_count = (
            db.query(func.count(Employee.employee_id))
            .filter(Employee.department_id == dept.department_id, Employee.is_active.is_(True))
            .scalar()
            or 0
        )
        return DepartmentResponse(
            id=dept.department_id,
            department_id=dept.department_id,
            name=dept.department_name,
            code=dept.department_id,
            cost_center=dept.cost_center,
            description=dept.description,
            is_active=dept.is_active,
            employee_count=active_count,
        )

    @staticmethod
    def create_department(db: Session, dept_in: DepartmentCreate) -> DepartmentResponse:
        code_clean = dept_in.code.strip().upper()
        name_clean = dept_in.name.strip()

        existing_code = db.query(Department).filter(func.lower(Department.department_id) == code_clean.lower()).first()
        if existing_code:
            raise ConflictException(f"Department with code '{code_clean}' already exists", field="code")

        existing_name = db.query(Department).filter(func.lower(Department.department_name) == name_clean.lower()).first()
        if existing_name:
            raise ConflictException(f"Department with name '{name_clean}' already exists", field="name")

        dept = Department(
            department_id=code_clean,
            department_name=name_clean,
            cost_center=dept_in.cost_center,
            description=dept_in.description,
            is_active=dept_in.is_active,
        )
        try:
            db.add(dept)
            db.commit()
            db.refresh(dept)
        except IntegrityError:
            db.rollback()
            raise ConflictException("Department with this code or name already exists")

        return DepartmentResponse(
            id=dept.department_id,
            department_id=dept.department_id,
            name=dept.department_name,
            code=dept.department_id,
            cost_center=dept.cost_center,
            description=dept.description,
            is_active=dept.is_active,
            employee_count=0,
        )

    @staticmethod
    def update_department(db: Session, department_id: Any, dept_in: DepartmentUpdate) -> DepartmentResponse:
        dept = DepartmentService.get_department(db, department_id)
        update_data = dept_in.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] is not None:
            name_clean = update_data["name"].strip()
            if name_clean.lower() != dept.department_name.lower():
                existing = db.query(Department).filter(
                    func.lower(Department.department_name) == name_clean.lower(),
                    Department.department_id != dept.department_id,
                ).first()
                if existing:
                    raise ConflictException(f"Department with name '{name_clean}' already exists", field="name")
                dept.department_name = name_clean

        if "code" in update_data and update_data["code"] is not None:
            code_clean = update_data["code"].strip().upper()
            if code_clean.lower() != dept.department_id.lower():
                existing = db.query(Department).filter(
                    func.lower(Department.department_id) == code_clean.lower(),
                    Department.department_id != dept.department_id,
                ).first()
                if existing:
                    raise ConflictException(f"Department with code '{code_clean}' already exists", field="code")
                dept.department_id = code_clean

        if "cost_center" in update_data:
            dept.cost_center = update_data["cost_center"]
        if "description" in update_data:
            dept.description = update_data["description"]
        if "is_active" in update_data and update_data["is_active"] is not None:
            dept.is_active = update_data["is_active"]

        try:
            db.commit()
            db.refresh(dept)
        except IntegrityError:
            db.rollback()
            raise ConflictException("Department with this code or name already exists")

        active_count = (
            db.query(func.count(Employee.employee_id))
            .filter(Employee.department_id == dept.department_id, Employee.is_active.is_(True))
            .scalar()
            or 0
        )
        return DepartmentResponse(
            id=dept.department_id,
            department_id=dept.department_id,
            name=dept.department_name,
            code=dept.department_id,
            cost_center=dept.cost_center,
            description=dept.description,
            is_active=dept.is_active,
            employee_count=active_count,
        )

    @staticmethod
    def delete_department(db: Session, department_id: Any) -> None:
        dept = DepartmentService.get_department(db, department_id)

        active_employees = (
            db.query(Employee)
            .filter(Employee.department_id == dept.department_id, Employee.is_active.is_(True))
            .count()
        )
        if active_employees > 0:
            raise BadRequestException(
                f"Cannot delete department with {active_employees} active employee(s). Reassign them first.",
                field="department_id",
            )

        roles_count = db.query(Role).filter(Role.department_id == dept.department_id).count()
        total_employees = db.query(Employee).filter(Employee.department_id == dept.department_id).count()
        assignments_count = db.query(EmployeeAssignment).filter(EmployeeAssignment.department_id == dept.department_id).count()

        if total_employees > 0 or roles_count > 0 or assignments_count > 0:
            dept.is_active = False
            db.commit()
        else:
            db.delete(dept)
            db.commit()

    @staticmethod
    def get_department_employees(
        db: Session,
        department_id: Any,
        page: int = 1,
        size: int = 20,
        include_inactive: bool = False,
    ) -> PaginatedResponse[EmployeeResponse]:
        dept = DepartmentService.get_department(db, department_id)

        query = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.role),
                joinedload(Employee.manager),
            )
            .filter(Employee.department_id == dept.department_id)
        )

        if not include_inactive:
            query = query.filter(Employee.is_active.is_(True))

        query = query.order_by(Employee.last_name.asc(), Employee.first_name.asc())

        total = query.count()
        pages = math.ceil(total / size) if total > 0 else 0
        offset = (page - 1) * size
        employees = query.offset(offset).limit(size).all()

        items = [format_employee_response(e) for e in employees]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )


department_service = DepartmentService()
