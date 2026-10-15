from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.department import Department


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    department_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("departments.department_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role_title: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    band_min_annual: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    band_mid_annual: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    band_max_annual: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    overtime_eligible: Mapped[str] = mapped_column(String(5), default="N", nullable=False)
    band_year: Mapped[int] = mapped_column(Integer, default=2026, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="roles")
    employees: Mapped[list["Employee"]] = relationship("Employee", back_populates="role")

    def __init__(self, **kwargs):
        if "code" in kwargs and "role_id" not in kwargs:
            kwargs["role_id"] = kwargs.pop("code")
        if "id" in kwargs and "role_id" not in kwargs:
            kwargs["role_id"] = str(kwargs.pop("id"))
        if "title" in kwargs and "role_title" not in kwargs:
            kwargs["role_title"] = kwargs.pop("title")
        if "level" in kwargs and kwargs["level"] is not None:
            kwargs["level"] = str(kwargs["level"])
        if "department_id" in kwargs and kwargs["department_id"] is not None:
            kwargs["department_id"] = str(kwargs["department_id"])
        if "role_id" not in kwargs:
            import uuid
            kwargs["role_id"] = f"R{uuid.uuid4().hex[:4].upper()}"
        super().__init__(**kwargs)

    @hybrid_property
    def id(self) -> str:
        return self.role_id

    @id.setter
    def id(self, value: str):
        self.role_id = value

    @hybrid_property
    def code(self) -> str:
        return self.role_id

    @code.setter
    def code(self, value: str):
        self.role_id = value

    @hybrid_property
    def title(self) -> str:
        return self.role_title

    @title.setter
    def title(self, value: str):
        self.role_title = value

    def __repr__(self) -> str:
        return f"<Role(id='{self.role_id}', title='{self.role_title}', level={self.level})>"


class EmployeeRole(Base):
    __tablename__ = "employee_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "role_id", name="uq_employee_role"),
    )

    role: Mapped["Role"] = relationship("Role")
    employee: Mapped["Employee"] = relationship("Employee", back_populates="employee_roles")

    def __init__(self, **kwargs):
        if "employee_id" in kwargs:
            kwargs["employee_id"] = str(kwargs["employee_id"])
        if "role_id" in kwargs:
            kwargs["role_id"] = str(kwargs["role_id"])
        super().__init__(**kwargs)
