"""Shared response formatters and mappers for Aura Workforce OS services."""

from app.models.employee import Employee
from app.schemas.employee import EmployeeResponse
from app.schemas.role import RoleBrief


def format_employee_response(e: Employee) -> EmployeeResponse:
    """Formats an Employee SQLAlchemy model instance into an EmployeeResponse schema."""
    roles_brief = []
    role_brief = None

    if e.role is not None:
        role_brief = RoleBrief(
            id=e.role.role_id,
            role_id=e.role.role_id,
            code=e.role.role_id,
            title=e.role.role_title,
            level=e.role.level,
            is_primary=True,
        )
        roles_brief.append(role_brief)

    # If any additional roles exist in employee_roles
    for er in (getattr(e, "employee_roles", None) or []):
        if er.role is not None and er.role.role_id != e.role_id:
            roles_brief.append(
                RoleBrief(
                    id=er.role.role_id,
                    role_id=er.role.role_id,
                    code=er.role.role_id,
                    title=er.role.role_title,
                    level=er.role.level,
                    is_primary=er.is_primary,
                )
            )

    return EmployeeResponse(
        id=e.employee_id,
        employee_id=e.employee_id,
        employee_code=e.employee_id,
        first_name=e.first_name,
        last_name=e.last_name,
        full_name=e.full_name or f"{e.first_name} {e.last_name}",
        email=e.work_email,
        work_email=e.work_email,
        phone_number=e.phone_number,
        gender=e.gender,
        date_of_birth=e.date_of_birth,
        department_id=e.department_id,
        department=e.department,
        role_id=e.role_id,
        role=role_brief,
        manager_id=e.manager_id,
        manager=e.manager,
        salary=e.salary,
        hire_date=e.hire_date,
        exit_date=e.exit_date,
        employment_status=e.employment_status,
        employment_type=e.employment_type,
        exit_type=e.exit_type,
        exit_reason=e.exit_reason,
        work_location=e.work_location,
        work_mode=e.work_mode,
        highest_education=e.highest_education,
        prior_experience_years=e.prior_experience_years,
        career_gap_months=e.career_gap_months,
        commute_distance_km=e.commute_distance_km,
        pf_applicable=e.pf_applicable,
        esi_applicable=e.esi_applicable,
        notice_period_days=e.notice_period_days,
        resignation_date=e.resignation_date,
        is_active=e.is_active,
        roles=roles_brief,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )
