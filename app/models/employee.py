from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Boolean,
    Date,
    Numeric,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.role import EmployeeRole
    from app.models.attendance import Attendance
    from app.models.salary import SalaryRecord
    from app.models.assignment import EmployeeAssignment
    from app.models.salary_revision import SalaryRevision


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    work_location: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    work_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    employment_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    exit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    exit_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    exit_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pf_applicable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    esi_applicable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("salary > 0", name="ck_employees_salary_positive"),
        Index("ix_employees_name", "last_name", "first_name"),
        Index("ix_employees_dept_active", "department_id", "is_active"),
    )

    department: Mapped["Department"] = relationship("Department", back_populates="employees")
    
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        remote_side="[Employee.id]",
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

    def __repr__(self) -> str:
        return (
            f"<Employee(id={self.id}, name='{self.first_name} {self.last_name}', "
            f"email='{self.email}', department_id={self.department_id}, "
            f"manager_id={self.manager_id}, is_active={self.is_active})>"
        )
