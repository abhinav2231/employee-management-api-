from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok"
            }
        }
    }
