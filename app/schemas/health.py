from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Schema for health check endpoint responses.
    """
    status: str = Field(default="ok", description="Application health status indicator")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok"
            }
        }
    }
