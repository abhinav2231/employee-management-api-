import math
from typing import List
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.department import Department
from app.models.employee import Employee
from app.models.role import Role, EmployeeRole
from app.models.assignment import EmployeeAssignment
from app.schemas.department import DepartmentResponse, DepartmentCreate, DepartmentUpdate
from app.schemas.employee import EmployeeResponse
from app.schemas.common import PaginatedResponse
from app.schemas.role import RoleBrief
from app.services.formatters import format_employee_response


class DepartmentService:
    @staticmethod
    def list_departments(db: Session) -> List[DepartmentResponse]:
        departments = db.query(Department).order_by(Department.name.asc()).all()

        active_counts = dict(
            db.query(Employee.department_id, func.count(Employee.id))
            .filter(Employee.is_active.is_(True))
            .group_by(Employee.department_id)
            .all()
        )

        return [
            DepartmentResponse(
                id=d.id,
                name=d.name,
                code=d.code,
                cost_center=d.cost_center,
                description=d.description,
                is_active=d.is_active,
                employee_count=active_counts.get(d.id, 0),
            )
            for d in departments
        ]

    @staticmethod
    def get_department(db: Session, department_id: int) -> Department:
        dept = db.query(Department).filter(Department.id == department_id).first()
        if not dept:
            raise NotFoundException(f"Department with ID {department_id} not found", field="department_id")
        return dept

    @staticmethod
    def get_department_details(db: Session, department_id: int) -> DepartmentResponse:
        dept = DepartmentService.get_department(db, department_id)
        active_count = (
            db.query(func.count(Employee.id))
            .filter(Employee.department_id == department_id, Employee.is_active.is_(True))
            .scalar()
            or 0
        )
        return DepartmentResponse(
            id=dept.id,
            name=dept.name,
            code=dept.code,
            cost_center=dept.cost_center,
            description=dept.description,
            is_active=dept.is_active,
            employee_count=active_count,
        )

    @staticmethod
    def create_department(db: Session, dept_in: DepartmentCreate) -> DepartmentResponse:
        code_clean = dept_in.code.strip()
        name_clean = dept_in.name.strip()

        existing_code = db.query(Department).filter(func.lower(Department.code) == code_clean.lower()).first()
        if existing_code:
            raise ConflictException(f"Department with code '{code_clean}' already exists", field="code")

        existing_name = db.query(Department).filter(func.lower(Department.name) == name_clean.lower()).first()
        if existing_name:
            raise ConflictException(f"Department with name '{name_clean}' already exists", field="name")

        dept = Department(
            name=name_clean,
            code=code_clean.upper(),
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
            id=dept.id,
            name=dept.name,
            code=dept.code,
            cost_center=dept.cost_center,
            description=dept.description,
            is_active=dept.is_active,
            employee_count=0,
        )

    @staticmethod
    def update_department(db: Session, department_id: int, dept_in: DepartmentUpdate) -> DepartmentResponse:
        dept = DepartmentService.get_department(db, department_id)
        update_data = dept_in.model_dump(exclude_unset=True)

        if "code" in update_data and update_data["code"] is not None:
            code_clean = update_data["code"].strip()
            if code_clean.lower() != dept.code.lower():
                existing = db.query(Department).filter(
                    func.lower(Department.code) == code_clean.lower(),
                    Department.id != dept.id,
                ).first()
                if existing:
                    raise ConflictException(f"Department with code '{code_clean}' already exists", field="code")
                dept.code = code_clean.upper()

        if "name" in update_data and update_data["name"] is not None:
            name_clean = update_data["name"].strip()
            if name_clean.lower() != dept.name.lower():
                existing = db.query(Department).filter(
                    func.lower(Department.name) == name_clean.lower(),
                    Department.id != dept.id,
                ).first()
                if existing:
                    raise ConflictException(f"Department with name '{name_clean}' already exists", field="name")
                dept.name = name_clean

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
            db.query(func.count(Employee.id))
            .filter(Employee.department_id == dept.id, Employee.is_active.is_(True))
            .scalar()
            or 0
        )
        return DepartmentResponse(
            id=dept.id,
            name=dept.name,
            code=dept.code,
            cost_center=dept.cost_center,
            description=dept.description,
            is_active=dept.is_active,
            employee_count=active_count,
        )

    @staticmethod
    def delete_department(db: Session, department_id: int) -> None:
        dept = DepartmentService.get_department(db, department_id)

        active_employees = (
            db.query(Employee)
            .filter(Employee.department_id == department_id, Employee.is_active.is_(True))
            .count()
        )
        if active_employees > 0:
            raise BadRequestException(
                f"Cannot delete department with {active_employees} active employee(s). Reassign them first.",
                field="department_id",
            )

        roles_count = db.query(Role).filter(Role.department_id == department_id).count()
        total_employees = db.query(Employee).filter(Employee.department_id == department_id).count()
        assignments_count = db.query(EmployeeAssignment).filter(EmployeeAssignment.department_id == department_id).count()

        if total_employees > 0 or roles_count > 0 or assignments_count > 0:
            dept.is_active = False
            db.commit()
        else:
            db.delete(dept)
            db.commit()

    @staticmethod
    def get_department_employees(
        db: Session,
        department_id: int,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[EmployeeResponse]:
        DepartmentService.get_department(db, department_id)

        query = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.manager),
                selectinload(Employee.employee_roles).joinedload(EmployeeRole.role),
            )
            .filter(
                Employee.department_id == department_id,
                Employee.is_active.is_(True),
            )
            .order_by(Employee.last_name.asc(), Employee.first_name.asc())
        )

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

    @staticmethod
    def _format_employee_response(e: Employee) -> EmployeeResponse:
        return format_employee_response(e)



department_service = DepartmentService()
