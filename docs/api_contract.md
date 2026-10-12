# LedgerForge API — Early API Contract (Draft v1) — Aura WorkforceOS

*LedgerForge is the Python backbone of Aura WorkforceOS: holding people, compensation, and recording every rupee in the books.*

**Handoff Target:** All 6 Cross-Functional Teams (Frontend, Integrations, Analytics, Payroll, Audit, Core)  
**Target Release:** Day 2 Early Alignment  
**Base URL:** `http://localhost:8000/api/v1` (Docker Compose / Local Dev)  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI) | `http://localhost:8000/redoc` (ReDoc)

---

## 1. Planned Endpoints Summary Table

| HTTP Method | Path | Request Body | Success Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/health` | None | `200 OK` | Top-level system liveness & health check |
| **GET** | `/api/v1/health` | None | `200 OK` | Versioned API health check |
| **GET** | `/api/v1/employees` | Query params (`skip`, `limit`, `department`, `is_active`) | `200 OK` | List employees with pagination and filters |
| **POST** | `/api/v1/employees` | `EmployeeCreate` | `201 Created` | Create a new employee record |
| **GET** | `/api/v1/employees/{id}` | None | `200 OK` | Retrieve single employee by ID |
| **PUT** | `/api/v1/employees/{id}` | `EmployeeUpdate` (full/partial) | `200 OK` | Update existing employee details |
| **DELETE** | `/api/v1/employees/{id}` | None | `204 No Content` | Delete employee record |
| **GET** | `/api/v1/departments` | None | `200 OK` | List distinct departments and headcounts |

---

## 2. Data Models & Schemas

### 2.1 Employee Data Dictionary

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `integer` | Read-only, auto-increment primary key | Unique employee identifier |
| `first_name` | `string` | Min: 1, Max: 50 | Employee legal first name |
| `last_name` | `string` | Min: 1, Max: 50 | Employee legal last name |
| `email` | `string (email)` | Unique, valid RFC 5322 email | Corporate email address |
| `department` | `string` | Min: 1, Max: 50 | Department name (e.g. `Engineering`, `Product`) |
| `role` | `string` | Min: 1, Max: 50 | Job title (e.g. `Software Engineer`) |
| `salary` | `number (float)`| > 0 | Annual gross compensation |
| `hire_date` | `string (date)` | Format: `YYYY-MM-DD` | Date of joining |
| `is_active` | `boolean` | Default: `true` | Employment status flag |

---

## 3. Detailed Request / Response Payloads

### 3.1 GET `/health` & GET `/api/v1/health`
**Response (200 OK):**
```json
{
  "status": "ok"
}
```

### 3.2 GET `/api/v1/employees`
**Query Parameters:**
- `skip`: `int` (default: `0`, min: `0`)
- `limit`: `int` (default: `20`, min: `1`, max: `100`)
- `department`: `string` (optional filter)
- `is_active`: `bool` (optional filter)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice.smith@example.com",
    "department": "Engineering",
    "role": "Lead Backend Engineer",
    "salary": 125000.0,
    "hire_date": "2021-03-15",
    "is_active": true
  }
]
```

### 3.3 POST `/api/v1/employees`
**Request Body (`application/json`):**
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane.doe@example.com",
  "department": "Engineering",
  "role": "Software Engineer",
  "salary": 95000.0,
  "hire_date": "2023-01-15",
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": 11,
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane.doe@example.com",
  "department": "Engineering",
  "role": "Software Engineer",
  "salary": 95000.0,
  "hire_date": "2023-01-15",
  "is_active": true
}
```

### 3.4 GET `/api/v1/employees/{id}`
**Response (200 OK):**
```json
{
  "id": 1,
  "first_name": "Alice",
  "last_name": "Smith",
  "email": "alice.smith@example.com",
  "department": "Engineering",
  "role": "Lead Backend Engineer",
  "salary": 125000.0,
  "hire_date": "2021-03-15",
  "is_active": true
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Employee with ID 999 not found"
}
```

---

## 4. Standard Error Structure (FastAPI / RFC 7807 compatible)

```json
{
  "detail": "Descriptive error message"
}
```

For validation errors (`422 Unprocessable Entity`):
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error"
    }
  ]
}
```
