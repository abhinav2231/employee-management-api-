from fastapi import APIRouter
from app.api.v1.endpoints import health, employees, departments

api_router = APIRouter()

# Mount endpoints
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
