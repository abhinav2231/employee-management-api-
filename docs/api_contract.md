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
| **DELETE**| `/api/v1/employees/{id}` | None | `204 No Content` | Soft delete employee (`is_active = false`), sets exit fields and reassigns direct reports |
| **GET** | `/api/v1/employees/{id}/team` | None | `200 OK` | Direct reports reporting to manager |
| **GET** | `/api/v1/departments` | None | `200 OK` | List all 11 departments and active headcounts |
| **GET** | `/api/v1/departments/{id}` | None | `200 OK` | Retrieve single department by ID |
| **GET** | `/api/v1/departments/{id}/employees` | Query params (`page`, `size`) | `200 OK` | Paginated employee roster for a department |

---

## 2. Data Models & Schemas

### 2.1 Employee Data Dictionary

| Field | Type | Exposure | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `integer` | Read-only | Auto-increment primary key | Database internal identifier |
| `employee_code` | `string` | Read-only / Auto | Unique code e.g. `EMP-0001` | Unique business employee code |
| `first_name` | `string` | Create / Update / Read | Min: 1, Max: 50 | Employee legal first name |
| `last_name` | `string` | Create / Update / Read | Min: 1, Max: 50 | Employee legal last name |
| `email` | `string (email)` | Create / Update / Read | Unique, valid RFC 5322 email | Corporate work email address |
| `phone_number` | `string` | Create / Update / Read | Indian mobile (`+91[6-9]XXXXXXXXX`) | Corporate contact phone number |
| `department_id` | `integer or string` | Create / Update / Read | Required (ID or Code e.g. `D01`) | Department foreign reference |
| `role_id` | `integer or string` | Create / Update | Optional (ID or Code e.g. `R001`) | Primary role designation |
| `manager_id` | `integer or string` | Create / Update / Read | Optional (ID or Code e.g. `EMP-0006`) | Reporting manager reference |
| `salary` | `number` | Create / Update / Read | Required, `> 0` | Annual gross compensation (INR) |
| `hire_date` | `string (date)` | Create / Update / Read | Required, `YYYY-MM-DD`, non-future | Date of joining |
| `exit_date` | `string (date)` | Create / Update / Read | Optional, `YYYY-MM-DD` | Date of departure / exit |
| `employment_status`| `string` | Create / Update / Read | `Active`, `Resigned`, `Terminated` | Status of employment |
| `exit_type` | `string` | Create / Update / Read | `Voluntary`, `Involuntary`, etc. | Categorization of exit |
| `exit_reason` | `string` | Create / Update / Read | Max: 255 | Departure reason narrative |
| `work_location` | `string` | Create / Update / Read | Max: 50 | Office city / base location |
| `work_mode` | `string` | Create / Update / Read | `Onsite`, `Remote`, `Hybrid` | Operating work model |
| `employment_type` | `string` | Create / Update / Read | Max: 50 | Permanent, Contract, etc. |
| `is_active` | `boolean` | Create / Update / Read | Default: `true` | Active employment status flag |
| `date_of_birth` | `string (date)` | Internal Only | Valid date | Date of birth (PII withheld until Task 5) |
| `pf_applicable` | `boolean` | Internal Only | Boolean | Provident Fund applicability (withheld until Task 5) |
| `esi_applicable`| `boolean` | Internal Only | Boolean | ESI applicability (withheld until Task 5) |

### 2.2 Privacy & Sensitive Field Access Policy
- **PII & Statutory Fields Withheld:** In compliance with enterprise data privacy standards, `date_of_birth`, `pf_applicable`, and `esi_applicable` are persisted in the database schema for payroll/compliance processing, but are deliberately omitted from general employee read schemas (`EmployeeResponse`). These fields will be exposed via administrative endpoints protected by Role-Based Access Control (RBAC) in Task 5.
- **Enterprise History Tables:** `salary_revisions` (2,459 records) and `employee_assignments` (1,606 records) are relational audit tables seeded and maintained in PostgreSQL. Dedicated CRUD and analytics endpoints for these historical entities are scheduled for rollout in Task 5.

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
