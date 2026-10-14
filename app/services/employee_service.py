from datetime import date
import math
import re
from typing import Optional, List, Any, Union
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

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
    @staticmethod
    def _find_employee(db: Session, identifier: Any) -> Optional[Employee]:
        if identifier is None:
            return None
        ident_str = str(identifier).strip()
        if ident_str.isdigit():
            return db.query(Employee).filter(Employee.id == int(ident_str)).first()
        return db.query(Employee).filter(Employee.employee_code.ilike(ident_str)).first()

    @staticmethod
    def _resolve_department(db: Session, dept_val: Any) -> Department:
        dept = None
        if isinstance(dept_val, int) or (isinstance(dept_val, str) and dept_val.isdigit()):
            dept = db.query(Department).filter(Department.id == int(dept_val)).first()
        if not dept and isinstance(dept_val, str):
            dept = db.query(Department).filter(
                or_(Department.code.ilike(dept_val.strip()), Department.name.ilike(dept_val.strip()))
            ).first()

        if not dept:
            raise BadRequestException(
                f"Department '{dept_val}' does not exist",
                field="department_id",
            )
        return dept

    @staticmethod
    def _resolve_role(db: Session, role_val: Any) -> Optional[Role]:
        if role_val is None:
            return None
        role = None
        if isinstance(role_val, int) or (isinstance(role_val, str) and role_val.isdigit()):
            role = db.query(Role).filter(Role.id == int(role_val)).first()
        if not role and isinstance(role_val, str):
            role = db.query(Role).filter(
                or_(Role.code.ilike(role_val.strip()), Role.title.ilike(role_val.strip()))
            ).first()

        if not role:
            raise BadRequestException(
                f"Role '{role_val}' does not exist",
                field="role_id",
            )
        return role

    @staticmethod
    def _resolve_manager(db: Session, mgr_val: Any) -> Optional[Employee]:
        if mgr_val is None:
            return None
        manager = EmployeeService._find_employee(db, mgr_val)
        if not manager:
            raise BadRequestException(
                f"Manager '{mgr_val}' does not exist",
                field="manager_id",
            )
        if not manager.is_active:
            raise BadRequestException(
                f"Cannot assign inactive or soft-deleted employee '{mgr_val}' as manager",
                field="manager_id",
            )
        return manager

    @staticmethod
    def _get_next_employee_code(db: Session) -> str:
        codes = db.query(Employee.employee_code).filter(Employee.employee_code.like("EMP-%")).all()
        max_num = 0
        for (c,) in codes:
            if c:
                match = re.search(r"EMP-(\d+)", c, re.IGNORECASE)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
        next_code = f"EMP-{max_num + 1:04d}"
        return next_code

    @staticmethod
    def _detect_manager_cycle(db: Session, employee_id: int, candidate_manager_id: int) -> None:
        if employee_id == candidate_manager_id:
            raise BadRequestException("An employee cannot be their own manager", field="manager_id")

        visited = {employee_id}
        curr_id = candidate_manager_id
        while curr_id:
            if curr_id in visited:
                raise BadRequestException(
                    "Manager assignment would create a circular reporting hierarchy",
                    field="manager_id",
                )
            visited.add(curr_id)
            mgr_row = db.query(Employee.manager_id).filter(Employee.id == curr_id).first()
            curr_id = mgr_row[0] if mgr_row else None

    @staticmethod
    def create_employee(db: Session, employee_in: EmployeeCreate) -> EmployeeResponse:
        existing_email = db.query(Employee).filter(Employee.email == employee_in.email).first()
        if existing_email:
            raise ConflictException(
                f"Employee with work email '{employee_in.email}' already exists",
                field="email",
            )

        dept = EmployeeService._resolve_department(db, employee_in.department_id)
        manager = EmployeeService._resolve_manager(db, employee_in.manager_id)
        role = EmployeeService._resolve_role(db, employee_in.role_id)

        if employee_in.employee_code and employee_in.employee_code.strip():
            code_val = employee_in.employee_code.strip()
            existing_code = db.query(Employee).filter(Employee.employee_code.ilike(code_val)).first()
            if existing_code:
                raise ConflictException(
                    f"Employee with code '{code_val}' already exists ({existing_code.first_name} {existing_code.last_name}).",
                    field="employee_code",
                )
            final_code = code_val
        else:
            final_code = EmployeeService._get_next_employee_code(db)

        if employee_in.exit_date and employee_in.hire_date and employee_in.exit_date < employee_in.hire_date:
            raise BadRequestException("exit_date cannot be before hire_date", field="exit_date")

        employee = Employee(
            employee_code=final_code,
            first_name=employee_in.first_name,
            last_name=employee_in.last_name,
            email=employee_in.email,
            department_id=dept.id,
            manager_id=manager.id if manager else None,
            salary=employee_in.salary,
            hire_date=employee_in.hire_date,
            work_location=employee_in.work_location,
            work_mode=employee_in.work_mode,
            employment_type=employee_in.employment_type,
            employment_status=employee_in.employment_status or ("Active" if employee_in.is_active else "Deactivated"),
            exit_type=employee_in.exit_type,
            exit_reason=employee_in.exit_reason,
            exit_date=employee_in.exit_date or (None if employee_in.is_active else date.today()),
            is_active=employee_in.is_active,
        )
        db.add(employee)

        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise ConflictException(
                f"Employee with email '{employee_in.email}' or code '{final_code}' already exists",
                field="email",
            )

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
    def get_employee(db: Session, employee_id: Any) -> EmployeeResponse:
        query = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.manager),
                selectinload(Employee.employee_roles).joinedload(EmployeeRole.role),
            )
        )
        ident_str = str(employee_id).strip()
        if ident_str.isdigit():
            employee = query.filter(Employee.id == int(ident_str)).first()
        else:
            employee = query.filter(Employee.employee_code.ilike(ident_str)).first()

        if not employee:
            raise NotFoundException(f"Employee with ID or code '{employee_id}' not found", field="id")
        return EmployeeService._format_employee_response(employee)

    @staticmethod
    def list_employees(
        db: Session,
        page: int = 1,
        size: int = 20,
        department: Optional[str] = None,
        employee_code: Optional[str] = None,
        q: Optional[str] = None,
        include_inactive: bool = False,
    ) -> PaginatedResponse[EmployeeResponse]:
        query = db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.manager),
            selectinload(Employee.employee_roles).joinedload(EmployeeRole.role),
        )

        if not include_inactive:
            query = query.filter(Employee.is_active.is_(True))

        if employee_code and employee_code.strip():
            code_term = employee_code.strip()
            query = query.filter(Employee.employee_code.ilike(f"%{code_term}%"))

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
        employee_id: Any,
        employee_in: EmployeeUpdate,
    ) -> EmployeeResponse:
        employee = EmployeeService._find_employee(db, employee_id)
        if not employee:
            raise NotFoundException(f"Employee with ID or code '{employee_id}' not found", field="id")

        update_data = employee_in.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] != employee.email:
            existing_email = db.query(Employee).filter(
                Employee.email == update_data["email"],
                Employee.id != employee.id,
            ).first()
            if existing_email:
                raise ConflictException(
                    f"Employee with work email '{update_data['email']}' already exists",
                    field="email",
                )
            employee.email = update_data["email"]

        if "department_id" in update_data and update_data["department_id"] is not None:
            dept = EmployeeService._resolve_department(db, update_data["department_id"])
            employee.department_id = dept.id

        if "manager_id" in update_data:
            mgr_val = update_data["manager_id"]
            if mgr_val is None:
                employee.manager_id = None
            else:
                manager = EmployeeService._resolve_manager(db, mgr_val)
                EmployeeService._detect_manager_cycle(db, employee.id, manager.id)
                employee.manager_id = manager.id

        if "role_id" in update_data and update_data["role_id"] is not None:
            role = EmployeeService._resolve_role(db, update_data["role_id"])
            if role:
                for er in employee.employee_roles:
                    if er.is_primary:
                        er.is_primary = False

                matching_er = next((er for er in employee.employee_roles if er.role_id == role.id), None)
                if matching_er:
                    matching_er.is_primary = True
                else:
                    db.add(EmployeeRole(employee_id=employee.id, role_id=role.id, is_primary=True))

        if "first_name" in update_data and update_data["first_name"] is not None:
            employee.first_name = update_data["first_name"]
        if "last_name" in update_data and update_data["last_name"] is not None:
            employee.last_name = update_data["last_name"]
        if "salary" in update_data and update_data["salary"] is not None:
            employee.salary = update_data["salary"]
        if "hire_date" in update_data and update_data["hire_date"] is not None:
            employee.hire_date = update_data["hire_date"]
        if "work_location" in update_data:
            employee.work_location = update_data["work_location"]
        if "work_mode" in update_data:
            employee.work_mode = update_data["work_mode"]
        if "employment_type" in update_data:
            employee.employment_type = update_data["employment_type"]
        if update_data.get("employment_status") is not None:
            employee.employment_status = update_data["employment_status"]
            employee.is_active = update_data["employment_status"] == "Active"
        elif update_data.get("is_active") is not None:
            employee.is_active = update_data["is_active"]
            if employee.is_active:
                employee.employment_status = "Active"
            elif employee.employment_status in (None, "Active"):
                employee.employment_status = "Deactivated"

        if employee.is_active:
            if any(update_data.get(k) is not None for k in ("exit_type", "exit_reason", "exit_date")):
                raise BadRequestException("Exit fields cannot be set on an active employee", field="exit_type")
            employee.exit_date = employee.exit_type = employee.exit_reason = None
        else:
            if update_data.get("exit_date") is not None:
                if update_data["exit_date"] < employee.hire_date:
                    raise BadRequestException("exit_date cannot be before hire_date", field="exit_date")
                employee.exit_date = update_data["exit_date"]
            elif not employee.exit_date:
                employee.exit_date = date.today()
            if "exit_type" in update_data:
                employee.exit_type = update_data["exit_type"]
            if "exit_reason" in update_data:
                employee.exit_reason = update_data["exit_reason"]

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ConflictException("Database integrity conflict occurred during update", field="email")

        db.refresh(employee)
        return EmployeeService._format_employee_response(employee)

    @staticmethod
    def delete_employee(db: Session, employee_id: Any) -> None:
        employee = EmployeeService._find_employee(db, employee_id)
        if not employee:
            raise NotFoundException(f"Employee with ID or code '{employee_id}' not found", field="id")

        for report in employee.direct_reports:
            report.manager_id = employee.manager_id

        employee.is_active = False
        if not employee.exit_date:
            employee.exit_date = date.today()
        if employee.employment_status in (None, "Active"):
            employee.employment_status = "Deactivated"
        db.commit()

    @staticmethod
    def get_employee_team(db: Session, employee_id: Any) -> TeamResponse:
        manager = EmployeeService._find_employee(db, employee_id)
        if not manager:
            raise NotFoundException(f"Employee with ID or code '{employee_id}' not found", field="id")

        direct_reports = db.query(Employee).filter(
            Employee.manager_id == manager.id,
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
            employment_status=e.employment_status,
            exit_type=e.exit_type,
            exit_reason=e.exit_reason,
            work_location=e.work_location,
            work_mode=e.work_mode,
            employment_type=e.employment_type,
            is_active=e.is_active,
            roles=roles_brief,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )


employee_service = EmployeeService()
