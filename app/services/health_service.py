from app.schemas.health import HealthResponse


class HealthService:
    """
    Business logic layer for system health evaluation.
    """
    @staticmethod
    def get_health() -> HealthResponse:
        """
        Evaluate application status and return standard health response.
        """
        return HealthResponse(status="ok")


health_service = HealthService()
