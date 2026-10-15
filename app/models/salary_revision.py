from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class SalaryRevision(Base, TimestampMixin):
    __tablename__ = "salary_revisions"

    revision_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    revision_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    previous_annual_fixed: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    new_annual_fixed: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    pct_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    role_id_after: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="salary_revisions")

    @hybrid_property
    def id(self) -> str:
        return self.revision_id

    @id.setter
    def id(self, val: str):
        self.revision_id = val

    @hybrid_property
    def revision_code(self) -> str:
        return self.revision_id

    @revision_code.setter
    def revision_code(self, val: str):
        self.revision_id = val

    def __repr__(self) -> str:
        return f"<SalaryRevision(id='{self.revision_id}', emp='{self.employee_id}', new_fixed={self.new_annual_fixed})>"

