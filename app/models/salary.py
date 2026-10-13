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
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class SalaryRecord(Base, TimestampMixin):
    """
    Periodic salary, compensation, and payroll record linked directly to an Employee.
    """
    __tablename__ = "salary_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pay_period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # YYYY-MM (e.g. '2026-06')
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Financial breakdown
    base_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    allowances: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    bonuses: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default="PAID", nullable=False)  # PAID, PROCESSED, PENDING

    __table_args__ = (
        UniqueConstraint("employee_id", "pay_period", name="uq_salary_employee_period"),
        CheckConstraint("base_salary >= 0", name="ck_salary_base_positive"),
        CheckConstraint("net_salary >= 0", name="ck_salary_net_positive"),
        Index("ix_salary_emp_period", "employee_id", "pay_period"),
    )

    employee: Mapped["Employee"] = relationship("Employee", back_populates="salary_records")

    def __repr__(self) -> str:
        return (
            f"<SalaryRecord(id={self.id}, employee_id={self.employee_id}, "
            f"pay_period='{self.pay_period}', net_salary={self.net_salary}, status='{self.payment_status}')>"
        )
