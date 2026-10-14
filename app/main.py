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
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Aura Workforce OS: Core Payroll, Accounting & Employee Data Engine.",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(application)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/", include_in_schema=False)
    def root_redirect():
        return RedirectResponse(url="/docs")

    @application.get(
        "/health",
        response_model=HealthResponse,
        status_code=status.HTTP_200_OK,
        tags=["Health"],
    )
    def top_level_health() -> HealthResponse:
        return health_service.get_health()

    application.include_router(api_router, prefix=settings.API_V1_STR)

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
