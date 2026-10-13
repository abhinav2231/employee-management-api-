import os
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
    """
    Test client fixture providing a synchronous HTTP client for tests.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function", autouse=True)
def db() -> Generator[Session, None, None]:
    """
    Yields a database session per test and cleans up data between test runs.
    """
    session = SessionLocal()
    try:
        # Clean existing test data before each test
        session.execute(text("DELETE FROM attendance; DELETE FROM salary_records; DELETE FROM employee_assignments; DELETE FROM employee_roles; DELETE FROM employees; DELETE FROM roles; DELETE FROM departments;"))
        session.commit()
    except Exception:
        session.rollback()
        # In case tables weren't created yet, create them via metadata
        Base.metadata.create_all(bind=engine)
        session.commit()

    try:
        yield session
    finally:
        session.rollback()
        try:
            session.execute(text("DELETE FROM attendance; DELETE FROM salary_records; DELETE FROM employee_assignments; DELETE FROM employee_roles; DELETE FROM employees; DELETE FROM roles; DELETE FROM departments;"))
            session.commit()
        except Exception:
            session.rollback()
        session.close()
