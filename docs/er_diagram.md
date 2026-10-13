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
        int department_id FK "References DEPARTMENTS(id)"
        int manager_id FK "Self-reference to EMPLOYEES(id)"
        numeric salary "Annual compensation in INR (CHECK > 0)"
        date hire_date "Date of joining"
        date exit_date "Optional exit / resignation date"
        string work_location "City / Office (Pune, Coimbatore, etc.)"
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
- An employee's direct reports can be loaded via `employee.direct_reports` while the reporting line is accessed via `employee.manager`.

### 3.3 Soft Delete Pattern (`is_active`)
- Deleting an employee physically destroys historical audit trails for payroll, attendance, and compliance.
- Records are preserved permanently; soft deletion toggles `is_active = FALSE`.

### 3.4 Constraints and Performance Indexes
- **Unique Constraints:**
  - `employees.email`: Enforces strict corporate email uniqueness.
  - `departments.name` & `departments.code`: Prevents duplicate departments.
  - `roles.title`: Prevents ambiguous duplicate job definitions.
  - `employee_roles(employee_id, role_id)`: Prevents assigning the same role twice to one person.
- **Check Constraints:**
  - `ck_employees_salary_positive`: Guarantees `salary > 0`.
- **Performance Indexes:**
  - `ix_employees_email`: Instant authentication and search lookups.
  - `ix_employees_name (last_name, first_name)`: Composite index for alphabetized roster queries.
  - `ix_employees_department_id`: Speeds up department employee listings.
  - `ix_employees_manager_id`: Fast manager-tree and direct-report traversals.
  - `ix_employees_is_active`: Efficient filtering of currently active workforce.
