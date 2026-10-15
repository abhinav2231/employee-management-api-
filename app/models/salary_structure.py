from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class SalaryStructure(Base, TimestampMixin):
    __tablename__ = "salary_structures"

    structure_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    component_name: Mapped[str] = mapped_column(String(100), nullable=False)
    component_type: Mapped[str] = mapped_column(String(50), nullable=False)
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    revision_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="salary_structures")

    @property
    def id(self) -> str:
        return self.structure_id

    def __repr__(self) -> str:
        return f"<SalaryStructure(id='{self.structure_id}', emp='{self.employee_id}', comp='{self.component_id}', amount={self.monthly_amount})>"
