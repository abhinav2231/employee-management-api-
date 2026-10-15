from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    service: Optional[str] = None
    version: Optional[str] = None
    checks: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "service": "aura-workforce-api",
                "version": "1.0.0",
                "checks": {"database": "ok"},
            }
        }
    }
