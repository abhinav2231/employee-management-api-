import math
from typing import Optional, List
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
)
from app.models.department import Department
from app.models.role import Role, EmployeeRole
from app.models.employee import Employee
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeBrief,
    TeamResponse,
)
from app.schemas.common import PaginatedResponse
from app.schemas.role import RoleBrief


class EmployeeService:
    """
    Business logic layer for Employee management and reporting hierarchy.
    """

    @staticmethod
    def create_employee(db: Session, employee_in: EmployeeCreate) -> EmployeeResponse:
        """
        Create a new employee record with validation of uniqueness and foreign relationships.
        """
        # 1. Email uniqueness check
        existing_email = db.query(Employee).filter(Employee.email == employee_in.email).first()
        if existing_email:
            raise ConflictException(
                f"Employee with work email '{employee_in.email}' already exists",
                field="email",
            )

        # 2. Validate department existence
        dept = db.query(Department).filter(Department.id == employee_in.department_id).first()
        if not dept:
            raise BadRequestException(
                f"Department with ID {employee_in.department_id} does not exist",
                field="department_id",
            )

        # 3. Validate manager existence (if assigned)
        if employee_in.manager_id is not None:
            manager = db.query(Employee).filter(Employee.id == employee_in.manager_id).first()
            if not manager:
                raise BadRequestException(
                    f"Manager with ID {employee_in.manager_id} does not exist",
                    field="manager_id",
                )

        # 4. Validate role existence (if assigned)
        role = None
        if employee_in.role_id is not None:
            role = db.query(Role).filter(Role.id == employee_in.role_id).first()
            if not role:
                raise BadRequestException(
                    f"Role with ID {employee_in.role_id} does not exist",
                    field="role_id",
                )

        # 5. Create employee entity
        employee = Employee(
            employee_code=employee_in.employee_code,
            first_name=employee_in.first_name,
            last_name=employee_in.last_name,
            email=employee_in.email,
            department_id=employee_in.department_id,
            manager_id=employee_in.manager_id,
            salary=employee_in.salary,
            hire_date=employee_in.hire_date,
            work_location=employee_in.work_location,
            employment_type=employee_in.employment_type,
            is_active=employee_in.is_active,
        )
        db.add(employee)
        db.flush()

        # 6. Assign primary role if supplied
        if role is not None:
            emp_role = EmployeeRole(
                employee_id=employee.id,
                role_id=role.id,
                is_primary=True,
            )
            db.add(emp_role)

        db.commit()
        db.refresh(employee)

        return EmployeeService._format_employee_response(employee)

    @staticmethod
    def get_employee(db: Session, employee_id: int) -> EmployeeResponse:
        """
        Retrieve a single employee by ID.
        """
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise NotFoundException(f"Employee with ID {employee_id} not found", field="id")
        return EmployeeService._format_employee_response(employee)

    @staticmethod
    def list_employees(
        db: Session,
        page: int = 1,
        size: int = 20,
        department: Optional[str] = None,
        q: Optional[str] = None,
        include_inactive: bool = False,
    ) -> PaginatedResponse[EmployeeResponse]:
        """
        List employees with pagination, department filter, and full-text name/email search.
        """
        query = db.query(Employee)

        # Filter active employment status by default
        if not include_inactive:
            query = query.filter(Employee.is_active.is_(True))

        # Department filtering (accepts ID, Code like 'ENG', or Name like 'Engineering')
        if department:
            dept_term = department.strip()
            if dept_term.isdigit():
                query = query.filter(Employee.department_id == int(dept_term))
            else:
                query = query.join(Employee.department).filter(
                    or_(
                        Department.code.ilike(dept_term),
                        Department.name.ilike(f"%{dept_term}%"),
                    )
                )

        # Search query (matches first name, last name, full name, or email)
        if q and q.strip():
            search = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search),
                    Employee.last_name.ilike(search),
                    func.concat(Employee.first_name, " ", Employee.last_name).ilike(search),
                    Employee.email.ilike(search),
                    Employee.employee_code.ilike(search),
                )
            )

        query = query.order_by(Employee.id.asc())

        total = query.count()
        pages = math.ceil(total / size) if total > 0 else 0
        offset = (page - 1) * size
        employees = query.offset(offset).limit(size).all()

        items = [EmployeeService._format_employee_response(e) for e in employees]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    @staticmethod
    def update_employee(
        db: Session,
        employee_id: int,
        employee_in: EmployeeUpdate,
    ) -> EmployeeResponse:
        """
        Partially update (PATCH) an existing employee record.
        """
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise NotFoundException(f"Employee with ID {employee_id} not found", field="id")

        # 1. Email conflict check
        if employee_in.email is not None and employee_in.email != employee.email:
            existing_email = db.query(Employee).filter(
                Employee.email == employee_in.email,
                Employee.id != employee_id,
            ).first()
            if existing_email:
                raise ConflictException(
                    f"Employee with work email '{employee_in.email}' already exists",
                    field="email",
                )
            employee.email = employee_in.email

        # 2. Department check
        if employee_in.department_id is not None:
            dept = db.query(Department).filter(Department.id == employee_in.department_id).first()
            if not dept:
                raise BadRequestException(
                    f"Department with ID {employee_in.department_id} does not exist",
                    field="department_id",
                )
            employee.department_id = employee_in.department_id

        # 3. Manager check & self-manager prevention
        if employee_in.manager_id is not None:
            if employee_in.manager_id == employee_id:
                raise BadRequestException("An employee cannot be their own manager", field="manager_id")
            manager = db.query(Employee).filter(Employee.id == employee_in.manager_id).first()
            if not manager:
                raise BadRequestException(
                    f"Manager with ID {employee_in.manager_id} does not exist",
                    field="manager_id",
                )
            employee.manager_id = employee_in.manager_id

        # 4. Role assignment update
        if employee_in.role_id is not None:
            role = db.query(Role).filter(Role.id == employee_in.role_id).first()
            if not role:
                raise BadRequestException(
                    f"Role with ID {employee_in.role_id} does not exist",
                    field="role_id",
                )
            # Demote existing primary roles
            for er in employee.employee_roles:
                if er.is_primary:
                    er.is_primary = False

            # Assign or promote new role
            matching_er = next((er for er in employee.employee_roles if er.role_id == role.id), None)
            if matching_er:
                matching_er.is_primary = True
            else:
                db.add(EmployeeRole(employee_id=employee.id, role_id=role.id, is_primary=True))

        # 5. Direct field updates
        if employee_in.first_name is not None:
            employee.first_name = employee_in.first_name
        if employee_in.last_name is not None:
            employee.last_name = employee_in.last_name
        if employee_in.salary is not None:
            employee.salary = employee_in.salary
        if employee_in.hire_date is not None:
            employee.hire_date = employee_in.hire_date
        if employee_in.is_active is not None:
            employee.is_active = employee_in.is_active

        db.commit()
        db.refresh(employee)

        return EmployeeService._format_employee_response(employee)

    @staticmethod
    def delete_employee(db: Session, employee_id: int) -> None:
        """
        Soft delete an employee by toggling is_active = False.
        Preserves compliance and historical payroll records.
        """
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise NotFoundException(f"Employee with ID {employee_id} not found", field="id")

        employee.is_active = False
        db.commit()

    @staticmethod
    def get_employee_team(db: Session, employee_id: int) -> TeamResponse:
        """
        Retrieve manager details and all active direct reports.
        """
        manager = db.query(Employee).filter(Employee.id == employee_id).first()
        if not manager:
            raise NotFoundException(f"Employee with ID {employee_id} not found", field="id")

        direct_reports = db.query(Employee).filter(
            Employee.manager_id == employee_id,
            Employee.is_active.is_(True),
        ).order_by(Employee.last_name.asc(), Employee.first_name.asc()).all()

        manager_brief = EmployeeBrief(
            id=manager.id,
            employee_code=manager.employee_code,
            first_name=manager.first_name,
            last_name=manager.last_name,
            email=manager.email,
            department_id=manager.department_id,
            is_active=manager.is_active,
        )

        reports_brief = [
            EmployeeBrief(
                id=rep.id,
                employee_code=rep.employee_code,
                first_name=rep.first_name,
                last_name=rep.last_name,
                email=rep.email,
                department_id=rep.department_id,
                is_active=rep.is_active,
            )
            for rep in direct_reports
        ]

        return TeamResponse(
            manager=manager_brief,
            direct_reports=reports_brief,
            total_reports=len(reports_brief),
        )

    @staticmethod
    def _format_employee_response(e: Employee) -> EmployeeResponse:
        roles_brief = [
            RoleBrief(
                id=er.role.id,
                code=er.role.code,
                title=er.role.title,
                level=er.role.level,
                is_primary=er.is_primary,
            )
            for er in e.employee_roles
        ]
        return EmployeeResponse(
            id=e.id,
            employee_code=e.employee_code,
            first_name=e.first_name,
            last_name=e.last_name,
            email=e.email,
            department_id=e.department_id,
            department=e.department,
            manager_id=e.manager_id,
            manager=e.manager,
            salary=e.salary,
            hire_date=e.hire_date,
            exit_date=e.exit_date,
            work_location=e.work_location,
            employment_type=e.employment_type,
            is_active=e.is_active,
            roles=roles_brief,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )


employee_service = EmployeeService()
