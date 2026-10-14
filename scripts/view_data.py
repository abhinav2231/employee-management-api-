import os
import sys
import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine
from app.models.department import Department
from app.models.role import Role
from app.models.employee import Employee

engine.echo = False


def view_data() -> None:
    db = SessionLocal()
    try:
        print("=" * 80)
        print("                 AURA WORKFORCE OS - DATABASE OVERVIEW")
        print("=" * 80)

        print("\n--- [1] DEPARTMENTS ---")
        departments = db.query(Department).order_by(Department.id).all()
        for d in departments:
            emp_count = len(d.employees)
            print(f"[{d.code}] {d.name:<22} | Cost Center: {d.cost_center or 'N/A':<7} | Employees: {emp_count:<3} | Active: {d.is_active}")

        print("\n--- [2] ROLES ---")
        roles = db.query(Role).order_by(Role.id).limit(15).all()
        for r in roles:
            print(f"[{r.code or 'N/A'}] ID: {r.id:<3} | Title: {r.title:<34} | Level: {r.level or 'N/A'}")
        print("  ... (showing 15 of 58 roles)")

        print("\n--- [3] EMPLOYEES ROSTER (SAMPLE) ---")
        employees = db.query(Employee).order_by(Employee.id).limit(20).all()
        header = f"{'Code':<10} {'Name':<22} {'Dept':<6} {'Role':<30} {'Salary (INR)':<14} {'Manager':<16} {'Status'}"
        print(header)
        print("-" * len(header))

        for e in employees:
            dept_code = e.department.code if e.department else "N/A"
            primary_roles = [er.role.title for er in e.employee_roles if er.is_primary]
            role_title = primary_roles[0] if primary_roles else "No Primary Role"
            manager_name = f"{e.manager.first_name} {e.manager.last_name}" if e.manager else "None (CEO)"
            status = "Active" if e.is_active else "Inactive"
            name = f"{e.first_name} {e.last_name}"
            salary_str = f"INR {e.salary:,.0f}"
            emp_code = e.employee_code or f"ID:{e.id}"

            print(f"{emp_code:<10} {name:<22} {dept_code:<6} {role_title:<30} {salary_str:<14} {manager_name:<16} {status}")

        print("\n--- [4] ORGANIZATIONAL HIERARCHY TREE ---")
        top_managers = db.query(Employee).filter(Employee.manager_id.is_(None)).all()
        for top in top_managers:
            print(f"+ {top.first_name} {top.last_name} ({top.department.name})")
            for rep in top.direct_reports:
                print(f"  |--> {rep.first_name} {rep.last_name} ({rep.email})")

        print("\n" + "=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    view_data()
