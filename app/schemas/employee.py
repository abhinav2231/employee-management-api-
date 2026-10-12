from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class EmployeeBase(BaseModel):
    """
    Base schema shared across employee input and output models.
    """
    first_name: str = Field(..., min_length=1, max_length=50, examples=["Jane"])
    last_name: str = Field(..., min_length=1, max_length=50, examples=["Doe"])
    email: EmailStr = Field(..., examples=["jane.doe@example.com"])
    department: str = Field(..., min_length=1, max_length=50, examples=["Engineering"])
    role: str = Field(..., min_length=1, max_length=50, examples=["Software Engineer"])
    salary: float = Field(..., gt=0, examples=[95000.0])
    hire_date: date = Field(..., examples=["2023-01-15"])
    is_active: bool = Field(default=True, examples=[True])


class EmployeeCreate(EmployeeBase):
    """
    Schema for creating a new employee.
    """
    pass


class EmployeeUpdate(BaseModel):
    """
    Schema for updating employee fields partially.
    """
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, min_length=1, max_length=50)
    role: Optional[str] = Field(None, min_length=1, max_length=50)
    salary: Optional[float] = Field(None, gt=0)
    hire_date: Optional[date] = None
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    """
    Draft response schema for an employee including system-generated ID.
    """
    id: int = Field(..., examples=[1])

    model_config = {
        "from_attributes": True
    }
