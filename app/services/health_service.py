import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import AppException
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)


class HealthService:
    @staticmethod
    def get_health(detailed: bool = False, db: Optional[Session] = None) -> HealthResponse:
        if not detailed:
            return HealthResponse(status="ok")
        db_status = "ok"
        if db:
            try:
                db.execute(text("SELECT 1"))
            except Exception as exc:
                logger.error("Database health check probe failed: %s", exc)
                db_status = "error"
        return HealthResponse(
            status="ok" if db_status == "ok" else "degraded",
            service="aura-workforce-api",
            version=settings.VERSION,
            checks={"database": db_status},
        )

    @staticmethod
    def check_readiness(db: Session) -> dict:
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ok", "database": "connected"}
        except Exception as exc:
            logger.error("Database readiness probe failed: %s", exc)
            raise AppException(
                detail="Database service is unavailable",
                status_code=503,
                error_code="SERVICE_UNAVAILABLE",
            )


health_service = HealthService()
