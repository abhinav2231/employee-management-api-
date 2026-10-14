from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any, Union
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict

from app.schemas.department import DepartmentBrief
from app.schemas.role import RoleBrief


class EmployeeBrief(BaseModel):
    id: int
    employee_code: Optional[str] = None
    first_name: str
    last_name: str
    email: EmailStr
    department_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(BaseModel):
    employee_code: Optional[str] = Field(None, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    department_id: Union[int, str] = Field(..., description="Department database ID or Code")
    role_id: Optional[Union[int, str]] = Field(None, description="Role database ID or Code")
    primary_role_id: Optional[Union[int, str]] = Field(None, description="Alias for role_id")
    manager_id: Optional[Union[int, str]] = Field(None, description="Manager database ID or Code")
    salary: Decimal = Field(..., gt=0)
    hire_date: date
    work_location: Optional[str] = Field(None, max_length=50)
    employment_type: Optional[str] = Field(None, max_length=50)

    @model_validator(mode="before")
    @classmethod
    def handle_role_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "primary_role_id" in data and ("role_id" not in data or data["role_id"] is None):
                data["role_id"] = data["primary_role_id"]
        return data

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Name cannot be empty or whitespace")
        return trimmed

    @field_validator("hire_date")
    @classmethod
    def validate_hire_date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Joining date cannot be in the future")
        return v


class EmployeeCreate(EmployeeBase):
    is_active: bool = Field(default=True)


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    department_id: Optional[Union[int, str]] = None
    role_id: Optional[Union[int, str]] = None
    manager_id: Optional[Union[int, str]] = None
    salary: Optional[Decimal] = Field(None, gt=0)
    hire_date: Optional[date] = None
    work_location: Optional[str] = Field(None, max_length=50)
    employment_type: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Name cannot be empty or whitespace")
            return trimmed
        return v

    @field_validator("hire_date")
    @classmethod
    def validate_hire_date_not_future(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Joining date cannot be in the future")
        return v


class EmployeeResponse(BaseModel):
    id: int
    employee_code: Optional[str] = None
    first_name: str
    last_name: str
    email: EmailStr
    department_id: int
    department: Optional[DepartmentBrief] = None
    manager_id: Optional[int] = None
    manager: Optional[EmployeeBrief] = None
    salary: Decimal
    hire_date: date
    exit_date: Optional[date] = None
    work_location: Optional[str] = None
    employment_type: Optional[str] = None
    is_active: bool
    roles: List[RoleBrief] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamResponse(BaseModel):
    manager: EmployeeBrief
    direct_reports: List[EmployeeBrief]
    total_reports: int = Field(..., ge=0)
