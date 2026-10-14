from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, code='{self.code}', name='{self.name}')>"
