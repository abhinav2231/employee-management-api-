"""Shared response formatters and mappers for Aura Workforce OS services."""

from app.models.employee import Employee
from app.schemas.employee import EmployeeResponse
from app.schemas.role import RoleBrief


def format_employee_response(e: Employee) -> EmployeeResponse:
    """Formats an Employee SQLAlchemy model instance into an EmployeeResponse schema."""
    roles_brief = [
        RoleBrief(
            id=er.role.id,
            code=er.role.code,
            title=er.role.title,
            level=er.role.level,
            is_primary=er.is_primary,
        )
        for er in (e.employee_roles or [])
        if er.role is not None
    ]

    return EmployeeResponse(
        id=e.id,
        employee_code=e.employee_code,
        first_name=e.first_name,
        last_name=e.last_name,
        email=e.email,
        phone_number=e.phone_number,
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
