import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.models import Base

is_container = os.path.exists("/.dockerenv")
host = settings.POSTGRES_SERVER if is_container or settings.POSTGRES_SERVER != "db" else "localhost"
TEST_DB_URI = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{host}:{settings.POSTGRES_PORT}/aura_workforce_test_db",
)

test_engine = create_engine(TEST_DB_URI, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function", autouse=True)
def db() -> Generator[Session, None, None]:
    session = TestSessionLocal()
    tables = [
        "attendance",
        "salary_records",
        "employee_assignments",
        "employee_roles",
        "employees",
        "roles",
        "departments",
    ]
    for table in tables:
        session.execute(text(f"DELETE FROM {table}"))
    session.commit()

    app.dependency_overrides[get_db] = lambda: session

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        app.dependency_overrides.pop(get_db, None)
