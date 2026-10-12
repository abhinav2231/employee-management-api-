# LedgerForge — The Python Backbone of Aura WorkforceOS
## Task 1: Project Skeleton & Early Handoff Package

> *"A ledger is the book where a company records its money. To forge means to build something strong. **LedgerForge** is the strong engine that holds your people, pays them, and records every rupee in the books. It is the Python backbone of **WorkforceOS**."*

A production-ready, layered **FastAPI** application skeleton backed by **PostgreSQL** in **Docker Compose**, with environment configuration via `pydantic-settings`, automated testing via `pytest`, and an early team handoff package (API contract and sample dataset for all 6 cross-functional teams).

---

## 🚀 Quickstart (One Command Starts Everything)

Ensure Docker Desktop is installed and running, then execute:

```bash
docker compose up --build
```

That's it! Both the FastAPI application (`api`) and PostgreSQL database (`db`) will start up:
- **API Server:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

To stop the services:
```bash
docker compose down
```

---

## 🏗️ Project Architecture (Layered Design)

This project strictly adheres to a layered design pattern to separate concerns cleanly:

```text
employee_management_api/
├── app/
│   ├── api/                     # Route controllers & routers
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   └── health.py    # Health check route handler
│   │   │   └── api.py           # v1 router aggregator
│   ├── core/                    # Core configuration and database session
│   │   ├── config.py            # Pydantic Settings loaded from .env
│   │   └── database.py          # SQLAlchemy engine & session factory
│   ├── models/                  # Database models (Base ready for Task 2)
│   ├── schemas/                 # Pydantic request/response validation schemas
│   │   ├── health.py            # HealthResponse schema
│   │   └── employee.py          # Draft employee contract schemas
│   ├── services/                # Business logic layer
│   │   └── health_service.py    # Health status logic
│   └── main.py                  # FastAPI factory & app instance
├── data/
│   ├── sample_employees.json    # 10 fake employee records (JSON)
│   └── sample_employees.csv     # 10 fake employee records (CSV)
├── docs/
│   ├── api_contract.md          # Comprehensive early API contract
│   └── openapi_draft.json       # Draft OpenAPI 3.1 specification export
├── tests/
│   ├── conftest.py              # TestClient fixture
│   └── test_health.py           # Pytest test for /health
├── .env.example                 # Environment variables template (no secrets)
├── .env                         # Local dev environment configuration
├── .gitignore                   # Standard gitignore (secrets, venv, caches)
├── Dockerfile                   # Python 3.12-slim container image definition
├── docker-compose.yml           # Compose setup for 'api' and 'db' services
├── pyproject.toml               # Modern Python project configuration
├── requirements.txt             # Locked project dependencies
└── README.md                    # Setup and execution guide
```

---

## ⚙️ Environment Variables & Configuration

Settings are managed via `pydantic-settings` in `app/core/config.py`.

- Copy `.env.example` to `.env` if starting fresh:
  ```bash
  cp .env.example .env
  ```
- **Inside Docker Compose**, the database host name is the service name: `db`.
- **Outside Docker** (running locally on host), set `POSTGRES_SERVER=localhost` or point `DATABASE_URL` to your local database.

---

## 🧪 Local Development & Running Tests

### 1. Create and Activate Virtual Environment

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Pytest Suite

```bash
pytest
```

Expected output:
```text
tests/test_health.py::test_top_level_health_endpoint PASSED
tests/test_health.py::test_api_v1_health_endpoint PASSED
```

### 4. Run API Server Locally (Without Docker)

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📦 Early Handoff Package (Shared by Day 2)

As required for cross-team alignment:
1. **Draft API Contract:**
   - Table and endpoint specifications: [`docs/api_contract.md`](docs/api_contract.md)
   - Machine-readable OpenAPI 3.1 schema: [`docs/openapi_draft.json`](docs/openapi_draft.json)
2. **Sample Fake-Data (10 Employees):**
   - JSON format: [`data/sample_employees.json`](data/sample_employees.json)
   - CSV format: [`data/sample_employees.csv`](data/sample_employees.csv)

---

## 🔗 Connection to Next Task (Task 2)

The running app and database provide the foundational environment where **Task 2** will create the employee database tables and SQLAlchemy ORM models in `app/models/` and migrations.
