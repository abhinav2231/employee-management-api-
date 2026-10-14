from app.schemas.health import HealthResponse


class HealthService:
    @staticmethod
    def get_health() -> HealthResponse:
        return HealthResponse(status="ok")


health_service = HealthService()
