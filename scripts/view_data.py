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
        departments = db.query(Department).order_by(Department.department_id).all()
        for d in departments:
            emp_count = len(d.employees)
            print(f"[{d.department_id}] {d.department_name:<22} | Cost Center: {d.cost_center or 'N/A':<7} | Employees: {emp_count:<3} | Active: {d.is_active}")

        print("\n--- [2] ROLES ---")
        total_roles = db.query(Role).count()
        roles = db.query(Role).order_by(Role.role_id).limit(15).all()
        for r in roles:
            print(f"[{r.role_id}] Title: {r.role_title:<34} | Dept: {r.department_id or 'N/A':<4} | Level: {r.level or 'N/A'}")
        print(f"  ... (showing {len(roles)} of {total_roles} roles)")

        print("\n--- [3] EMPLOYEES ROSTER (SAMPLE) ---")
        employees = db.query(Employee).order_by(Employee.employee_id).limit(20).all()
        header = f"{'Code':<10} {'Name':<22} {'Dept':<6} {'Role':<30} {'Salary (INR)':<14} {'Manager':<16} {'Status'}"
        print(header)
        print("-" * len(header))

        for e in employees:
            dept_code = e.department_id or "N/A"
            if e.role:
                role_title = e.role.role_title
            else:
                primary_roles = [er.role.title for er in e.employee_roles if er.is_primary]
                role_title = primary_roles[0] if primary_roles else "No Primary Role"
            manager_name = f"{e.manager.first_name} {e.manager.last_name}" if e.manager else "None (CEO)"
            status = e.employment_status or ("Active" if e.is_active else "Inactive")
            name = e.full_name or f"{e.first_name} {e.last_name}"
            salary_str = f"INR {e.salary:,.0f}" if e.salary else "N/A"

            print(f"{e.employee_id:<10} {name:<22} {dept_code:<6} {role_title[:29]:<30} {salary_str:<14} {manager_name[:15]:<16} {status}")

        print("\n--- [4] ORGANIZATIONAL HIERARCHY TREE ---")
        top_managers = db.query(Employee).filter(Employee.manager_id.is_(None)).all()
        for top in top_managers:
            dept_name = top.department.department_name if top.department else "N/A"
            print(f"+ {top.full_name} ({dept_name})")
            for rep in top.direct_reports[:10]:
                print(f"  |--> {rep.full_name} ({rep.work_email})")

        print("\n" + "=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    view_data()
