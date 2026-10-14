from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DepartmentBrief(BaseModel):
    id: int
    name: str
    code: str
    cost_center: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=10)
    cost_center: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=255)
    is_active: bool = Field(default=True)


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
    employee_count: int = Field(default=0)

    model_config = ConfigDict(from_attributes=True)
