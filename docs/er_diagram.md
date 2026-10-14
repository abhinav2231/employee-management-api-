# Aura Workforce OS — Entity Relationship (ER) Data Model

## 1. Overview
The **Aura Workforce OS** data model provides the normalized relational foundation for workforce records, organization hierarchy, multi-role assignments, compensation records, daily attendance tracking, and career progression history.

---

## 2. Mermaid Entity Relationship Diagram

```mermaid
erDiagram
    DEPARTMENTS ||--o{ EMPLOYEES : "employs"
    EMPLOYEES ||--o{ EMPLOYEES : "manages (manager_id)"
    EMPLOYEES ||--o{ EMPLOYEE_ROLES : "holds"
    ROLES ||--o{ EMPLOYEE_ROLES : "assigned_to"
    EMPLOYEES ||--o{ EMPLOYEE_ASSIGNMENTS : "career_history"
    DEPARTMENTS ||--o{ EMPLOYEE_ASSIGNMENTS : "department_assignment"
    ROLES ||--o{ EMPLOYEE_ASSIGNMENTS : "role_assignment"
    EMPLOYEES ||--o{ SALARY_RECORDS : "compensation_history"
    EMPLOYEES ||--o{ ATTENDANCE : "attendance_logs"

    DEPARTMENTS {
        int id PK "Auto-increment ID"
        string code UK "Department code (e.g. D00 to D10)"
        string name UK "Department name (e.g. Engineering)"
        string cost_center "Cost center (e.g. CC-100)"
        string description "Description"
        boolean is_active "Active department status"
        timestamp created_at "Audit timestamp"
        timestamp updated_at "Audit timestamp"
    }

    ROLES {
        int id PK "Auto-increment ID"
        string code UK "Role code (e.g. R001 to R058)"
        string title UK "Role title (e.g. Tech Lead)"
        int department_id FK "References DEPARTMENTS(id)"
        string level "Seniority grade (L1 Associate to L7 Executive)"
        boolean is_active "Active role status"
        timestamp created_at "Audit timestamp"
        timestamp updated_at "Audit timestamp"
    }

    EMPLOYEES {
        int id PK "Auto-increment ID"
        string employee_code UK "Unique code (EMP-0001 to EMP-0745)"
        string first_name "First name"
        string last_name "Last name"
        string email UK "Corporate work email (@auraworkforce.io)"
        string phone_number "Indian format corporate phone number"
        int department_id FK "References DEPARTMENTS(id)"
        int manager_id FK "Self-reference to EMPLOYEES(id)"
        numeric salary "Annual compensation in INR (CHECK > 0)"
        date hire_date "Date of joining"
        date exit_date "Optional exit / resignation date"
        string work_location "City / Office (Pune, Bangalore, etc.)"
        string employment_type "Permanent, Contract, etc."
        boolean is_active "Active employment status flag"
        timestamp created_at "Audit creation timestamp"
        timestamp updated_at "Audit last-update timestamp"
    }

    EMPLOYEE_ROLES {
        int id PK "Auto-increment ID"
        int employee_id FK "References EMPLOYEES(id)"
        int role_id FK "References ROLES(id)"
        boolean is_primary "Primary role flag"
        timestamp assigned_at "Assignment audit timestamp"
    }

    EMPLOYEE_ASSIGNMENTS {
        int id PK "Auto-increment ID"
        string assignment_code UK "Assignment code (AS-00001)"
        int employee_id FK "References EMPLOYEES(id)"
        date effective_from "Effective start date"
        date effective_to "Effective end date"
        int department_id FK "References DEPARTMENTS(id)"
        int role_id FK "References ROLES(id)"
        int job_level "Job level (1-7)"
        int manager_id FK "References EMPLOYEES(id)"
        string change_reason "Joining, Promotion, Manager Change, etc."
    }

    SALARY_RECORDS {
        int id PK "Auto-increment ID"
        int employee_id FK "References EMPLOYEES(id)"
        string pay_period UK "Pay period (YYYY-MM)"
        date effective_date "Payroll release date"
        numeric base_salary "Fixed base salary (CHECK >= 0)"
        numeric allowances "HRA and allowances (>= 0)"
        numeric bonuses "Variable bonuses and overtime (>= 0)"
        numeric deductions "Statutory deductions (>= 0)"
        numeric net_salary "Net pay amount (CHECK >= 0)"
        string currency "Currency code (default INR)"
        string payment_status "PAID, PROCESSED, PENDING"
    }

    ATTENDANCE {
        int id PK "Auto-increment ID"
        int employee_id FK "References EMPLOYEES(id)"
        date date UK "Date of attendance"
        string status "PRESENT, REMOTE, PAID_LEAVE, UNPAID_LEAVE, HALF_DAY, ABSENT"
        time check_in "Daily check-in timestamp"
        time check_out "Daily check-out timestamp"
        numeric hours_worked "Total hours logged"
        string notes "WFH or Leave Code description"
    }
```

---

## 3. Architectural Design Decisions

### 3.1 Role Cardinality Decision: One Role vs Many Roles
- **Decision:** Employees can hold **multiple roles** through the `employee_roles` association entity, with an `is_primary` flag.
- **Rationale:** 
  1. In modern organizations, employees have a single primary contractual position (e.g., *Senior Software Engineer*) used for salary bands and payroll.
  2. However, team members often take on functional, operational, or governance responsibilities (e.g., *Hiring Bar Raiser*, *Incident Commander*, *Team Lead*).
  3. Storing roles in a junction table (`employee_roles`) ensures zero breaking database migrations when secondary duties or future security permissions are added.

### 3.2 Organizational Hierarchy (Self-Referential Manager Relationship)
- `manager_id` is a nullable foreign key pointing to `employees.id` with `ON DELETE SET NULL`.
- Top-level leadership (e.g. CEO) has `manager_id = NULL`.
- Cycle detection is enforced at service layer preventing A -> B -> A or multi-level circular reporting trees.

### 3.3 Soft Delete Pattern (`is_active`)
- Deleting an employee physically destroys historical audit trails for payroll, attendance, and compliance.
- Records are preserved permanently; soft deletion toggles `is_active = FALSE`.
- When a manager is soft-deleted, their direct reports are safely reassigned to their supervisor to prevent dangling trees.

### 3.4 Constraints and Performance Indexes
- **Unique Constraints:**
  - `employees.email`: Enforces strict corporate email uniqueness.
  - `employees.employee_code`: Guarantees unique business employee IDs.
  - `departments.name` & `departments.code`: Prevents duplicate departments.
  - `roles.title`: Prevents ambiguous duplicate job definitions.
  - `employee_roles(employee_id, role_id)`: Prevents assigning the same role twice to one person.
  - `salary_records(employee_id, pay_period)`: Ensures idempotency per employee pay run.
  - `attendance(employee_id, date)`: Prevents duplicate attendance logs for same date.
- **Check Constraints:**
  - `ck_employees_salary_positive`: Guarantees `salary > 0`.
  - `ck_salary_base_positive`: Guarantees `base_salary >= 0`.
  - `ck_salary_net_positive`: Guarantees `net_salary >= 0`.
