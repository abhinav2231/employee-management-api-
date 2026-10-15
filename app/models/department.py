from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.role import Role


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    department_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    department_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        passive_deletes=True,
    )

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        back_populates="department",
    )

    def __init__(self, **kwargs):
        if "code" in kwargs and "department_id" not in kwargs:
            kwargs["department_id"] = kwargs.pop("code")
        if "id" in kwargs and "department_id" not in kwargs:
            kwargs["department_id"] = str(kwargs.pop("id"))
        if "name" in kwargs and "department_name" not in kwargs:
            kwargs["department_name"] = kwargs.pop("name")
        super().__init__(**kwargs)

    @hybrid_property
    def id(self) -> str:
        return self.department_id

    @id.setter
    def id(self, value: str):
        self.department_id = value

    @hybrid_property
    def code(self) -> str:
        return self.department_id

    @code.setter
    def code(self, value: str):
        self.department_id = value

    @hybrid_property
    def name(self) -> str:
        return self.department_name

    @name.setter
    def name(self, value: str):
        self.department_name = value

    def __repr__(self) -> str:
        return f"<Department(id='{self.department_id}', name='{self.department_name}')>"

