from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Date, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.department import Department
    from app.models.role import Role


class EmployeeAssignment(Base, TimestampMixin):
    __tablename__ = "employee_assignments"

    assignment_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    department_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("departments.department_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("roles.role_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    manager_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    change_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="assignments",
        foreign_keys=[employee_id],
    )
    department: Mapped[Optional["Department"]] = relationship("Department")
    role: Mapped[Optional["Role"]] = relationship("Role")

    @hybrid_property
    def id(self) -> str:
        return self.assignment_id

    @id.setter
    def id(self, val: str):
        self.assignment_id = val

    @hybrid_property
    def assignment_code(self) -> str:
        return self.assignment_id

    @assignment_code.setter
    def assignment_code(self, val: str):
        self.assignment_id = val

    def __repr__(self) -> str:
        return f"<EmployeeAssignment(id='{self.assignment_id}', emp='{self.employee_id}', from={self.effective_from})>"

