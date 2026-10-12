from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DepartmentBrief(BaseModel):
    """Minimal department projection."""
    id: int
    name: str
    code: str
    cost_center: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentBase(BaseModel):
    """Base fields for Department."""
    name: str = Field(..., min_length=1, max_length=50, examples=["Engineering"])
    code: str = Field(..., min_length=1, max_length=10, examples=["D01"])
    cost_center: Optional[str] = Field(None, max_length=20, examples=["CC-100"])
    description: Optional[str] = Field(None, max_length=255, examples=["Product engineering, QA and DevOps"])
    is_active: bool = Field(default=True, examples=[True])


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    cost_center: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: int
    employee_count: int = Field(default=0, description="Active headcount in this department")

    model_config = ConfigDict(from_attributes=True)
