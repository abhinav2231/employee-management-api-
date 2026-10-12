from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RoleBrief(BaseModel):
    """Minimal role projection."""
    id: int
    code: Optional[str] = None
    title: str
    level: Optional[str] = None
    is_primary: bool = Field(default=False)

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    code: Optional[str] = Field(None, max_length=10, examples=["R001"])
    title: str = Field(..., min_length=1, max_length=100, examples=["Software Engineer"])
    description: Optional[str] = Field(None, max_length=255)
    level: Optional[str] = Field(None, max_length=50, examples=["L2 Executive"])
    is_active: bool = Field(default=True)


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
