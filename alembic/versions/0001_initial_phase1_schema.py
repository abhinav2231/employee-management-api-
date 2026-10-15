"""initial_phase1_schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. departments
    op.create_table(
        "departments",
        sa.Column("department_id", sa.String(length=20), nullable=False),
        sa.Column("department_name", sa.String(length=100), nullable=False),
        sa.Column("cost_center", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("department_id"),
    )
    op.create_index(op.f("ix_departments_department_name"), "departments", ["department_name"], unique=True)

    # 2. roles
    op.create_table(
        "roles",
        sa.Column("role_id", sa.String(length=20), nullable=False),
        sa.Column("department_id", sa.String(length=20), nullable=True),
        sa.Column("role_title", sa.String(length=100), nullable=False),
        sa.Column("level", sa.String(length=50), nullable=True),
        sa.Column("grade", sa.String(length=50), nullable=True),
        sa.Column("band_min_annual", sa.Integer(), nullable=True),
        sa.Column("band_mid_annual", sa.Integer(), nullable=True),
        sa.Column("band_max_annual", sa.Integer(), nullable=True),
        sa.Column("overtime_eligible", sa.String(length=5), nullable=False),
        sa.Column("band_year", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.department_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("role_id"),
    )
    op.create_index(op.f("ix_roles_department_id"), "roles", ["department_id"], unique=False)
    op.create_index(op.f("ix_roles_role_title"), "roles", ["role_title"], unique=True)

    # 3. employees
    op.create_table(
        "employees",
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("work_email", sa.String(length=255), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("exit_date", sa.Date(), nullable=True),
        sa.Column("employment_status", sa.String(length=50), nullable=False),
        sa.Column("employment_type", sa.String(length=50), nullable=True),
        sa.Column("department_id", sa.String(length=20), nullable=False),
        sa.Column("role_id", sa.String(length=20), nullable=True),
        sa.Column("manager_id", sa.String(length=20), nullable=True),
        sa.Column("work_location", sa.String(length=50), nullable=True),
        sa.Column("work_mode", sa.String(length=50), nullable=True),
        sa.Column("highest_education", sa.String(length=100), nullable=True),
        sa.Column("prior_experience_years", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("career_gap_months", sa.Integer(), nullable=True),
        sa.Column("commute_distance_km", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("pf_applicable", sa.String(length=5), nullable=True),
        sa.Column("esi_applicable", sa.String(length=5), nullable=True),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column("resignation_date", sa.Date(), nullable=True),
        sa.Column("exit_type", sa.String(length=50), nullable=True),
        sa.Column("exit_reason", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=30), nullable=True),
        sa.Column("salary", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("salary IS NULL OR salary > 0", name="ck_employees_salary_positive"),
        sa.CheckConstraint("exit_date IS NULL OR exit_date >= hire_date", name="ck_employees_exit_after_hire"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.department_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.employee_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("employee_id"),
    )
    op.create_index(op.f("ix_employees_department_id"), "employees", ["department_id"], unique=False)
    op.create_index("ix_employees_dept_active", "employees", ["department_id", "is_active"], unique=False)
    op.create_index(op.f("ix_employees_employment_status"), "employees", ["employment_status"], unique=False)
    op.create_index(op.f("ix_employees_full_name"), "employees", ["full_name"], unique=False)
    op.create_index(op.f("ix_employees_hire_date"), "employees", ["hire_date"], unique=False)
    op.create_index(op.f("ix_employees_is_active"), "employees", ["is_active"], unique=False)
    op.create_index(op.f("ix_employees_manager_id"), "employees", ["manager_id"], unique=False)
    op.create_index("ix_employees_name", "employees", ["last_name", "first_name"], unique=False)
    op.create_index(op.f("ix_employees_role_id"), "employees", ["role_id"], unique=False)
    op.create_index("ix_employees_status", "employees", ["employment_status"], unique=False)
    op.create_index(op.f("ix_employees_work_email"), "employees", ["work_email"], unique=True)
    op.create_index(op.f("ix_employees_work_location"), "employees", ["work_location"], unique=False)
    op.create_index(op.f("ix_employees_work_mode"), "employees", ["work_mode"], unique=False)

    # 4. employee_roles
    op.create_table(
        "employee_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("role_id", sa.String(length=20), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "role_id", name="uq_employee_role"),
    )
    op.create_index(op.f("ix_employee_roles_employee_id"), "employee_roles", ["employee_id"], unique=False)
    op.create_index(op.f("ix_employee_roles_role_id"), "employee_roles", ["role_id"], unique=False)

    # 5. employee_assignments
    op.create_table(
        "employee_assignments",
        sa.Column("assignment_id", sa.String(length=30), nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("department_id", sa.String(length=20), nullable=True),
        sa.Column("role_id", sa.String(length=20), nullable=True),
        sa.Column("job_level", sa.String(length=50), nullable=True),
        sa.Column("manager_id", sa.String(length=20), nullable=True),
        sa.Column("change_reason", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.department_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.employee_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("assignment_id"),
    )
    op.create_index(op.f("ix_employee_assignments_department_id"), "employee_assignments", ["department_id"], unique=False)
    op.create_index(op.f("ix_employee_assignments_effective_from"), "employee_assignments", ["effective_from"], unique=False)
    op.create_index(op.f("ix_employee_assignments_employee_id"), "employee_assignments", ["employee_id"], unique=False)
    op.create_index(op.f("ix_employee_assignments_manager_id"), "employee_assignments", ["manager_id"], unique=False)
    op.create_index(op.f("ix_employee_assignments_role_id"), "employee_assignments", ["role_id"], unique=False)

    # 6. salary_revisions
    op.create_table(
        "salary_revisions",
        sa.Column("revision_id", sa.String(length=30), nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("revision_reason", sa.String(length=100), nullable=True),
        sa.Column("previous_annual_fixed", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("new_annual_fixed", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("pct_change", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("role_id_after", sa.String(length=20), nullable=True),
        sa.Column("approved_by", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("revision_id"),
    )
    op.create_index(op.f("ix_salary_revisions_effective_from"), "salary_revisions", ["effective_from"], unique=False)
    op.create_index(op.f("ix_salary_revisions_employee_id"), "salary_revisions", ["employee_id"], unique=False)

    # 7. salary_structures
    op.create_table(
        "salary_structures",
        sa.Column("structure_id", sa.String(length=30), nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("component_id", sa.String(length=20), nullable=False),
        sa.Column("component_name", sa.String(length=100), nullable=False),
        sa.Column("component_type", sa.String(length=50), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("revision_id", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("structure_id"),
    )
    op.create_index(op.f("ix_salary_structures_component_id"), "salary_structures", ["component_id"], unique=False)
    op.create_index(op.f("ix_salary_structures_effective_from"), "salary_structures", ["effective_from"], unique=False)
    op.create_index(op.f("ix_salary_structures_employee_id"), "salary_structures", ["employee_id"], unique=False)

    # 8. salary_records
    op.create_table(
        "salary_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("pay_period", sa.String(length=10), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("base_salary", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("allowances", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("bonuses", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("deductions", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("net_salary", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("payment_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("base_salary >= 0", name="ck_salary_base_positive"),
        sa.CheckConstraint("net_salary >= 0", name="ck_salary_net_positive"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "pay_period", name="uq_salary_employee_period"),
    )
    op.create_index("ix_salary_emp_period", "salary_records", ["employee_id", "pay_period"], unique=False)
    op.create_index(op.f("ix_salary_records_employee_id"), "salary_records", ["employee_id"], unique=False)
    op.create_index(op.f("ix_salary_records_pay_period"), "salary_records", ["pay_period"], unique=False)

    # 9. attendance
    op.create_table(
        "attendance",
        sa.Column("attendance_id", sa.String(length=30), nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("weekday", sa.String(length=10), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("leave_type_code", sa.String(length=20), nullable=True),
        sa.Column("check_in", sa.String(length=10), nullable=True),
        sa.Column("check_out", sa.String(length=10), nullable=True),
        sa.Column("hours_worked", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("overtime_hours", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("late_flag", sa.String(length=5), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("data_quality_flag", sa.String(length=50), nullable=True),
        sa.Column("department_id", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.department_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.employee_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("attendance_id"),
        sa.UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
    )
    op.create_index(op.f("ix_attendance_attendance_date"), "attendance", ["attendance_date"], unique=False)
    op.create_index(op.f("ix_attendance_department_id"), "attendance", ["department_id"], unique=False)
    op.create_index("ix_attendance_emp_date", "attendance", ["employee_id", "attendance_date"], unique=False)
    op.create_index(op.f("ix_attendance_employee_id"), "attendance", ["employee_id"], unique=False)


def downgrade() -> None:
    op.drop_table("attendance")
    op.drop_table("salary_records")
    op.drop_table("salary_structures")
    op.drop_table("salary_revisions")
    op.drop_table("employee_assignments")
    op.drop_table("employee_roles")
    op.drop_table("employees")
    op.drop_table("roles")
    op.drop_table("departments")
