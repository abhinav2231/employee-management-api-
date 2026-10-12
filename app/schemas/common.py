from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard pagination envelope returning total counts and page navigation metadata.
    """
    items: List[T]
    total: int = Field(..., ge=0, description="Total count of matching records across all pages")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    size: int = Field(..., ge=1, description="Number of items per page")
    pages: int = Field(..., ge=0, description="Total number of available pages")
