from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class SalaryRevision(Base, TimestampMixin):
    __tablename__ = "salary_revisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    revision_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    revision_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    previous_annual_fixed: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    new_annual_fixed: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    pct_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    role_id_after: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="salary_revisions")

    def __repr__(self) -> str:
        return f"<SalaryRevision(code='{self.revision_code}', employee_id={self.employee_id}, new_fixed={self.new_annual_fixed})>"
