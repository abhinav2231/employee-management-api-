# Aura Workforce OS API — Core & Multi-Phase API Contract
### Enterprise Workforce Management, Payroll & Accounting Engine

**System:** Aura Workforce OS  
**Base URL:** `http://localhost:8000/api/v1` (Docker Compose / Local Dev)  
**Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) | [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)  
**OpenAPI Specification:** [`docs/openapi_draft.json`](openapi_draft.json) (OpenAPI 3.1.0 maintained draft covering 64 operations)

---

## 1. 20-Task Roadmap Endpoints Matrix

The API contract spans the entire 20-task roadmap for Aura Workforce OS. **Tasks 1–4 are fully implemented and verified with 78 automated tests**; Tasks 5–20 define the stable contracts against which client, web, and reporting teams can build concurrently.

### Phase 1: Core Workforce Skeleton & Progression (Tasks 1–4 — Implemented)

| HTTP Method | Path | Request Body | Success Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/health` | None | `200 OK` | Top-level system liveness (`{"status": "ok"}`) |
| **GET** | `/health/ready` | None | `200 OK` | Database readiness check (`{"status": "ready", "database": "connected"}`) |
| **GET** | `/api/v1/health` | None | `200 OK` | Rich health status (`service`, `version`, `checks.database`) |
| **GET** | `/api/v1/departments` | None | `200 OK` | List all departments with active headcounts |
| **POST** | `/api/v1/departments` | `DepartmentCreate` | `201 Created` | Create department with unique text ID / code |
| **GET** | `/api/v1/departments/{id}` | None | `200 OK` | Retrieve single department by text ID or code |
| **PATCH**| `/api/v1/departments/{id}` | `DepartmentUpdate` | `200 OK` | Update department name, cost center, description |
| **DELETE**| `/api/v1/departments/{id}`| None | `204 No Content` | Delete empty department or soft-deactivate |
| **GET** | `/api/v1/departments/{id}/employees` | Query (`page`, `size`) | `200 OK` | Paginated employee roster for a department |
| **GET** | `/api/v1/roles` | None | `200 OK` | List all 58 job roles across 7 levels |
| **GET** | `/api/v1/roles/{id}` | None | `200 OK` | Retrieve single role by text ID (`R001`..`R058`) |
| **POST** | `/api/v1/employees` | `EmployeeCreate` | `201 Created` | Create employee (supports custom `EMP-XXXX` code) |
| **GET** | `/api/v1/employees` | Multi-column filters & sorting | `200 OK` | List employees with filters (`department_id`, `role_id`, `employment_status`, `work_location`, `work_mode`, `manager_id`, `hire_date_from`, `hire_date_to`, `q`, `sort=field|-field`, `page`, `size`) |
| **GET** | `/api/v1/employees/{id}` | None | `200 OK` | Retrieve single employee by ID or Code |
| **PATCH**| `/api/v1/employees/{id}` | `EmployeeUpdate` | `200 OK` | Partial update (manages cycle prevention, logs career assignment, creates salary revision if pay changes) |
| **DELETE**| `/api/v1/employees/{id}` | None | `204 No Content` | Soft delete employee (`is_active = false`, sets `exit_date = DEMO_TODAY`, reparents direct reports to skip-level manager) |
| **GET** | `/api/v1/employees/{id}/team` | None | `200 OK` | Direct reports reporting to manager |
| **GET** | `/api/v1/employees/{id}/assignments` | None | `200 OK` | Chronological career progression history (`ASG-...`) |

### Phase 2: Authentication, RBAC, Users & Audit Logs (Tasks 5–8 — Contract Defined)

| HTTP Method | Path | Request Body | Success Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/login` | `OAuth2Password` | `200 OK` | Authenticate with work email & password; returns JWT access + refresh tokens |
| **POST** | `/api/v1/auth/refresh` | `RefreshTokenRequest` | `200 OK` | Rotate and issue new access token |
| **POST** | `/api/v1/auth/logout` | None | `200 OK` | Invalidate active user session / revoke token |
| **GET** | `/api/v1/auth/me` | None (Bearer Token) | `200 OK` | Return current user identity, role, and permission scopes |
| **GET** | `/api/v1/users` | Query params | `200 OK` | Paginated system user list |
| **POST** | `/api/v1/users` | `UserCreate` | `201 Created` | Provision system user linked to employee |
| **GET** | `/api/v1/users/{id}` | None | `200 OK` | Get user account details |
| **PATCH**| `/api/v1/users/{id}` | `UserUpdate` | `200 OK` | Update user status, role, or credentials |
| **DELETE**| `/api/v1/users/{id}` | None | `204 No Content` | Deactivate system user account |
| **GET** | `/api/v1/auth/roles` | None | `200 OK` | List RBAC roles and permissions |
| **POST** | `/api/v1/auth/api-keys` | `ApiKeyCreate` | `201 Created` | Create service API key for background integration |
| **GET** | `/api/v1/auth/api-keys` | None | `200 OK` | List active service API keys |
| **DELETE**| `/api/v1/auth/api-keys/{id}` | None | `204 No Content` | Revoke service API key |
| **GET** | `/api/v1/audit/logs` | Query params | `200 OK` | Query security and compensation audit trail |

### Phase 3: Compensation, Monthly Payroll Runs & Compliance (Tasks 9–12 — Contract Defined)

| HTTP Method | Path | Request Body | Success Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/payroll/structures` | Query params | `200 OK` | List 12,295 salary component structures |
| **GET** | `/api/v1/payroll/structures/{employee_id}` | None | `200 OK` | Get active salary breakdown for employee |
| **POST** | `/api/v1/payroll/structures` | `SalaryStructureCreate` | `201 Created` | Define employee monthly salary breakdown |
| **GET** | `/api/v1/payroll/revisions` | Query params | `200 OK` | List historical compensation revisions |
| **POST** | `/api/v1/payroll/revisions` | `SalaryRevisionCreate` | `201 Created` | Log approved compensation revision |
| **POST** | `/api/v1/payroll/runs` | `PayrollRunCreate` | `201 Created` | Trigger monthly payroll calculation run (gross, LOP, tax, net) |
| **GET** | `/api/v1/payroll/runs` | Query params | `200 OK` | List payroll runs by month/status |
| **GET** | `/api/v1/payroll/runs/{id}` | None | `200 OK` | Detailed payroll run summary and totals |
| **POST** | `/api/v1/payroll/runs/{id}/approve` | None | `200 OK` | Approve and lock monthly payroll run |
| **GET** | `/api/v1/payroll/runs/{id}/payslips` | Query params | `200 OK` | List individual payslips in run |
| **GET** | `/api/v1/payroll/payslips/{id}` | None | `200 OK` | Get detailed payslip breakdown |
| **GET** | `/api/v1/payroll/compliance/pf` | Query params | `200 OK` | Provident Fund (PF) statutory compliance report |
| **GET** | `/api/v1/payroll/compliance/esi` | Query params | `200 OK` | Employee State Insurance (ESI) compliance report |
| **GET** | `/api/v1/payroll/compliance/tds` | Query params | `200 OK` | Tax Deducted at Source (TDS) tax report |

### Phase 4: Attendance, Leaves & Timesheets (Tasks 13–16 — Contract Defined)

| HTTP Method | Path | Request Body | Success Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/attendance/check-in` | `CheckInRequest` | `201 Created` | Clock-in daily timestamp |
| **POST** | `/api/v1/attendance/check-out` | `CheckOutRequest` | `200 OK` | Clock-out daily timestamp & calculate hours |
| **GET** | `/api/v1/attendance` | Query (`date_from`, `date_to`, `status`) | `200 OK` | Query 150,155 attendance logs across 18-month history |
| **GET** | `/api/v1/attendance/summary` | Query (`month`, `employee_id`) | `200 OK` | Aggregate monthly attendance metrics (worked, LOP, overtime) |
| **POST** | `/api/v1/leaves/requests` | `LeaveRequestCreate` | `201 Created` | Submit paid/unpaid leave request |
| **GET** | `/api/v1/leaves/requests` | Query params | `200 OK` | List pending and processed leave requests |
| **PATCH**| `/api/v1/leaves/requests/{id}` | `LeaveActionUpdate` | `200 OK` | Manager approve or reject leave request |
| **GET** | `/api/v1/leaves/balances/{employee_id}` | None | `200 OK` | Current leave quota balances |
| **GET** | `/api/v1/shifts` | None | `200 OK` | List work shifts |
| **GET** | `/api/v1/holidays` | Query (`year`) | `200 OK` | Official company holiday schedule |

### Phase 5: Analytics, Exports & Webhooks (Tasks 17–20 — Contract Defined)

| HTTP Method | Path | Request Body | Success Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/analytics/headcount` | Query params | `200 OK` | Headcount trends, new hires, leavers |
| **GET** | `/api/v1/analytics/attrition` | Query params | `200 OK` | Departmental attrition and tenure analysis |
| **GET** | `/api/v1/analytics/payroll-cost`| Query params | `200 OK` | Total cost to company (CTC) trend analysis |
| **POST** | `/api/v1/reports/export` | `ReportExportRequest` | `202 Accepted` | Asynchronously schedule CSV/PDF/XLSX export |
| **GET** | `/api/v1/reports/export/{job_id}` | None | `200 OK` | Download generated export artifact |
| **GET** | `/api/v1/webhooks` | None | `200 OK` | List active webhook event subscriptions |
| **POST** | `/api/v1/webhooks` | `WebhookCreate` | `201 Created` | Register webhook endpoint (e.g. `employee.created`) |
| **DELETE**| `/api/v1/webhooks/{id}` | None | `204 No Content` | Remove webhook subscription |

---

## 2. Standard Error Envelope

All API errors return a uniform, machine-readable envelope with standard error codes and request tracing:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Joining date cannot be in the future (after 2026-09-30)",
    "details": [
      {
        "field": "hire_date",
        "issue": "Joining date cannot be in the future (after 2026-09-30)"
      }
    ],
    "request_id": "req-9b8a7c6d5e"
  },
  "detail": "Joining date cannot be in the future (after 2026-09-30)",
  "error_code": "VALIDATION_ERROR",
  "field": "hire_date"
}
```

### Standard Error Codes:
- `VALIDATION_ERROR` (HTTP 422): Schema validation, boundary violations, or regex format errors.
- `NOT_FOUND` (HTTP 404): Entity does not exist.
- `CONFLICT` (HTTP 409): Unique constraint violation (`work_email`, `employee_id`, `department_name`, etc.).
- `BAD_REQUEST` (HTTP 400): Business rule violation (e.g., hierarchical reporting cycles).
- `UNAUTHENTICATED` (HTTP 401): Missing or expired JWT token / invalid API key.
- `FORBIDDEN` (HTTP 403): Insufficient RBAC permission scopes.
- `INTERNAL_SERVER_ERROR` (HTTP 500): Unhandled server exception.

---

## 3. Data Dictionary (Natural Primary Keys)

All primary keys use natural string identifiers directly aligned with the master workbook:

| Entity | Primary Key Field | Format / Pattern | Example |
| :--- | :--- | :--- | :--- |
| **Department** | `department_id` | `D[0-9]{2}` | `D01`, `D02`, `D10` |
| **Role** | `role_id` | `R[0-9]{3}` | `R001`, `R015`, `R058` |
| **Employee** | `employee_id` | `EMP-[0-9]{4}` | `EMP-0001` .. `EMP-0745` |
| **Assignment** | `assignment_id` | `ASG-[0-9]{4}-[0-9]{2}` | `ASG-0001-01` |
| **Salary Revision**| `revision_id` | `REV-[0-9]{4}-[0-9]{2}` | `REV-0001-01` |
| **Salary Structure**| `structure_id`| `SAL-[0-9]{4}-[A-Z]+` | `SAL-0001-BASIC` |
| **Attendance** | `attendance_id` | `ATT-[0-9]{4}-[0-9]{8}` | `ATT-0001-20260901` |
| **Payroll Run** | `run_id` | `PR-[0-9]{4}-[0-9]{2}` | `PR-2026-09` |
| **Payslip Item** | `payroll_item_id` | `PI-[0-9]{4}-[0-9]{2}-[0-9]{4}` | `PI-2026-09-0001` |

*(Note: SQLAlchemy `@hybrid_property` getters and setters preserve compatibility for legacy callers accessing `.id`, `.code`, `.email`, or `.name`)*.
