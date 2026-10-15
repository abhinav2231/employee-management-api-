from typing import Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class DepartmentBrief(BaseModel):
    id: Union[str, int]
    department_id: Optional[str] = None
    name: str
    code: str
    cost_center: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    cost_center: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    is_active: bool = Field(default=True)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    cost_center: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: Union[str, int]
    department_id: Optional[str] = None
    employee_count: int = Field(default=0)

    model_config = ConfigDict(from_attributes=True)
