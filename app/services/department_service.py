import math
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentResponse
from app.schemas.employee import EmployeeResponse
from app.schemas.common import PaginatedResponse
from app.schemas.role import RoleBrief


class DepartmentService:
    """
    Business logic layer for department operations.
    Keeps route handlers lean and focused purely on HTTP contracts.
    """

    @staticmethod
    def list_departments(db: Session) -> List[DepartmentResponse]:
        """
        List all departments with their current active headcount.
        """
        departments = db.query(Department).order_by(Department.name.asc()).all()
        results: List[DepartmentResponse] = []

        for d in departments:
            active_count = sum(1 for e in d.employees if e.is_active)
            results.append(
                DepartmentResponse(
                    id=d.id,
                    name=d.name,
                    code=d.code,
                    description=d.description,
                    is_active=d.is_active,
                    employee_count=active_count,
                )
            )
        return results

    @staticmethod
    def get_department(db: Session, department_id: int) -> Department:
        """
        Retrieve a single department by ID or raise a NotFoundException.
        """
        dept = db.query(Department).filter(Department.id == department_id).first()
        if not dept:
            raise NotFoundException(f"Department with ID {department_id} not found", field="department_id")
        return dept

    @staticmethod
    def get_department_details(db: Session, department_id: int) -> DepartmentResponse:
        """
        Retrieve a single department by ID with calculated active headcount.
        """
        dept = DepartmentService.get_department(db, department_id)
        active_count = sum(1 for e in dept.employees if e.is_active)
        return DepartmentResponse(
            id=dept.id,
            name=dept.name,
            code=dept.code,
            description=dept.description,
            is_active=dept.is_active,
            employee_count=active_count,
        )

    @staticmethod
    def get_department_employees(
        db: Session,
        department_id: int,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[EmployeeResponse]:
        """
        Retrieve paginated list of active employees belonging to a specific department.
        """
        # Ensure department exists first
        DepartmentService.get_department(db, department_id)

        query = db.query(Employee).filter(
            Employee.department_id == department_id,
            Employee.is_active.is_(True),
        ).order_by(Employee.last_name.asc(), Employee.first_name.asc())

        total = query.count()
        pages = math.ceil(total / size) if total > 0 else 0
        offset = (page - 1) * size
        employees = query.offset(offset).limit(size).all()

        items = [DepartmentService._format_employee_response(e) for e in employees]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    @staticmethod
    def _format_employee_response(e: Employee) -> EmployeeResponse:
        roles_brief = [
            RoleBrief(
                id=er.role.id,
                title=er.role.title,
                level=er.role.level,
                is_primary=er.is_primary,
            )
            for er in e.employee_roles
        ]
        return EmployeeResponse(
            id=e.id,
            first_name=e.first_name,
            last_name=e.last_name,
            email=e.email,
            department_id=e.department_id,
            department=e.department,
            manager_id=e.manager_id,
            manager=e.manager,
            salary=e.salary,
            hire_date=e.hire_date,
            is_active=e.is_active,
            roles=roles_brief,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )


department_service = DepartmentService()
