from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.api.v1.api import api_router
from app.schemas.health import HealthResponse
from app.services.health_service import health_service


def create_application() -> FastAPI:
    """
    Application factory initializing FastAPI with configurations and routers.
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Layered FastAPI Employee Management API. "
            "Features automatic OpenAPI docs, modular service-oriented architecture, "
            "and Dockerized PostgreSQL integration."
        ),
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root redirect to documentation
    @application.get(
        "/",
        include_in_schema=False,
        summary="Root Documentation Redirect",
    )
    def root_redirect():
        return RedirectResponse(url="/docs")

    # Top-level /health endpoint matching specification requirement
    @application.get(
        "/health",
        response_model=HealthResponse,
        status_code=status.HTTP_200_OK,
        summary="Service Health Check",
        description="Top-level health verification endpoint.",
        tags=["Health"],
    )
    def top_level_health() -> HealthResponse:
        return health_service.get_health()

    # Mount versioned API routes (e.g. /api/v1/health, /api/v1/employees)
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app = create_application()
