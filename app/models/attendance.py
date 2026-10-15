from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Date,
    Numeric,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"

    attendance_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    weekday: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    leave_type_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    check_in: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    check_out: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    hours_worked: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    overtime_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    late_flag: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data_quality_flag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    department_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("departments.department_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
        Index("ix_attendance_emp_date", "employee_id", "attendance_date"),
    )

    employee: Mapped["Employee"] = relationship("Employee", back_populates="attendances")

    def __init__(self, **kwargs):
        if "employee_id" in kwargs:
            kwargs["employee_id"] = str(kwargs["employee_id"])
        if "date" in kwargs and "attendance_date" not in kwargs:
            kwargs["attendance_date"] = kwargs.pop("date")
        if "notes" in kwargs and "data_quality_flag" not in kwargs:
            kwargs["data_quality_flag"] = kwargs.pop("notes")
        if "attendance_id" not in kwargs:
            import uuid
            kwargs["attendance_id"] = f"ATT-{uuid.uuid4().hex[:8].upper()}"
        super().__init__(**kwargs)

    @hybrid_property
    def id(self) -> str:
        return self.attendance_id

    @id.setter
    def id(self, val: str):
        self.attendance_id = val

    @hybrid_property
    def date(self) -> date:
        return self.attendance_date

    @date.setter
    def date(self, val: date):
        self.attendance_date = val

    @hybrid_property
    def notes(self) -> Optional[str]:
        return self.data_quality_flag

    @notes.setter
    def notes(self, val: Optional[str]):
        self.data_quality_flag = val

    def __repr__(self) -> str:
        return f"<Attendance(id='{self.attendance_id}', emp='{self.employee_id}', date={self.attendance_date}, status='{self.status}')>"
