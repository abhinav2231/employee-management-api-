from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Boolean,
    Date,
    Integer,
    Numeric,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.role import Role, EmployeeRole
    from app.models.attendance import Attendance
    from app.models.salary import SalaryRecord
    from app.models.assignment import EmployeeAssignment
    from app.models.salary_revision import SalaryRevision
    from app.models.salary_structure import SalaryStructure


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    work_email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    exit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    employment_status: Mapped[str] = mapped_column(String(50), default="Active", nullable=False, index=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), default="Permanent", nullable=True)

    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.department_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("roles.role_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    manager_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    work_location: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    work_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    highest_education: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prior_experience_years: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    career_gap_months: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    commute_distance_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    pf_applicable: Mapped[Optional[str]] = mapped_column(String(5), default="Y", nullable=True)
    esi_applicable: Mapped[Optional[str]] = mapped_column(String(5), default="N", nullable=True)
    notice_period_days: Mapped[Optional[int]] = mapped_column(Integer, default=30, nullable=True)
    resignation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    exit_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    exit_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("salary IS NULL OR salary > 0", name="ck_employees_salary_positive"),
        CheckConstraint("exit_date IS NULL OR exit_date >= hire_date", name="ck_employees_exit_after_hire"),
        Index("ix_employees_name", "last_name", "first_name"),
        Index("ix_employees_dept_active", "department_id", "is_active"),
        Index("ix_employees_status", "employment_status"),
        Index("ix_employees_full_name", "full_name"),
    )

    department: Mapped["Department"] = relationship("Department", back_populates="employees")
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="employees")
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        remote_side="[Employee.employee_id]",
        back_populates="direct_reports",
    )
    direct_reports: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="manager",
    )

    employee_roles: Mapped[list["EmployeeRole"]] = relationship(
        "EmployeeRole",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    attendances: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    salary_records: Mapped[list["SalaryRecord"]] = relationship(
        "SalaryRecord",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    assignments: Mapped[list["EmployeeAssignment"]] = relationship(
        "EmployeeAssignment",
        back_populates="employee",
        cascade="all, delete-orphan",
        foreign_keys="[EmployeeAssignment.employee_id]",
    )

    salary_revisions: Mapped[list["SalaryRevision"]] = relationship(
        "SalaryRevision",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    salary_structures: Mapped[list["SalaryStructure"]] = relationship(
        "SalaryStructure",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    def __init__(self, **kwargs):
        if "employee_code" in kwargs and "employee_id" not in kwargs:
            kwargs["employee_id"] = kwargs.pop("employee_code")
        if "id" in kwargs and "employee_id" not in kwargs:
            kwargs["employee_id"] = str(kwargs.pop("id"))
        if "email" in kwargs and "work_email" not in kwargs:
            kwargs["work_email"] = kwargs.pop("email")
        if "department_id" in kwargs:
            kwargs["department_id"] = str(kwargs["department_id"])
        if "role_id" in kwargs and kwargs["role_id"] is not None:
            kwargs["role_id"] = str(kwargs["role_id"])
        if "manager_id" in kwargs and kwargs["manager_id"] is not None:
            kwargs["manager_id"] = str(kwargs["manager_id"])
        if "full_name" not in kwargs and "first_name" in kwargs and "last_name" in kwargs:
            kwargs["full_name"] = f"{kwargs['first_name']} {kwargs['last_name']}"
        if "employee_id" not in kwargs:
            import uuid
            kwargs["employee_id"] = f"EMP-{uuid.uuid4().hex[:4].upper()}"
        super().__init__(**kwargs)

    @hybrid_property
    def id(self) -> str:
        return self.employee_id

    @id.setter
    def id(self, val: str):
        self.employee_id = val

    @hybrid_property
    def employee_code(self) -> str:
        return self.employee_id

    @employee_code.setter
    def employee_code(self, val: str):
        self.employee_id = val

    @hybrid_property
    def email(self) -> str:
        return self.work_email

    @email.setter
    def email(self, val: str):
        self.work_email = val

    def __repr__(self) -> str:
        return f"<Employee(id='{self.employee_id}', email='{self.work_email}', status='{self.employment_status}')>"

