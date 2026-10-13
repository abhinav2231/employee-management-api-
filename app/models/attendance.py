from datetime import date, time
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Date,
    Time,
    Numeric,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class Attendance(Base, TimestampMixin):
    """
    Daily attendance record for workforce management and payroll tracking,
    linked directly to an Employee.
    """
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # PRESENT, REMOTE, ON_LEAVE, HALF_DAY, ABSENT
    check_in: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    check_out: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    hours_worked: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),
        Index("ix_attendance_emp_date", "employee_id", "date"),
    )

    employee: Mapped["Employee"] = relationship("Employee", back_populates="attendances")

    def __repr__(self) -> str:
        return (
            f"<Attendance(id={self.id}, employee_id={self.employee_id}, "
            f"date='{self.date}', status='{self.status}', hours={self.hours_worked})>"
        )
