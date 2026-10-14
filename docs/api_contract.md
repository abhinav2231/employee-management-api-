# Aura Workforce OS API — Core API Contract

**System:** Aura Workforce OS  
**Target:** Core Payroll, Accounting & Workforce Operating System  
**Base URL:** `http://localhost:8000/api/v1` (Docker Compose / Local Dev)  
*(Enterprise Master Dataset: Aura Workforce OS)*  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI) | `http://localhost:8000/redoc` (ReDoc)

---

## 1. Implemented Endpoints Summary Table

| HTTP Method | Path | Request Body | Success Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/health` | None | `200 OK` | Top-level system liveness & health check |
| **GET** | `/api/v1/health` | None | `200 OK` | Versioned API health check |
| **POST** | `/api/v1/employees` | `EmployeeCreate` (JSON) | `201 Created` | Create new employee with department & role |
| **GET** | `/api/v1/employees` | Query params (`page`, `size`, `department`, `employee_code`, `q`, `include_inactive`) | `200 OK` | List employees with pagination, filter & search |
| **GET** | `/api/v1/employees/{id}` | None | `200 OK` | Retrieve single employee by ID or Code |
| **PATCH**| `/api/v1/employees/{id}` | `EmployeeUpdate` (JSON) | `200 OK` | Partial update of employee details (supports cycle prevention & manager clear) |
| **DELETE**| `/api/v1/employees/{id}` | None | `204 No Content` | Soft delete employee (`is_active = false`), reassigns direct reports |
| **GET** | `/api/v1/employees/{id}/team` | None | `200 OK` | Direct reports reporting to manager |
| **GET** | `/api/v1/departments` | None | `200 OK` | List all 11 departments and active headcounts |
| **GET** | `/api/v1/departments/{id}` | None | `200 OK` | Retrieve single department by ID |
| **GET** | `/api/v1/departments/{id}/employees` | Query params (`page`, `size`) | `200 OK` | Paginated employee roster for a department |

---

## 2. Data Models & Schemas

### 2.1 Employee Data Dictionary

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `integer` | Read-only, auto-increment primary key | Database internal identifier |
| `employee_code` | `string` | Optional on create (auto-generated `EMP-xxxx`) | Business employee code |
| `first_name` | `string` | Min: 1, Max: 50 | Employee legal first name |
| `last_name` | `string` | Min: 1, Max: 50 | Employee legal last name |
| `email` | `string (email)` | Unique, valid RFC 5322 email | Corporate email address |
| `phone_number` | `string` | Indian phone format (`en_IN`) | Corporate contact phone number |
| `department_id` | `integer or string` | Required (ID or Code e.g. `D01`) | Department foreign reference |
| `role_id` | `integer or string` | Optional (ID or Code e.g. `R001`) | Primary role designation |
| `manager_id` | `integer or string` | Optional (ID or Code e.g. `EMP-0006`) | Reporting manager reference |
| `salary` | `number` | Required, `> 0` | Annual gross compensation (INR) |
| `hire_date` | `string (date)` | Required, `YYYY-MM-DD`, non-future | Date of joining |
| `exit_date` | `string (date)` | Optional, `YYYY-MM-DD` | Date of departure |
| `work_location` | `string` | Optional, Max: 50 | Office city / base location |
| `employment_type` | `string` | Optional, Max: 50 | Permanent, Contract, etc. |
| `is_active` | `boolean` | Default: `true` | Active employment status flag |

---

## 3. Standard Error Envelope

All API errors return a uniform JSON format:

```json
{
  "detail": "Description of the error",
  "error_code": "NOT_FOUND | CONFLICT | BAD_REQUEST | VALIDATION_ERROR | INTERNAL_SERVER_ERROR",
  "field": "optional_field_name"
}
```
