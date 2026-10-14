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

def ensure_test_database_exists():
    admin_db = "postgres"
    admin_uri = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{host}:{settings.POSTGRES_PORT}/{admin_db}"
    admin_engine = create_engine(admin_uri, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            check_sql = text("SELECT 1 FROM pg_database WHERE datname = 'aura_workforce_test_db'")
            res = conn.execute(check_sql).scalar()
            if not res:
                conn.execute(text("CREATE DATABASE aura_workforce_test_db"))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Could not verify/create test database via admin connection: %s", exc)
    finally:
        admin_engine.dispose()


ensure_test_database_exists()

test_engine = create_engine(TEST_DB_URI, pool_pre_ping=True)
db_name = test_engine.url.database or ""
assert "test" in db_name.lower(), (
    f"CRITICAL TEST DATABASE SAFETY GUARD: Refusing to drop/create tables on '{db_name}'. "
    f"The test database name must contain 'test' to prevent wiping development or production databases."
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


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
        "salary_revisions",
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
