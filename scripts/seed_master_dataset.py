import sys
import os
import datetime
from decimal import Decimal
import openpyxl
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.department import Department
from app.models.role import Role, EmployeeRole
from app.models.employee import Employee
from app.models.assignment import EmployeeAssignment


def parse_date(val):
    if val is None:
        return None
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    try:
        return datetime.date.fromisoformat(str(val))
    except Exception:
        return None


def seed_master_dataset():
    excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "01_LedgerForge_Python_Master_Dataset.xlsx")
    if not os.path.exists(excel_path):
        print(f"[ERROR] Excel file not found at: {excel_path}")
        return

    print(f"[INFO] Loading master dataset from: {excel_path}")
    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)

    db: Session = SessionLocal()
    engine.echo = False

    try:
        print("[INFO] Cleaning existing database tables...")
        db.execute(text("TRUNCATE TABLE employee_assignments, employee_roles, employees, roles, departments CASCADE;"))
        db.commit()

        # 1. Seed Departments
        print("[INFO] Seeding departments (Reference sheet: departments)...")
        dept_sheet = wb["departments"]
        dept_map = {} # code -> id
        dept_rows = list(dept_sheet.iter_rows(values_only=True))
        for row in dept_rows[1:]:
            d_code, d_name, cost_center, desc = row[0], row[1], row[2], row[3]
            if not d_code:
                continue
            dept = Department(
                code=str(d_code).strip(),
                name=str(d_name).strip(),
                cost_center=str(cost_center).strip() if cost_center else None,
                description=str(desc).strip() if desc else None,
                is_active=True,
            )
            db.add(dept)
            db.flush()
            dept_map[dept.code] = dept.id
        db.commit()
        print(f"  + Seeded {len(dept_map)} departments.")

        # 2. Seed Roles
        print("[INFO] Seeding roles (Reference sheet: roles)...")
        roles_sheet = wb["roles"]
        role_map = {} # code -> id
        role_rows = list(roles_sheet.iter_rows(values_only=True))
        for row in role_rows[1:]:
            r_code = row[0]
            d_code = row[1]
            title = row[2]
            grade = row[4]
            if not r_code:
                continue
            role = Role(
                code=str(r_code).strip(),
                title=str(title).strip(),
                department_id=dept_map.get(str(d_code).strip()) if d_code else None,
                level=str(grade).strip() if grade else None,
                is_active=True,
            )
            db.add(role)
            db.flush()
            role_map[role.code] = role.id
        db.commit()
        print(f"  + Seeded {len(role_map)} roles across 7 levels.")

        # 3. Read latest salary for each employee from salary_revisions
        print("[INFO] Processing salary revisions for employee compensation...")
        salary_sheet = wb["salary_revisions"]
        salary_rows = list(salary_sheet.iter_rows(values_only=True))
        emp_salary_map = {}
        for row in salary_rows[1:]:
            emp_code = row[1]
            new_annual = row[5]
            if emp_code and new_annual is not None:
                emp_salary_map[str(emp_code).strip()] = Decimal(str(new_annual))

        # 4. Seed Employees (Pass 1: Insert without manager_id)
        print("[INFO] Seeding employees (Pass 1 - People sheet: employees)...")
        emp_sheet = wb["employees"]
        emp_rows = list(emp_sheet.iter_rows(values_only=True))
        
        emp_code_to_id = {}
        emp_manager_codes = {}
        emp_primary_roles = {}

        for row in emp_rows[1:]:
            emp_code = str(row[0]).strip()
            first_name = str(row[1]).strip()
            last_name = str(row[2]).strip()
            email = str(row[4]).strip()
            hire_date = parse_date(row[7])
            exit_date = parse_date(row[8])
            status_str = str(row[9]).strip() if row[9] else "Active"
            emp_type = str(row[10]).strip() if row[10] else "Permanent"
            d_code = str(row[11]).strip() if row[11] else None
            r_code = str(row[12]).strip() if row[12] else None
            mgr_code = str(row[13]).strip() if row[13] else None
            location = str(row[14]).strip() if row[14] else None

            is_active = (status_str.lower() == "active")
            salary = emp_salary_map.get(emp_code, Decimal("500000.00"))
            dept_id = dept_map.get(d_code)

            employee = Employee(
                employee_code=emp_code,
                first_name=first_name,
                last_name=last_name,
                email=email,
                department_id=dept_id,
                manager_id=None, # Updated in Pass 2
                salary=salary,
                hire_date=hire_date,
                exit_date=exit_date,
                work_location=location,
                employment_type=emp_type,
                is_active=is_active,
            )
            db.add(employee)
            db.flush()

            emp_code_to_id[emp_code] = employee.id
            if mgr_code:
                emp_manager_codes[employee.id] = mgr_code
            if r_code and r_code in role_map:
                emp_primary_roles[employee.id] = role_map[r_code]

        db.commit()
        print(f"  + Inserted {len(emp_code_to_id)} employees.")

        # Pass 2: Link managers & assign primary roles
        print("[INFO] Linking manager hierarchy and primary roles (Pass 2)...")
        for emp_id, mgr_code in emp_manager_codes.items():
            mgr_db_id = emp_code_to_id.get(mgr_code)
            if mgr_db_id:
                db.execute(
                    text("UPDATE employees SET manager_id = :mgr_id WHERE id = :emp_id"),
                    {"mgr_id": mgr_db_id, "emp_id": emp_id},
                )

        # Bulk insert primary roles
        for emp_id, role_id in emp_primary_roles.items():
            db.add(
                EmployeeRole(
                    employee_id=emp_id,
                    role_id=role_id,
                    is_primary=True,
                )
            )
        db.commit()
        print("  + Manager hierarchy and role mappings established.")

        # 5. Seed Employee Career Assignments History
        print("[INFO] Seeding career progression history (Sheet: employee_assignments)...")
        assign_sheet = wb["employee_assignments"]
        assign_rows = list(assign_sheet.iter_rows(values_only=True))
        assignments_count = 0

        for row in assign_rows[1:]:
            as_code = str(row[0]).strip() if row[0] else None
            emp_code = str(row[1]).strip() if row[1] else None
            eff_from = parse_date(row[2])
            eff_to = parse_date(row[3])
            d_code = str(row[4]).strip() if row[4] else None
            r_code = str(row[5]).strip() if row[5] else None
            j_level = int(row[6]) if row[6] is not None else None
            mgr_code = str(row[7]).strip() if row[7] else None
            reason = str(row[8]).strip() if row[8] else None

            emp_db_id = emp_code_to_id.get(emp_code)
            if not emp_db_id or not eff_from:
                continue

            assignment = EmployeeAssignment(
                assignment_code=as_code,
                employee_id=emp_db_id,
                effective_from=eff_from,
                effective_to=eff_to,
                department_id=dept_map.get(d_code),
                role_id=role_map.get(r_code),
                job_level=j_level,
                manager_id=emp_code_to_id.get(mgr_code),
                change_reason=reason,
            )
            db.add(assignment)
            assignments_count += 1
            if assignments_count % 500 == 0:
                db.commit()

        db.commit()
        print(f"  + Seeded {assignments_count} career progression assignment records.")

        # Summary statistics
        active_count = db.query(Employee).filter(Employee.is_active.is_(True)).count()
        inactive_count = db.query(Employee).filter(Employee.is_active.is_(False)).count()
        print(f"\n[SUCCESS] Master Dataset Seeding Completed Successfully!")
        print(f"  * Total Departments: {len(dept_map)}")
        print(f"  * Total Roles:       {len(role_map)}")
        print(f"  * Total Employees:   {len(emp_code_to_id)} ({active_count} active, {inactive_count} inactive/leavers)")
        print(f"  * Career History:    {assignments_count} assignment entries")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_master_dataset()
