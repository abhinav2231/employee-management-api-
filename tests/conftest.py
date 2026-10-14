from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, engine
from app.models import Base


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def auto_reseed_after_tests():
    yield
    from scripts.seed import seed_database
    seed_database()


@pytest.fixture(scope="function", autouse=True)
def db() -> Generator[Session, None, None]:
    session = SessionLocal()
    tables = [
        "attendance",
        "salary_records",
        "employee_assignments",
        "employee_roles",
        "employees",
        "roles",
        "departments",
    ]
    try:
        for table in tables:
            session.execute(text(f"DELETE FROM {table}"))
        session.commit()
    except Exception:
        session.rollback()
        Base.metadata.create_all(bind=engine)
        session.commit()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
