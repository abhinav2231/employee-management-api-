from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.api.v1.api import api_router
from app.api.v1.endpoints import employees, departments
from app.schemas.health import HealthResponse
from app.services.health_service import health_service


def create_application() -> FastAPI:
    """
    Application factory initializing FastAPI with configurations, error handlers, and routers.
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Aura Workforce OS: Core Payroll, Accounting & Employee Data Engine. "
            "Features automated OpenAPI docs, service-oriented architecture, and Dockerized PostgreSQL integration."
        ),
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Register centralized exception handlers for uniform error format
    register_exception_handlers(application)

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

    # Mount versioned API routes (/api/v1/...)
    application.include_router(api_router, prefix=settings.API_V1_STR)

    # Top-level route aliases for convenience (/employees, /departments)
    application.include_router(
        employees.router,
        prefix="/employees",
        include_in_schema=False,
    )
    application.include_router(
        departments.router,
        prefix="/departments",
        include_in_schema=False,
    )

    return application


app = create_application()
