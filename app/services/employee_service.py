from datetime import date
import math
import re
from typing import Optional, Any, List
from sqlalchemy import or_, func, desc, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import settings
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
)
from app.models.department import Department
from app.models.role import Role, EmployeeRole
from app.models.employee import Employee
from app.models.salary_revision import SalaryRevision
from app.models.assignment import EmployeeAssignment
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeBrief,
    TeamResponse,
)
from app.schemas.common import PaginatedResponse
from app.schemas.assignment import EmployeeAssignmentResponse
from app.services.formatters import format_employee_response


def _escape_like(val: str) -> str:
    """Escapes SQL LIKE wildcards (% and _) and backslashes for literal substring matching."""
    return val.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class EmployeeService:
    @staticmethod
    def _find_employee(db: Session, identifier: Any) -> Optional[Employee]:
        if identifier is None:
            return None
        ident_str = str(identifier).strip()
        # Direct match on employee_id (e.g. EMP-0001)
        emp = db.query(Employee).filter(func.lower(Employee.employee_id) == ident_str.lower()).first()
        if not emp and ident_str.isdigit():
            # Support pure integer ID lookup if mapped as EMP-000X
            cand = f"EMP-{int(ident_str):04d}"
            emp = db.query(Employee).filter(Employee.employee_id == cand).first()
        return emp

    @staticmethod
    def _resolve_department(db: Session, dept_val: Any) -> Department:
        if dept_val is None:
            raise BadRequestException("department_id is required", field="department_id")
        dept_str = str(dept_val).strip()
        dept = db.query(Department).filter(
            or_(
                func.lower(Department.department_id) == dept_str.lower(),
                func.lower(Department.department_name) == dept_str.lower(),
            )
        ).first()

        if not dept:
            raise BadRequestException(
                f"Department '{dept_val}' does not exist",
                field="department_id",
            )
        if not dept.is_active:
            raise BadRequestException(
                "Department is inactive",
                field="department_id",
            )
        return dept

    @staticmethod
    def _resolve_role(db: Session, role_val: Any) -> Optional[Role]:
        if role_val is None:
            return None
        role_str = str(role_val).strip()
        role = db.query(Role).filter(
            or_(
                func.lower(Role.role_id) == role_str.lower(),
                func.lower(Role.role_title) == role_str.lower(),
            )
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
        max_code = (
            db.query(func.max(Employee.employee_id))
            .filter(
                Employee.employee_id.like("EMP-%"),
                func.length(Employee.employee_id) == 8,
            )
            .scalar()
        )
        if max_code:
            match = re.search(r"EMP-(\d{4})", max_code, re.IGNORECASE)
            if match:
                return f"EMP-{int(match.group(1)) + 1:04d}"
        return "EMP-0001"

    @staticmethod
    def _detect_manager_cycle(db: Session, employee_id: str, candidate_manager_id: str) -> None:
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
            mgr_row = db.query(Employee.manager_id).filter(Employee.employee_id == curr_id).first()
            curr_id = mgr_row[0] if mgr_row else None

    @staticmethod
    def create_employee(db: Session, employee_in: EmployeeCreate) -> EmployeeResponse:
        clean_email = str(employee_in.email).strip().lower()
        existing_email = db.query(Employee).filter(func.lower(Employee.work_email) == clean_email).first()
        if existing_email:
            raise ConflictException(
                f"Employee with work email '{clean_email}' already exists",
                field="email",
            )

        dept = EmployeeService._resolve_department(db, employee_in.department_id)
        manager = EmployeeService._resolve_manager(db, employee_in.manager_id)

        # Default role to first department role or specified role
        role_id_in = employee_in.role_id or employee_in.primary_role_id
        if role_id_in is not None:
            role = EmployeeService._resolve_role(db, role_id_in)
        else:
            role = db.query(Role).filter(Role.department_id == dept.department_id).first()
            if not role:
                role = db.query(Role).first()

        code_candidate = employee_in.employee_id or employee_in.employee_code
        if code_candidate and code_candidate.strip():
            code_val = code_candidate.strip().upper()
            if not re.match(r"^EMP-\d{4}$", code_val):
                raise BadRequestException(
                    "Employee code must follow the standard 'EMP-XXXX' format with 4 digits (e.g. EMP-0001)",
                    field="employee_code",
                )
            existing_code = db.query(Employee).filter(func.lower(Employee.employee_id) == code_val.lower()).first()
            if existing_code:
                raise ConflictException(
                    f"Employee with code '{code_val}' already exists ({existing_code.first_name} {existing_code.last_name}).",
                    field="employee_code",
                )
            final_code = code_val
        else:
            final_code = EmployeeService._get_next_employee_code(db)

        full_name = f"{employee_in.first_name.strip()} {employee_in.last_name.strip()}"
        initial_status = employee_in.employment_status or ("Active" if employee_in.is_active else "Deactivated")
        exit_dt = employee_in.exit_date or (None if employee_in.is_active else settings.DEMO_TODAY)

        employee = Employee(
            employee_id=final_code,
            first_name=employee_in.first_name.strip(),
            last_name=employee_in.last_name.strip(),
            full_name=full_name,
            work_email=clean_email,
            department_id=dept.department_id,
            role_id=role.role_id if role else None,
            manager_id=manager.employee_id if manager else None,
            salary=employee_in.salary,
            hire_date=employee_in.hire_date,
            phone_number=employee_in.phone_number,
            gender=employee_in.gender,
            date_of_birth=employee_in.date_of_birth,
            work_location=employee_in.work_location,
            work_mode=employee_in.work_mode,
            highest_education=employee_in.highest_education,
            prior_experience_years=employee_in.prior_experience_years,
            career_gap_months=employee_in.career_gap_months or 0,
            commute_distance_km=employee_in.commute_distance_km,
            pf_applicable=employee_in.pf_applicable or "Y",
            esi_applicable=employee_in.esi_applicable or "N",
            notice_period_days=employee_in.notice_period_days or 30,
            resignation_date=employee_in.resignation_date,
            employment_type=employee_in.employment_type or "Permanent",
            employment_status=initial_status,
            exit_type=employee_in.exit_type,
            exit_reason=employee_in.exit_reason,
            exit_date=exit_dt,
            is_active=employee_in.is_active,
        )
        db.add(employee)

        try:
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            err_msg = str(exc).lower()
            if "employee_id" in err_msg or "employee_code" in err_msg or "pkey" in err_msg:
                raise ConflictException(
                    f"Employee with code '{final_code}' already exists",
                    field="employee_code",
                )
            raise ConflictException(
                f"Employee with work email '{clean_email}' already exists",
                field="email",
            )

        # Log initial career assignment
        assignment_id = f"ASG-{final_code[4:]}-01"
        db.add(
            EmployeeAssignment(
                assignment_id=assignment_id,
                employee_id=employee.employee_id,
                effective_from=employee.hire_date,
                effective_to=None,
                department_id=employee.department_id,
                role_id=employee.role_id,
                job_level=str(role.level) if role and role.level is not None else None,
                manager_id=employee.manager_id,
                change_reason="Joining",
            )
        )

        db.commit()
        db.refresh(employee)
        return format_employee_response(employee)

    @staticmethod
    def get_employee(db: Session, employee_id: Any) -> EmployeeResponse:
        query = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.role),
                joinedload(Employee.manager),
            )
        )
        employee = EmployeeService._find_employee(db, employee_id)
        if not employee:
            raise NotFoundException(f"Employee with ID or code '{employee_id}' not found", field="id")
        return format_employee_response(employee)

    @staticmethod
    def list_employees(
        db: Session,
        page: int = 1,
        size: int = 20,
        department_id: Optional[str] = None,
        role_id: Optional[str] = None,
        employment_status: Optional[str] = None,
        work_location: Optional[str] = None,
        work_mode: Optional[str] = None,
        manager_id: Optional[str] = None,
        hire_date_from: Optional[date] = None,
        hire_date_to: Optional[date] = None,
        department: Optional[str] = None,
        employee_code: Optional[str] = None,
        q: Optional[str] = None,
        sort: Optional[str] = None,
        include_inactive: bool = False,
    ) -> PaginatedResponse[EmployeeResponse]:
        query = db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.role),
            joinedload(Employee.manager),
        )

        if not include_inactive:
            query = query.filter(Employee.is_active.is_(True))

        target_dept = department_id or department
        if target_dept and target_dept.strip():
            dept_term = target_dept.strip()
            dept_escaped = _escape_like(dept_term)
            query = query.join(Employee.department).filter(
                or_(
                    func.lower(Department.department_id) == dept_term.lower(),
                    Department.department_name.ilike(f"%{dept_escaped}%", escape="\\"),
                )
            )

        if role_id and role_id.strip():
            r_term = role_id.strip()
            query = query.filter(
                or_(
                    func.lower(Employee.role_id) == r_term.lower(),
                    Employee.role.has(Role.role_title.ilike(f"%{_escape_like(r_term)}%", escape="\\")),
                )
            )

        if employment_status and employment_status.strip():
            query = query.filter(func.lower(Employee.employment_status) == employment_status.strip().lower())

        if work_location and work_location.strip():
            query = query.filter(Employee.work_location.ilike(f"%{_escape_like(work_location.strip())}%", escape="\\"))

        if work_mode and work_mode.strip():
            query = query.filter(func.lower(Employee.work_mode) == work_mode.strip().lower())

        if manager_id and manager_id.strip():
            mgr = EmployeeService._find_employee(db, manager_id.strip())
            if mgr:
                query = query.filter(Employee.manager_id == mgr.employee_id)
            else:
                query = query.filter(func.lower(Employee.manager_id) == manager_id.strip().lower())

        if hire_date_from:
            query = query.filter(Employee.hire_date >= hire_date_from)
        if hire_date_to:
            query = query.filter(Employee.hire_date <= hire_date_to)

        target_code = employee_code
        if target_code and target_code.strip():
            code_term = _escape_like(target_code.strip())
            query = query.filter(Employee.employee_id.ilike(f"%{code_term}%", escape="\\"))

        if q and q.strip():
            search = f"%{_escape_like(q.strip())}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search, escape="\\"),
                    Employee.last_name.ilike(search, escape="\\"),
                    Employee.full_name.ilike(search, escape="\\"),
                    Employee.work_email.ilike(search, escape="\\"),
                    Employee.employee_id.ilike(search, escape="\\"),
                )
            )

        # Sorting support: field or -field
        sort_col = Employee.employee_id.asc()
        if sort and sort.strip():
            s = sort.strip()
            descending = s.startswith("-")
            field_name = s[1:] if descending else s
            order_fn = desc if descending else asc

            sort_map = {
                "hire_date": Employee.hire_date,
                "first_name": Employee.first_name,
                "last_name": Employee.last_name,
                "full_name": Employee.full_name,
                "email": Employee.work_email,
                "work_email": Employee.work_email,
                "salary": Employee.salary,
                "employee_id": Employee.employee_id,
                "id": Employee.employee_id,
                "department_id": Employee.department_id,
                "role_id": Employee.role_id,
                "employment_status": Employee.employment_status,
            }
            if field_name in sort_map:
                sort_col = order_fn(sort_map[field_name])

        query = query.order_by(sort_col)

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
    def _deactivate_employee_helper(db: Session, employee: Employee) -> None:
        """Shared deactivation routine: reparents direct reports, sets is_active=False and DEMO_TODAY exit date."""
        for report in employee.direct_reports:
            report.manager_id = employee.manager_id
        employee.is_active = False
        if not employee.exit_date:
            employee.exit_date = settings.DEMO_TODAY
        if employee.employment_status in (None, "Active"):
            employee.employment_status = "Deactivated"

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

        new_email = update_data.get("email") or update_data.get("work_email")
        if new_email:
            clean_email = str(new_email).strip().lower()
            if clean_email != employee.work_email.lower():
                existing_email = db.query(Employee).filter(
                    func.lower(Employee.work_email) == clean_email,
                    Employee.employee_id != employee.employee_id,
                ).first()
                if existing_email:
                    raise ConflictException(
                        f"Employee with work email '{clean_email}' already exists",
                        field="email",
                    )
                employee.work_email = clean_email

        old_dept_id = employee.department_id
        old_mgr_id = employee.manager_id
        old_role_id = employee.role_id

        if "department_id" in update_data and update_data["department_id"] is not None:
            dept = EmployeeService._resolve_department(db, update_data["department_id"])
            employee.department_id = dept.department_id

        if "manager_id" in update_data:
            mgr_val = update_data["manager_id"]
            if mgr_val is None:
                employee.manager_id = None
            else:
                manager = EmployeeService._resolve_manager(db, mgr_val)
                EmployeeService._detect_manager_cycle(db, employee.employee_id, manager.employee_id)
                employee.manager_id = manager.employee_id

        role_val = update_data.get("role_id") or update_data.get("primary_role_id")
        if role_val is not None:
            role = EmployeeService._resolve_role(db, role_val)
            if role:
                employee.role_id = role.role_id
                for er in employee.employee_roles:
                    if er.is_primary:
                        er.role_id = role.role_id

        # Record assignment progression if org hierarchy or role changed
        if (
            employee.department_id != old_dept_id
            or employee.manager_id != old_mgr_id
            or employee.role_id != old_role_id
        ):
            open_asg = (
                db.query(EmployeeAssignment)
                .filter(EmployeeAssignment.employee_id == employee.employee_id, EmployeeAssignment.effective_to.is_(None))
                .order_by(EmployeeAssignment.effective_from.desc())
                .first()
            )
            if open_asg:
                open_asg.effective_to = settings.DEMO_TODAY

            next_seq = (
                db.query(func.count(EmployeeAssignment.assignment_id))
                .filter(EmployeeAssignment.employee_id == employee.employee_id)
                .scalar()
                or 0
            ) + 1
            asg_code = f"ASG-{employee.employee_id[4:]}-{next_seq:02d}"

            db.add(
                EmployeeAssignment(
                    assignment_id=asg_code,
                    employee_id=employee.employee_id,
                    effective_from=settings.DEMO_TODAY,
                    effective_to=None,
                    department_id=employee.department_id,
                    role_id=employee.role_id,
                    job_level=str(employee.role.level) if employee.role and employee.role.level is not None else "1",
                    manager_id=employee.manager_id,
                    change_reason="API Assignment Update",
                )
            )

        if "first_name" in update_data and update_data["first_name"] is not None:
            employee.first_name = update_data["first_name"].strip()
        if "last_name" in update_data and update_data["last_name"] is not None:
            employee.last_name = update_data["last_name"].strip()
        employee.full_name = f"{employee.first_name} {employee.last_name}"

        if "salary" in update_data and update_data["salary"] is not None and update_data["salary"] != employee.salary:
            old_salary = employee.salary
            new_salary = update_data["salary"]
            pct = round(((new_salary - old_salary) / old_salary) * 100, 2) if old_salary and old_salary > 0 else None
            employee.salary = new_salary

            rev_seq = (
                db.query(func.count(SalaryRevision.revision_id))
                .filter(SalaryRevision.employee_id == employee.employee_id)
                .scalar()
                or 0
            ) + 1
            rev_code = f"REV-{employee.employee_id[4:]}-{rev_seq:02d}"

            db.add(
                SalaryRevision(
                    revision_id=rev_code,
                    employee_id=employee.employee_id,
                    effective_from=settings.DEMO_TODAY,
                    revision_reason="API Compensation Adjustment",
                    previous_annual_fixed=old_salary,
                    new_annual_fixed=new_salary,
                    pct_change=pct,
                    role_id_after=employee.role_id,
                    approved_by="HR Admin",
                )
            )

        for fld in (
            "hire_date", "phone_number", "work_location", "work_mode",
            "employment_type", "gender", "date_of_birth", "highest_education",
            "prior_experience_years", "career_gap_months", "commute_distance_km",
            "pf_applicable", "esi_applicable", "notice_period_days", "resignation_date"
        ):
            if fld in update_data and update_data[fld] is not None:
                setattr(employee, fld, update_data[fld])

        deactivating = False
        if update_data.get("employment_status") is not None:
            new_status = update_data["employment_status"]
            employee.employment_status = new_status
            if new_status == "Active":
                employee.is_active = True
            else:
                deactivating = True
        elif update_data.get("is_active") is not None:
            if update_data["is_active"]:
                employee.is_active = True
                employee.employment_status = "Active"
            else:
                deactivating = True

        if deactivating:
            EmployeeService._deactivate_employee_helper(db, employee)
            if update_data.get("employment_status") is not None:
                employee.employment_status = update_data["employment_status"]

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
                employee.exit_date = settings.DEMO_TODAY
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
        return format_employee_response(employee)

    @staticmethod
    def delete_employee(db: Session, employee_id: Any) -> None:
        employee = EmployeeService._find_employee(db, employee_id)
        if not employee:
            raise NotFoundException(f"Employee with ID or code '{employee_id}' not found", field="id")

        EmployeeService._deactivate_employee_helper(db, employee)
        db.commit()

    @staticmethod
    def get_employee_team(db: Session, employee_id: Any) -> TeamResponse:
        manager = EmployeeService._find_employee(db, employee_id)
        if not manager:
            raise NotFoundException(f"Employee with ID or code '{employee_id}' not found", field="id")

        direct_reports = db.query(Employee).filter(
            Employee.manager_id == manager.employee_id,
            Employee.is_active.is_(True),
        ).order_by(Employee.last_name.asc(), Employee.first_name.asc()).all()

        manager_brief = EmployeeBrief(
            id=manager.employee_id,
            employee_id=manager.employee_id,
            employee_code=manager.employee_id,
            first_name=manager.first_name,
            last_name=manager.last_name,
            full_name=manager.full_name,
            email=manager.work_email,
            work_email=manager.work_email,
            department_id=manager.department_id,
            role_id=manager.role_id,
            is_active=manager.is_active,
        )

        reports_brief = [
            EmployeeBrief(
                id=rep.employee_id,
                employee_id=rep.employee_id,
                employee_code=rep.employee_id,
                first_name=rep.first_name,
                last_name=rep.last_name,
                full_name=rep.full_name,
                email=rep.work_email,
                work_email=rep.work_email,
                department_id=rep.department_id,
                role_id=rep.role_id,
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
    def get_employee_assignments(db: Session, employee_id: Any) -> List[EmployeeAssignmentResponse]:
        employee = EmployeeService._find_employee(db, employee_id)
        if not employee:
            raise NotFoundException(f"Employee with ID or code '{employee_id}' not found", field="id")

        asgs = (
            db.query(EmployeeAssignment)
            .filter(EmployeeAssignment.employee_id == employee.employee_id)
            .order_by(EmployeeAssignment.effective_from.asc())
            .all()
        )
        return [
            EmployeeAssignmentResponse(
                assignment_id=a.assignment_id,
                id=a.assignment_id,
                employee_id=a.employee_id,
                effective_from=a.effective_from,
                effective_to=a.effective_to,
                department_id=a.department_id,
                role_id=a.role_id,
                job_level=a.job_level,
                manager_id=a.manager_id,
                change_reason=a.change_reason,
            )
            for a in asgs
        ]


employee_service = EmployeeService()
