import json
import os
import sys
import logging
from datetime import datetime
from decimal import Decimal

# Suppress raw SQL engine logs for clean output
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine
from app.models.department import Department
from app.models.role import Role, EmployeeRole
from app.models.employee import Employee

# Turn off verbose SQL echoing for clean console logs
engine.echo = False

from scripts.seed_master_dataset import seed_master_dataset

EXCEL_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "01_LedgerForge_Python_Master_Dataset.xlsx")
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sample_employees.json")

DEPARTMENT_CODES = {
    "Engineering": "ENG",
    "Product": "PROD",
    "Design": "DSN",
    "Human Resources": "HR",
    "Finance": "FIN",
    "Marketing": "MKT",
    "Customer Success": "CS",
}

ROLE_LEVELS = {
    "Lead Backend Engineer": "Lead",
    "DevOps / Infrastructure Engineer": "Senior",
    "Senior Product Manager": "Senior",
    "Frontend Engineer": "Mid",
    "UI/UX Designer": "Mid",
    "HR Operations Specialist": "Specialist",
    "Financial Analyst": "Analyst",
    "Data Engineer": "Mid",
    "Growth Marketing Lead": "Lead",
    "Support Engineer": "Associate",
}


def seed_database() -> None:
    """
    Populate the database with sample departments, roles, and employee records.
    """
    if not os.path.exists(DATA_FILE):
        print(f"Data file not found at {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    db = SessionLocal()
    try:
        print("[INFO] Seeding database...")

        # 1. Seed Departments
        dept_map = {}
        for item in records:
            dept_name = item["department"]
            if dept_name not in dept_map:
                code = DEPARTMENT_CODES.get(dept_name, dept_name[:3].upper())
                dept = db.query(Department).filter(Department.name == dept_name).first()
                if not dept:
                    dept = Department(
                        name=dept_name,
                        code=code,
                        description=f"{dept_name} Department",
                        is_active=True,
                    )
                    db.add(dept)
                    db.flush()
                    print(f"  + Added Department: {dept.name} ({dept.code})")
                dept_map[dept_name] = dept

        # 2. Seed Roles
        role_map = {}
        for item in records:
            role_title = item["role"]
            if role_title not in role_map:
                level = ROLE_LEVELS.get(role_title, "Standard")
                role = db.query(Role).filter(Role.title == role_title).first()
                if not role:
                    role = Role(
                        title=role_title,
                        level=level,
                        description=f"{role_title} Position",
                        is_active=True,
                    )
                    db.add(role)
                    db.flush()
                    print(f"  + Added Role: {role.title} ({role.level})")
                role_map[role_title] = role

        db.commit()

        # 3. Seed Employees
        emp_map = {}
        for item in records:
            email = item["email"]
            emp = db.query(Employee).filter(Employee.email == email).first()
            dept = dept_map[item["department"]]

            if not emp:
                emp = Employee(
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    email=email,
                    department_id=dept.id,
                    salary=Decimal(str(item["salary"])),
                    hire_date=datetime.strptime(item["hire_date"], "%Y-%m-%d").date(),
                    is_active=item.get("is_active", True),
                )
                db.add(emp)
                db.flush()
                print(f"  + Added Employee: {emp.first_name} {emp.last_name} ({emp.email})")

            emp_map[item["id"]] = emp

            # Assign primary role
            role = role_map[item["role"]]
            existing_role_assign = db.query(EmployeeRole).filter(
                EmployeeRole.employee_id == emp.id,
                EmployeeRole.role_id == role.id,
            ).first()

            if not existing_role_assign:
                emp_role = EmployeeRole(
                    employee_id=emp.id,
                    role_id=role.id,
                    is_primary=True,
                )
                db.add(emp_role)

        # 4. Configure sample manager hierarchy
        # Alice Smith (Lead Backend, id: 1) manages Bob (2), David (4), and Hassan (8)
        lead_alice = emp_map.get(1)
        if lead_alice:
            for rep_id in [2, 4, 8]:
                report = emp_map.get(rep_id)
                if report and report.manager_id is None:
                    report.manager_id = lead_alice.id
                    print(f"  -> Assigned Manager {lead_alice.first_name} to {report.first_name}")

        # Carol Williams (Senior PM, id: 3) manages Jack Taylor (10)
        pm_carol = emp_map.get(3)
        if pm_carol:
            support_jack = emp_map.get(10)
            if support_jack and support_jack.manager_id is None:
                support_jack.manager_id = pm_carol.id
                print(f"  -> Assigned Manager {pm_carol.first_name} to {support_jack.first_name}")

        db.commit()
        print("[SUCCESS] Database seeding successfully completed!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if os.path.exists(EXCEL_FILE):
        seed_master_dataset()
    else:
        seed_database()
