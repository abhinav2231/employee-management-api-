from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from app.schemas.department import DepartmentBrief
from app.schemas.role import RoleBrief


class EmployeeBrief(BaseModel):
    """Minimal employee projection for manager or team listings."""
    id: int
    employee_code: Optional[str] = None
    first_name: str
    last_name: str
    email: EmailStr
    department_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(BaseModel):
    """Base fields for employee validation."""
    employee_code: Optional[str] = Field(None, max_length=20, examples=["EMP-0001"])
    first_name: str = Field(..., min_length=1, max_length=50, examples=["Jane"])
    last_name: str = Field(..., min_length=1, max_length=50, examples=["Doe"])
    email: EmailStr = Field(..., examples=["jane.doe@example.com"])
    department_id: int = Field(..., gt=0, examples=[1])
    role_id: Optional[int] = Field(None, gt=0, description="Optional primary job role ID", examples=[1])
    manager_id: Optional[int] = Field(None, gt=0, description="Optional manager ID", examples=[2])
    salary: Decimal = Field(..., gt=0, examples=[950000.00])
    hire_date: date = Field(..., examples=["2023-01-15"])
    work_location: Optional[str] = Field(None, max_length=50, examples=["Pune"])
    employment_type: Optional[str] = Field(None, max_length=50, examples=["Permanent"])

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
    """Schema for creating a new employee."""
    is_active: bool = Field(default=True, examples=[True])


class EmployeeUpdate(BaseModel):
    """Schema for patching / updating employee fields partially."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    department_id: Optional[int] = Field(None, gt=0)
    role_id: Optional[int] = Field(None, gt=0)
    manager_id: Optional[int] = None
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
    """Full employee response schema with relationships."""
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
    """Manager profile and direct reports list."""
    manager: EmployeeBrief
    direct_reports: List[EmployeeBrief]
    total_reports: int = Field(..., ge=0)
