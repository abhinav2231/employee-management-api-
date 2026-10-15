# Aura Workforce OS — Entity Relationship (ER) Data Model

## 1. Overview
The **Aura Workforce OS** data model provides the relational foundation for workforce records, organizational hierarchy, career progression (`employee_assignments`), compensation revisions (`salary_revisions`), component breakdowns (`salary_structures`), and daily attendance tracking (`attendance`).

---

## 2. Mermaid Entity Relationship Diagram

```mermaid
erDiagram
    DEPARTMENTS ||--o{ EMPLOYEES : "employs"
    DEPARTMENTS ||--o{ ROLES : "defines"
    ROLES ||--o{ EMPLOYEES : "current_role"
    EMPLOYEES ||--o{ EMPLOYEES : "manages (manager_id)"
    EMPLOYEES ||--o{ EMPLOYEE_ROLES : "holds"
    ROLES ||--o{ EMPLOYEE_ROLES : "assigned_to"
    EMPLOYEES ||--o{ EMPLOYEE_ASSIGNMENTS : "career_progression"
    DEPARTMENTS ||--o{ EMPLOYEE_ASSIGNMENTS : "dept_assignment"
    ROLES ||--o{ EMPLOYEE_ASSIGNMENTS : "role_assignment"
    EMPLOYEES ||--o{ SALARY_STRUCTURES : "salary_components"
    EMPLOYEES ||--o{ SALARY_REVISIONS : "salary_revisions"
    EMPLOYEES ||--o{ ATTENDANCE : "attendance_logs"

    DEPARTMENTS {
        string department_id PK "e.g. D01"
        string department_name UK
        string cost_center
        string description
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    ROLES {
        string role_id PK "e.g. R001"
        string role_title UK
        string department_id FK
        string level
        string grade
        int band_min_annual
        int band_mid_annual
        int band_max_annual
        string overtime_eligible
        int band_year
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    EMPLOYEES {
        string employee_id PK "e.g. EMP-0001"
        string first_name
        string last_name
        string full_name
        string work_email UK
        string phone_number
        string gender
        date date_of_birth
        date hire_date
        date exit_date
        string department_id FK
        string role_id FK
        string manager_id FK
        numeric salary
        string employment_status
        string employment_type
        string exit_type
        string exit_reason
        string work_location
        string work_mode
        string highest_education
        numeric prior_experience_years
        int career_gap_months
        numeric commute_distance_km
        string pf_applicable
        string esi_applicable
        int notice_period_days
        date resignation_date
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    EMPLOYEE_ASSIGNMENTS {
        string assignment_id PK "e.g. ASG-0001-01"
        string employee_id FK
        date effective_from
        date effective_to
        string department_id FK
        string role_id FK
        string job_level
        string manager_id FK
        string change_reason
        timestamp created_at
        timestamp updated_at
    }

    SALARY_STRUCTURES {
        string structure_id PK "e.g. SAL-0001-BASIC"
        string employee_id FK
        string component_id
        string component_name
        string component_type
        numeric monthly_amount
        date effective_from
        date effective_to
        string revision_id
        timestamp created_at
        timestamp updated_at
    }

    SALARY_REVISIONS {
        string revision_id PK "e.g. REV-0001-01"
        string employee_id FK
        date effective_from
        string revision_reason
        numeric previous_annual_fixed
        numeric new_annual_fixed
        numeric pct_change
        string role_id_after
        string approved_by
        timestamp created_at
        timestamp updated_at
    }

    ATTENDANCE {
        string attendance_id PK "e.g. ATT-0001-20260901"
        string employee_id FK
        date attendance_date
        string weekday
        string status
        string leave_type_code
        string check_in
        string check_out
        numeric hours_worked
        numeric overtime_hours
        string late_flag
        string source
        string data_quality_flag
        string department_id FK
        timestamp created_at
        timestamp updated_at
    }
}
```

---

## 3. Architectural Design Decisions

1. **Natural Text Primary Keys:** All tables use the exact text primary keys from Workbook 01 (`EMP-0001`, `D01`, `R001`, `ASG-...`, `REV-...`, `SAL-...`, `ATT-...`).
2. **Role Cardinality (One Current Role + Historical Progression):** Each employee has one current role (`employees.role_id`), while historical role/department/manager changes are tracked in `employee_assignments`. An optional `employee_roles` junction table is also maintained for secondary functional duties.
3. **Self-Referential Manager Hierarchy & Cycle Detection:** `employees.manager_id` references `employees.employee_id` (ON DELETE SET NULL). Service-layer validation blocks self-management and multi-hop circular reporting chains.
4. **Constraints & Indexes:**
   - Unique constraints on `employees.work_email`, `departments.department_name`, `roles.role_title`, and `attendance(employee_id, attendance_date)`.
   - Check constraints: `salary IS NULL OR salary > 0` and `exit_date IS NULL OR exit_date >= hire_date`.
   - Indexes on `department_id`, `manager_id`, `(last_name, first_name)`, `employment_status`, `work_location`, `work_mode`, and `is_active`.
