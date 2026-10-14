from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Date, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.department import Department
    from app.models.role import Role


class EmployeeAssignment(Base, TimestampMixin):
    __tablename__ = "employee_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assignment_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    change_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    employee: Mapped["Employee"] = relationship("Employee", foreign_keys=[employee_id])
    department: Mapped[Optional["Department"]] = relationship("Department")
    role: Mapped[Optional["Role"]] = relationship("Role")

    def __repr__(self) -> str:
        return f"<EmployeeAssignment(code='{self.assignment_code}', employee_id={self.employee_id}, reason='{self.change_reason}')>"
