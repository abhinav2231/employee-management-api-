from typing import Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class RoleBrief(BaseModel):
    id: Union[str, int]
    role_id: Optional[str] = None
    code: Optional[str] = None
    title: str
    level: Optional[Union[str, int]] = None
    is_primary: bool = Field(default=True)

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    role_id: Optional[str] = None
    code: Optional[str] = Field(None, max_length=20)
    title: str = Field(..., min_length=1, max_length=100)
    department_id: Optional[str] = None
    description: Optional[str] = Field(None, max_length=255)
    level: Optional[Union[str, int]] = None
    grade: Optional[str] = None
    band_min_annual: Optional[int] = None
    band_mid_annual: Optional[int] = None
    band_max_annual: Optional[int] = None
    overtime_eligible: Optional[str] = "N"
    band_year: Optional[int] = 2026
    is_active: bool = Field(default=True)


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: Union[str, int]

    model_config = ConfigDict(from_attributes=True)
