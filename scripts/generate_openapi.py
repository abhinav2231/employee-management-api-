import json
import os

def generate_openapi():
    # Base FastAPI live export or comprehensive contract
    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": "Aura Workforce OS — API Specification",
            "description": "Enterprise Workforce Management, Payroll, Accounting & Compliance API (20-Task Roadmap Contract).",
            "version": "1.0.0",
            "contact": {
                "name": "Zenith Nova Technologies / Aura Workforce Platform Team",
                "email": "api-support@znova-demo.example"
            }
        },
        "servers": [
            {"url": "http://localhost:8000", "description": "Local Development / Docker Compose Server"},
            {"url": "https://api.workforce.auraworkforce.io", "description": "Production API"}
        ],
        "paths": {},
        "components": {
            "securitySchemes": {
                "OAuth2PasswordBearer": {
                    "type": "oauth2",
                    "flows": {
                        "password": {
                            "tokenUrl": "/api/v1/auth/login",
                            "scopes": {}
                        }
                    }
                },
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            },
            "schemas": {
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "NOT_FOUND"},
                                "message": {"type": "string", "example": "Employee not found"},
                                "details": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "field": {"type": "string", "example": "employee_id"},
                                            "issue": {"type": "string", "example": "Record does not exist"}
                                        }
                                    }
                                },
                                "request_id": {"type": "string", "example": "req-9a8b7c6d5e"}
                            },
                            "required": ["code", "message", "details"]
                        },
                        "detail": {"type": "string", "example": "Employee not found"},
                        "error_code": {"type": "string", "example": "NOT_FOUND"},
                        "field": {"type": "string", "nullable": True, "example": "id"}
                    },
                    "required": ["error"]
                },
                "HealthStatus": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "ok"}
                    },
                    "required": ["status"]
                },
                "HealthDetail": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "ok"},
                        "service": {"type": "string", "example": "employee_management_api"},
                        "version": {"type": "string", "example": "1.0.0"},
                        "checks": {
                            "type": "object",
                            "properties": {
                                "database": {"type": "string", "example": "ok"}
                            }
                        }
                    },
                    "required": ["status", "service", "version"]
                },
                "Department": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "example": "D01"},
                        "department_id": {"type": "string", "example": "D01"},
                        "department_name": {"type": "string", "example": "Engineering"},
                        "code": {"type": "string", "example": "D01"},
                        "name": {"type": "string", "example": "Engineering"},
                        "cost_center": {"type": "string", "nullable": True, "example": "CC-ENG"},
                        "description": {"type": "string", "nullable": True, "example": "Software and infrastructure engineering"},
                        "is_active": {"type": "boolean", "example": True},
                        "headcount": {"type": "integer", "example": 142}
                    },
                    "required": ["department_id", "department_name"]
                },
                "DepartmentCreate": {
                    "type": "object",
                    "properties": {
                        "department_id": {"type": "string", "example": "D11"},
                        "department_name": {"type": "string", "example": "Data Platform"},
                        "cost_center": {"type": "string", "nullable": True, "example": "CC-DATA"},
                        "description": {"type": "string", "nullable": True, "example": "Big data and analytics operations"},
                        "is_active": {"type": "boolean", "default": True}
                    },
                    "required": ["department_name"]
                },
                "Role": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "example": "R001"},
                        "role_id": {"type": "string", "example": "R001"},
                        "role_title": {"type": "string", "example": "Principal Architect"},
                        "title": {"type": "string", "example": "Principal Architect"},
                        "level": {"type": "string", "nullable": True, "example": "6"},
                        "grade": {"type": "string", "nullable": True, "example": "L6"},
                        "department_id": {"type": "string", "nullable": True, "example": "D01"},
                        "band_min_annual": {"type": "integer", "nullable": True, "example": 2800000},
                        "band_mid_annual": {"type": "integer", "nullable": True, "example": 3500000},
                        "band_max_annual": {"type": "integer", "nullable": True, "example": 4500000},
                        "overtime_eligible": {"type": "string", "example": "N"},
                        "band_year": {"type": "integer", "example": 2026},
                        "is_active": {"type": "boolean", "example": True}
                    },
                    "required": ["role_id", "role_title"]
                },
                "Employee": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "example": "EMP-0001"},
                        "employee_id": {"type": "string", "example": "EMP-0001"},
                        "employee_code": {"type": "string", "example": "EMP-0001"},
                        "first_name": {"type": "string", "example": "Priya"},
                        "last_name": {"type": "string", "example": "Nair"},
                        "full_name": {"type": "string", "example": "Priya Nair"},
                        "email": {"type": "string", "format": "email", "example": "priya.nair@znova-demo.example"},
                        "work_email": {"type": "string", "format": "email", "example": "priya.nair@znova-demo.example"},
                        "phone_number": {"type": "string", "example": "+919845012345"},
                        "department_id": {"type": "string", "example": "D01"},
                        "role_id": {"type": "string", "nullable": True, "example": "R001"},
                        "manager_id": {"type": "string", "nullable": True, "example": "EMP-0010"},
                        "salary": {"type": "number", "example": 2400000.00},
                        "hire_date": {"type": "string", "format": "date", "example": "2025-04-01"},
                        "exit_date": {"type": "string", "format": "date", "nullable": True, "example": None},
                        "work_location": {"type": "string", "example": "Bengaluru"},
                        "work_mode": {"type": "string", "example": "Hybrid"},
                        "employment_type": {"type": "string", "example": "Permanent"},
                        "employment_status": {"type": "string", "example": "Active"},
                        "exit_type": {"type": "string", "nullable": True, "example": None},
                        "exit_reason": {"type": "string", "nullable": True, "example": None},
                        "is_active": {"type": "boolean", "example": True}
                    },
                    "required": ["employee_id", "first_name", "last_name", "work_email", "department_id", "hire_date"]
                },
                "EmployeeAssignment": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "example": "ASG-0001-01"},
                        "assignment_id": {"type": "string", "example": "ASG-0001-01"},
                        "employee_id": {"type": "string", "example": "EMP-0001"},
                        "effective_from": {"type": "string", "format": "date", "example": "2025-04-01"},
                        "effective_to": {"type": "string", "format": "date", "nullable": True, "example": None},
                        "department_id": {"type": "string", "example": "D01"},
                        "role_id": {"type": "string", "example": "R001"},
                        "job_level": {"type": "string", "example": "6"},
                        "manager_id": {"type": "string", "nullable": True, "example": "EMP-0010"},
                        "change_reason": {"type": "string", "example": "Joining"}
                    },
                    "required": ["assignment_id", "employee_id", "effective_from"]
                },
                "SalaryRevision": {
                    "type": "object",
                    "properties": {
                        "revision_id": {"type": "string", "example": "REV-0001-01"},
                        "employee_id": {"type": "string", "example": "EMP-0001"},
                        "effective_from": {"type": "string", "format": "date", "example": "2026-04-01"},
                        "revision_reason": {"type": "string", "example": "Annual Appraisal"},
                        "previous_annual_fixed": {"type": "number", "example": 2200000.00},
                        "new_annual_fixed": {"type": "number", "example": 2500000.00},
                        "pct_change": {"type": "number", "example": 13.64},
                        "role_id_after": {"type": "string", "example": "R001"},
                        "approved_by": {"type": "string", "example": "VP People"}
                    },
                    "required": ["revision_id", "employee_id", "effective_from", "new_annual_fixed"]
                },
                "SalaryStructure": {
                    "type": "object",
                    "properties": {
                        "structure_id": {"type": "string", "example": "SAL-0001-BASIC"},
                        "employee_id": {"type": "string", "example": "EMP-0001"},
                        "component_id": {"type": "string", "example": "BASIC"},
                        "component_name": {"type": "string", "example": "Basic Salary"},
                        "component_type": {"type": "string", "example": "Earning"},
                        "monthly_amount": {"type": "number", "example": 100000.00},
                        "effective_from": {"type": "string", "format": "date", "example": "2025-04-01"},
                        "effective_to": {"type": "string", "format": "date", "nullable": True, "example": None}
                    },
                    "required": ["structure_id", "employee_id", "component_id", "monthly_amount"]
                },
                "AttendanceRecord": {
                    "type": "object",
                    "properties": {
                        "attendance_id": {"type": "string", "example": "ATT-0001-20260901"},
                        "employee_id": {"type": "string", "example": "EMP-0001"},
                        "attendance_date": {"type": "string", "format": "date", "example": "2026-09-01"},
                        "status": {"type": "string", "example": "PRESENT"},
                        "check_in": {"type": "string", "example": "09:15"},
                        "check_out": {"type": "string", "example": "18:22"},
                        "hours_worked": {"type": "number", "example": 9.12},
                        "overtime_hours": {"type": "number", "example": 0.0},
                        "late_flag": {"type": "string", "example": "N"}
                    },
                    "required": ["attendance_id", "employee_id", "attendance_date", "status"]
                },
                "PayrollRun": {
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string", "example": "PR-2026-09"},
                        "payroll_month": {"type": "string", "example": "2026-09"},
                        "period_start": {"type": "string", "format": "date", "example": "2026-09-01"},
                        "period_end": {"type": "string", "format": "date", "example": "2026-09-30"},
                        "total_employees": {"type": "integer", "example": 441},
                        "gross_total": {"type": "number", "example": 54200000.00},
                        "deductions_total": {"type": "number", "example": 8900000.00},
                        "net_total": {"type": "number", "example": 45300000.00},
                        "status": {"type": "string", "example": "Approved"}
                    },
                    "required": ["run_id", "payroll_month", "period_start", "period_end", "status"]
                },
                "Payslip": {
                    "type": "object",
                    "properties": {
                        "payroll_item_id": {"type": "string", "example": "PI-2026-09-0001"},
                        "run_id": {"type": "string", "example": "PR-2026-09"},
                        "employee_id": {"type": "string", "example": "EMP-0001"},
                        "period_start": {"type": "string", "format": "date", "example": "2026-09-01"},
                        "period_end": {"type": "string", "format": "date", "example": "2026-09-30"},
                        "payable_days": {"type": "number", "example": 30.0},
                        "lop_days": {"type": "number", "example": 0.0},
                        "gross_pay": {"type": "number", "example": 200000.00},
                        "total_deductions": {"type": "number", "example": 32000.00},
                        "net_pay": {"type": "number", "example": 168000.00}
                    },
                    "required": ["payroll_item_id", "run_id", "employee_id", "gross_pay", "net_pay"]
                },
                "TokenResponse": {
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                        "refresh_token": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
                        "token_type": {"type": "string", "example": "bearer"},
                        "expires_in": {"type": "integer", "example": 3600}
                    },
                    "required": ["access_token", "token_type"]
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "example": "USR-001"},
                        "username": {"type": "string", "example": "priya.nair@znova-demo.example"},
                        "employee_id": {"type": "string", "example": "EMP-0001"},
                        "role": {"type": "string", "example": "HR_ADMIN"},
                        "is_active": {"type": "boolean", "example": True}
                    },
                    "required": ["user_id", "username", "role"]
                },
                "LeaveRequest": {
                    "type": "object",
                    "properties": {
                        "request_id": {"type": "string", "example": "LV-2026-0042"},
                        "employee_id": {"type": "string", "example": "EMP-0001"},
                        "leave_type": {"type": "string", "example": "PAID_LEAVE"},
                        "start_date": {"type": "string", "format": "date", "example": "2026-10-05"},
                        "end_date": {"type": "string", "format": "date", "example": "2026-10-07"},
                        "days_count": {"type": "number", "example": 3.0},
                        "reason": {"type": "string", "example": "Personal family event"},
                        "status": {"type": "string", "example": "PENDING"}
                    },
                    "required": ["request_id", "employee_id", "leave_type", "start_date", "end_date", "status"]
                },
                "AuditLog": {
                    "type": "object",
                    "properties": {
                        "log_id": {"type": "string", "example": "AUD-998877"},
                        "timestamp": {"type": "string", "format": "date-time", "example": "2026-09-30T10:14:00Z"},
                        "user_id": {"type": "string", "example": "USR-001"},
                        "entity": {"type": "string", "example": "employees"},
                        "entity_id": {"type": "string", "example": "EMP-0001"},
                        "action": {"type": "string", "example": "UPDATE"},
                        "changes": {"type": "object", "example": {"salary": {"old": 2200000, "new": 2500000}}}
                    },
                    "required": ["log_id", "timestamp", "entity", "action"]
                },
                "Webhook": {
                    "type": "object",
                    "properties": {
                        "webhook_id": {"type": "string", "example": "WH-001"},
                        "url": {"type": "string", "example": "https://erp.enterprise.example/webhooks/workforce"},
                        "events": {"type": "array", "items": {"type": "string"}, "example": ["employee.created", "payroll.approved"]},
                        "is_active": {"type": "boolean", "example": True}
                    },
                    "required": ["webhook_id", "url", "events"]
                }
            }
        }
    }

    # Helper to add an endpoint easily
    def add_op(path, method, tag, summary, op_id, req_schema=None, resp_schema="HealthStatus", status="200", params=None):
        if path not in spec["paths"]:
            spec["paths"][path] = {}
        op = {
            "tags": [tag],
            "summary": summary,
            "operationId": op_id,
            "responses": {
                status: {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{resp_schema}"} if isinstance(resp_schema, str) else resp_schema
                        }
                    }
                },
                "400": {"description": "Bad Request", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                "404": {"description": "Resource Not Found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                "422": {"description": "Validation Error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
            }
        }
        if req_schema:
            op["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{req_schema}"} if isinstance(req_schema, str) else req_schema
                    }
                }
            }
        if params:
            op["parameters"] = params
        spec["paths"][path][method.lower()] = op

    # --- TASKS 1-4: CORE WORKFORCE & HEALTH ---
    add_op("/health", "GET", "Health", "Top Level Health", "get_health_root", resp_schema="HealthStatus")
    add_op("/health/ready", "GET", "Health", "Top Level Readiness", "get_readiness_root", resp_schema={"type": "object", "properties": {"status": {"type": "string"}}})
    add_op("/api/v1/health", "GET", "Health", "System Health Metadata", "get_api_v1_health", resp_schema="HealthDetail")
    
    # Departments
    add_op("/api/v1/departments", "GET", "Departments", "List Departments", "list_departments", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/Department"}})
    add_op("/api/v1/departments", "POST", "Departments", "Create Department", "create_department", req_schema="DepartmentCreate", resp_schema="Department", status="201")
    add_op("/api/v1/departments/{id}", "GET", "Departments", "Get Department By ID or Code", "get_department", resp_schema="Department", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/departments/{id}", "PATCH", "Departments", "Update Department", "update_department", req_schema="DepartmentCreate", resp_schema="Department", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/departments/{id}", "DELETE", "Departments", "Delete/Deactivate Department", "delete_department", resp_schema={"type": "object"}, status="204", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/departments/{id}/employees", "GET", "Departments", "Department Roster", "get_department_employees", resp_schema={"type": "object", "properties": {"items": {"type": "array", "items": {"$ref": "#/components/schemas/Employee"}}}}, params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])

    # Roles
    add_op("/api/v1/roles", "GET", "Roles", "List Roles", "list_roles", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/Role"}})
    add_op("/api/v1/roles/{id}", "GET", "Roles", "Get Role By ID or Code", "get_role", resp_schema="Role", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])

    # Employees
    add_op("/api/v1/employees", "POST", "Employees", "Create Employee", "create_employee", req_schema="Employee", resp_schema="Employee", status="201")
    add_op("/api/v1/employees", "GET", "Employees", "List Employees Filtered", "list_employees", resp_schema={"type": "object", "properties": {"items": {"type": "array", "items": {"$ref": "#/components/schemas/Employee"}}, "total": {"type": "integer"}}}, params=[
        {"name": "department_id", "in": "query", "schema": {"type": "string"}},
        {"name": "role_id", "in": "query", "schema": {"type": "string"}},
        {"name": "employment_status", "in": "query", "schema": {"type": "string"}},
        {"name": "work_location", "in": "query", "schema": {"type": "string"}},
        {"name": "work_mode", "in": "query", "schema": {"type": "string"}},
        {"name": "manager_id", "in": "query", "schema": {"type": "string"}},
        {"name": "hire_date_from", "in": "query", "schema": {"type": "string", "format": "date"}},
        {"name": "hire_date_to", "in": "query", "schema": {"type": "string", "format": "date"}},
        {"name": "q", "in": "query", "schema": {"type": "string"}},
        {"name": "sort", "in": "query", "schema": {"type": "string"}},
        {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
        {"name": "size", "in": "query", "schema": {"type": "integer", "default": 50}}
    ])
    add_op("/api/v1/employees/{id}", "GET", "Employees", "Get Employee By ID", "get_employee", resp_schema="Employee", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/employees/{id}", "PATCH", "Employees", "Update Employee", "update_employee", req_schema="Employee", resp_schema="Employee", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/employees/{id}", "DELETE", "Employees", "Soft Delete Employee", "delete_employee", resp_schema={"type": "object"}, status="204", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/employees/{id}/team", "GET", "Employees", "Get Direct Reports", "get_employee_team", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/Employee"}}, params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/employees/{id}/assignments", "GET", "Employees", "Get Employee Assignments Progression", "get_employee_assignments", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/EmployeeAssignment"}}, params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])

    # --- TASKS 5-8: AUTHENTICATION, RBAC & SECURITY ---
    add_op("/api/v1/auth/login", "POST", "Auth", "User Login (OAuth2 Password)", "auth_login", req_schema={"type": "object", "properties": {"username": {"type": "string"}, "password": {"type": "string"}}}, resp_schema="TokenResponse")
    add_op("/api/v1/auth/refresh", "POST", "Auth", "Refresh Access Token", "auth_refresh", req_schema={"type": "object", "properties": {"refresh_token": {"type": "string"}}}, resp_schema="TokenResponse")
    add_op("/api/v1/auth/logout", "POST", "Auth", "Logout User Session", "auth_logout", resp_schema={"type": "object", "properties": {"status": {"type": "string"}}})
    add_op("/api/v1/auth/me", "GET", "Auth", "Get Current Authenticated User", "auth_me", resp_schema="User")
    add_op("/api/v1/users", "GET", "Users", "List System Users", "list_users", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/User"}})
    add_op("/api/v1/users", "POST", "Users", "Create User Account", "create_user", req_schema="User", resp_schema="User", status="201")
    add_op("/api/v1/users/{id}", "GET", "Users", "Get User By ID", "get_user", resp_schema="User", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/users/{id}", "PATCH", "Users", "Update User Status/Roles", "update_user", req_schema="User", resp_schema="User", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/users/{id}", "DELETE", "Users", "Deactivate User", "delete_user", resp_schema={"type": "object"}, status="204", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/auth/roles", "GET", "RBAC", "List RBAC Roles & Permissions", "list_rbac_roles", resp_schema={"type": "array", "items": {"type": "object"}})
    add_op("/api/v1/auth/api-keys", "POST", "API Keys", "Create API Key", "create_api_key", req_schema={"type": "object", "properties": {"name": {"type": "string"}}}, resp_schema={"type": "object", "properties": {"key": {"type": "string"}}}, status="201")
    add_op("/api/v1/auth/api-keys", "GET", "API Keys", "List API Keys", "list_api_keys", resp_schema={"type": "array", "items": {"type": "object"}})
    add_op("/api/v1/auth/api-keys/{id}", "DELETE", "API Keys", "Revoke API Key", "revoke_api_key", resp_schema={"type": "object"}, status="204", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/audit/logs", "GET", "Audit", "Query Security & Change Audit Logs", "list_audit_logs", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/AuditLog"}})

    # --- TASKS 9-12: COMPENSATION, PAYROLL RUNS & COMPLIANCE ---
    add_op("/api/v1/payroll/structures", "GET", "Payroll", "List Salary Structures", "list_salary_structures", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/SalaryStructure"}})
    add_op("/api/v1/payroll/structures/{employee_id}", "GET", "Payroll", "Get Employee Salary Structure", "get_employee_salary_structure", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/SalaryStructure"}}, params=[{"name": "employee_id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/payroll/structures", "POST", "Payroll", "Create/Update Salary Component", "create_salary_structure", req_schema="SalaryStructure", resp_schema="SalaryStructure", status="201")
    add_op("/api/v1/payroll/revisions", "GET", "Payroll", "List Salary Revisions", "list_salary_revisions", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/SalaryRevision"}})
    add_op("/api/v1/payroll/revisions", "POST", "Payroll", "Record Salary Revision", "create_salary_revision", req_schema="SalaryRevision", resp_schema="SalaryRevision", status="201")
    add_op("/api/v1/payroll/runs", "POST", "Payroll", "Execute Monthly Payroll Run", "create_payroll_run", req_schema={"type": "object", "properties": {"payroll_month": {"type": "string"}}}, resp_schema="PayrollRun", status="201")
    add_op("/api/v1/payroll/runs", "GET", "Payroll", "List Payroll Runs", "list_payroll_runs", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/PayrollRun"}})
    add_op("/api/v1/payroll/runs/{id}", "GET", "Payroll", "Get Payroll Run Summary", "get_payroll_run", resp_schema="PayrollRun", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/payroll/runs/{id}/approve", "POST", "Payroll", "Approve & Lock Payroll Run", "approve_payroll_run", resp_schema="PayrollRun", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/payroll/runs/{id}/payslips", "GET", "Payroll", "List Payslips in Run", "list_run_payslips", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/Payslip"}}, params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/payroll/payslips/{id}", "GET", "Payroll", "Get Detailed Payslip", "get_payslip", resp_schema="Payslip", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/payroll/compliance/pf", "GET", "Compliance", "Provident Fund Statutory Report", "get_pf_report", resp_schema={"type": "object", "properties": {"total_pf": {"type": "number"}}})
    add_op("/api/v1/payroll/compliance/esi", "GET", "Compliance", "ESI Statutory Report", "get_esi_report", resp_schema={"type": "object", "properties": {"total_esi": {"type": "number"}}})
    add_op("/api/v1/payroll/compliance/tds", "GET", "Compliance", "TDS Tax Deduction Report", "get_tds_report", resp_schema={"type": "object", "properties": {"total_tds": {"type": "number"}}})

    # --- TASKS 13-16: ATTENDANCE, LEAVE & TIMESHEETS ---
    add_op("/api/v1/attendance/check-in", "POST", "Attendance", "Employee Check-in", "attendance_check_in", req_schema={"type": "object", "properties": {"employee_id": {"type": "string"}}}, resp_schema="AttendanceRecord", status="201")
    add_op("/api/v1/attendance/check-out", "POST", "Attendance", "Employee Check-out", "attendance_check_out", req_schema={"type": "object", "properties": {"employee_id": {"type": "string"}}}, resp_schema="AttendanceRecord")
    add_op("/api/v1/attendance", "GET", "Attendance", "Query Attendance Records", "list_attendance", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/AttendanceRecord"}}, params=[
        {"name": "employee_id", "in": "query", "schema": {"type": "string"}},
        {"name": "date_from", "in": "query", "schema": {"type": "string", "format": "date"}},
        {"name": "date_to", "in": "query", "schema": {"type": "string", "format": "date"}},
        {"name": "status", "in": "query", "schema": {"type": "string"}}
    ])
    add_op("/api/v1/attendance/summary", "GET", "Attendance", "Monthly Attendance Summary", "get_attendance_summary", resp_schema={"type": "object", "properties": {"present_days": {"type": "number"}}})
    add_op("/api/v1/leaves/requests", "POST", "Leaves", "Submit Leave Request", "create_leave_request", req_schema="LeaveRequest", resp_schema="LeaveRequest", status="201")
    add_op("/api/v1/leaves/requests", "GET", "Leaves", "List Leave Requests", "list_leave_requests", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/LeaveRequest"}})
    add_op("/api/v1/leaves/requests/{id}", "PATCH", "Leaves", "Approve/Reject Leave Request", "update_leave_request", req_schema={"type": "object", "properties": {"status": {"type": "string"}}}, resp_schema="LeaveRequest", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/leaves/balances/{employee_id}", "GET", "Leaves", "Get Leave Balances", "get_leave_balances", resp_schema={"type": "object", "properties": {"paid_leave_balance": {"type": "number"}}}, params=[{"name": "employee_id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/shifts", "GET", "Attendance", "List Work Shifts", "list_shifts", resp_schema={"type": "array", "items": {"type": "object"}})
    add_op("/api/v1/holidays", "GET", "Attendance", "Official Holiday Calendar", "list_holidays", resp_schema={"type": "array", "items": {"type": "object"}})

    # --- TASKS 17-20: ANALYTICS, EXPORTS & WEBHOOKS ---
    add_op("/api/v1/analytics/headcount", "GET", "Analytics", "Headcount Trends & Breakdown", "get_headcount_analytics", resp_schema={"type": "object", "properties": {"active_headcount": {"type": "integer"}}})
    add_op("/api/v1/analytics/attrition", "GET", "Analytics", "Attrition & Turnover Analysis", "get_attrition_analytics", resp_schema={"type": "object", "properties": {"attrition_rate": {"type": "number"}}})
    add_op("/api/v1/analytics/payroll-cost", "GET", "Analytics", "Payroll Cost Analysis", "get_payroll_cost_analytics", resp_schema={"type": "object", "properties": {"monthly_cost": {"type": "number"}}})
    add_op("/api/v1/reports/export", "POST", "Reports", "Trigger Async Report Export", "create_export_job", req_schema={"type": "object", "properties": {"report_type": {"type": "string"}}}, resp_schema={"type": "object", "properties": {"job_id": {"type": "string"}}}, status="202")
    add_op("/api/v1/reports/export/{job_id}", "GET", "Reports", "Download Report Export File", "download_export_file", resp_schema={"type": "string"}, params=[{"name": "job_id", "in": "path", "required": True, "schema": {"type": "string"}}])
    add_op("/api/v1/webhooks", "GET", "Webhooks", "List Webhook Subscriptions", "list_webhooks", resp_schema={"type": "array", "items": {"$ref": "#/components/schemas/Webhook"}})
    add_op("/api/v1/webhooks", "POST", "Webhooks", "Register Webhook Subscription", "create_webhook", req_schema="Webhook", resp_schema="Webhook", status="201")
    add_op("/api/v1/webhooks/{id}", "DELETE", "Webhooks", "Unsubscribe Webhook", "delete_webhook", resp_schema={"type": "object"}, status="204", params=[{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}])

    os.makedirs("docs", exist_ok=True)
    out_path = os.path.join("docs", "openapi_draft.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)

    total_paths = len(spec["paths"])
    total_ops = sum(len(methods) for methods in spec["paths"].values())
    print(f"Generated {out_path} with {total_paths} distinct paths and {total_ops} operations!")

if __name__ == "__main__":
    generate_openapi()
