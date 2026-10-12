from fastapi import APIRouter
from app.api.v1.endpoints import health

api_router = APIRouter()

# Include endpoints
api_router.include_router(health.router, prefix="", tags=["Health"])
# Planned Task 2+ routers will be attached here:
# api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
