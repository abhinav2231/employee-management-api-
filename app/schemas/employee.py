import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any, Union, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict

from app.core.config import settings
from app.schemas.department import DepartmentBrief
from app.schemas.role import RoleBrief

EmploymentStatus = Literal["Active", "Resigned", "Terminated", "Contract Ended", "Deactivated"]
ExitType = Literal["Voluntary", "Involuntary", "Contract End"]


class EmployeeBrief(BaseModel):
    id: Union[str, int]
    employee_id: Optional[str] = None
    employee_code: Optional[str] = None
    first_name: str
    last_name: str
    full_name: Optional[str] = None
    email: EmailStr
    work_email: Optional[str] = None
    department_id: Union[str, int]
    role_id: Optional[Union[str, int]] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(BaseModel):
    employee_id: Optional[str] = None
    employee_code: Optional[str] = Field(None, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    full_name: Optional[str] = None
    email: EmailStr
    work_email: Optional[str] = None
    phone_number: Optional[str] = Field(
        None,
        pattern=r"^\+91[6-9]\d{9}$",
        description="Indian mobile phone number in +91[6-9]XXXXXXXXX format",
    )
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    department_id: Union[str, int] = Field(..., description="Department ID or Code")
    role_id: Optional[Union[str, int]] = Field(None, description="Role ID or Code")
    primary_role_id: Optional[Union[str, int]] = Field(None, description="Alias for role_id")
    manager_id: Optional[Union[str, int]] = Field(None, description="Manager ID or Code")
    salary: Optional[Decimal] = Field(None, gt=0)
    hire_date: date
    exit_date: Optional[date] = None
    work_location: Optional[str] = Field(None, max_length=50)
    work_mode: Optional[str] = Field(None, max_length=50)
    highest_education: Optional[str] = None
    prior_experience_years: Optional[Decimal] = None
    career_gap_months: Optional[int] = 0
    commute_distance_km: Optional[Decimal] = None
    pf_applicable: Optional[str] = "Y"
    esi_applicable: Optional[str] = "N"
    notice_period_days: Optional[int] = 30
    resignation_date: Optional[date] = None
    employment_type: Optional[str] = Field("Permanent", max_length=50)
    employment_status: Optional[EmploymentStatus] = "Active"
    exit_type: Optional[ExitType] = None
    exit_reason: Optional[str] = Field(None, max_length=255)

    @field_validator("email", mode="after")
    @classmethod
    def lowercase_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("employee_code", "employee_id")
    @classmethod
    def validate_employee_code_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip().upper()
            if not re.match(r"^EMP-\d{4}$", trimmed):
                raise ValueError("Employee code must follow the standard 'EMP-XXXX' format with 4 digits (e.g. EMP-0001)")
            return trimmed
        return v

    @model_validator(mode="before")
    @classmethod
    def handle_role_and_code_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "primary_role_id" in data and ("role_id" not in data or data["role_id"] is None):
                data["role_id"] = data["primary_role_id"]
            if "employee_code" in data and ("employee_id" not in data or data["employee_id"] is None):
                data["employee_id"] = data["employee_code"]
            elif "employee_id" in data and ("employee_code" not in data or data["employee_code"] is None):
                data["employee_code"] = data["employee_id"]
            if "work_email" in data and ("email" not in data or data["email"] is None):
                data["email"] = data["work_email"]
            elif "email" in data and ("work_email" not in data or data["work_email"] is None):
                data["work_email"] = str(data["email"])
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
        cut_off = max(date.today(), settings.DEMO_TODAY)
        if v > cut_off:
            raise ValueError(f"Joining date cannot be in the future (after {cut_off})")
        return v


class EmployeeCreate(EmployeeBase):
    is_active: bool = Field(default=True)

    @model_validator(mode="after")
    def check_exit_fields(self):
        if self.employment_status is not None and (self.employment_status == "Active") != self.is_active:
            raise ValueError("employment_status and is_active contradict each other")
        if self.is_active and any(v is not None for v in (self.exit_type, self.exit_reason, self.exit_date)):
            raise ValueError("exit fields cannot be set on an active employee")
        if self.exit_date is not None and self.hire_date is not None and self.exit_date < self.hire_date:
            raise ValueError("exit_date cannot be before hire_date")
        return self


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    work_email: Optional[str] = None

    @field_validator("email", mode="after")
    @classmethod
    def lowercase_email(cls, v: Optional[EmailStr]) -> Optional[str]:
        if v is not None:
            return str(v).strip().lower()
        return v

    phone_number: Optional[str] = Field(
        None,
        pattern=r"^\+91[6-9]\d{9}$",
        description="Indian mobile phone number in +91[6-9]XXXXXXXXX format",
    )
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    department_id: Optional[Union[str, int]] = None
    role_id: Optional[Union[str, int]] = None
    primary_role_id: Optional[Union[str, int]] = None
    manager_id: Optional[Union[str, int]] = None
    salary: Optional[Decimal] = Field(None, gt=0)
    hire_date: Optional[date] = None
    exit_date: Optional[date] = None
    work_location: Optional[str] = Field(None, max_length=50)
    work_mode: Optional[str] = Field(None, max_length=50)
    highest_education: Optional[str] = None
    prior_experience_years: Optional[Decimal] = None
    career_gap_months: Optional[int] = None
    commute_distance_km: Optional[Decimal] = None
    pf_applicable: Optional[str] = None
    esi_applicable: Optional[str] = None
    notice_period_days: Optional[int] = None
    resignation_date: Optional[date] = None
    employment_type: Optional[str] = Field(None, max_length=50)
    employment_status: Optional[EmploymentStatus] = None
    exit_type: Optional[ExitType] = None
    exit_reason: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def handle_role_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "primary_role_id" in data and ("role_id" not in data or data["role_id"] is None):
                data["role_id"] = data["primary_role_id"]
            if "work_email" in data and ("email" not in data or data["email"] is None):
                data["email"] = data["work_email"]
            elif "email" in data and ("work_email" not in data or data["work_email"] is None):
                data["work_email"] = str(data["email"])
        return data

    @model_validator(mode="after")
    def check_status_consistency(self):
        if self.employment_status is not None and self.is_active is not None:
            if (self.employment_status == "Active") != self.is_active:
                raise ValueError("employment_status and is_active contradict each other")
        going_active = self.employment_status == "Active" or self.is_active is True
        has_exit = any(v is not None for v in (self.exit_type, self.exit_reason, self.exit_date))
        if going_active and has_exit:
            raise ValueError("exit_type, exit_reason and exit_date cannot be set on an active employee")
        return self

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
        if v is not None and v > settings.DEMO_TODAY:
            raise ValueError(f"Joining date cannot be after {settings.DEMO_TODAY}")
        return v


class EmployeeResponse(BaseModel):
    id: Union[str, int]
    employee_id: Optional[str] = None
    employee_code: Optional[str] = None
    first_name: str
    last_name: str
    full_name: Optional[str] = None
    email: EmailStr
    work_email: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    department_id: Union[str, int]
    department: Optional[DepartmentBrief] = None
    role_id: Optional[Union[str, int]] = None
    role: Optional[RoleBrief] = None
    manager_id: Optional[Union[str, int]] = None
    manager: Optional[EmployeeBrief] = None
    salary: Optional[Decimal] = None
    hire_date: date
    exit_date: Optional[date] = None
    employment_status: Optional[str] = None
    exit_type: Optional[str] = None
    exit_reason: Optional[str] = None
    work_location: Optional[str] = None
    work_mode: Optional[str] = None
    highest_education: Optional[str] = None
    prior_experience_years: Optional[Decimal] = None
    career_gap_months: Optional[int] = None
    commute_distance_km: Optional[Decimal] = None
    pf_applicable: Optional[str] = None
    esi_applicable: Optional[str] = None
    notice_period_days: Optional[int] = None
    resignation_date: Optional[date] = None
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
